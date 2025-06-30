#!/bin/bash


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

# Helper function to run a command quietly, but print command + error if it fails
run_cmd() {
  # Run the command passed as argument, redirect stdout to /dev/null, stderr captured
  if ! output=$("$@" 2>&1 >/dev/null); then
    echo "Error running command: $*"
    echo "$output"
    exit 1
  fi
}

# Get ARNs for all functions
ARN_PREPROC=$(awslocal lambda get-function \
  --function-name preprocessing \
  | jq -r '.Configuration.FunctionArn')

# Get ARN for Profanity table in dynamodb
ARN_TABLE_PROFAN=$(awslocal dynamodb describe-table \
  --table-name Profanity \
  | jq -r '.Table.LatestStreamArn')


# Call preprocessing on insert into raw review bucket
run_cmd awslocal s3api put-bucket-notification-configuration \
  --bucket localstack-assignment3-reviews-raw \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [
      {
        \"LambdaFunctionArn\": \"$ARN_PREPROC\",
        \"Events\": [\"s3:ObjectCreated:*\"]
      }
    ]
  }"


# Create Event queues for both profanity check and sentiment analysis
run_cmd awslocal sqs create-queue --queue-name sentiment-queue --attributes VisibilityTimeout=60
run_cmd awslocal sqs create-queue --queue-name profanity-queue --attributes VisibilityTimeout=60

# Extract the required ARNs
QUEUE_URL_SENTIM=$(awslocal sqs get-queue-url \
  --queue-name sentiment-queue | jq -r '.QueueUrl')
QUEUE_URL_PROFAN=$(awslocal sqs get-queue-url \
  --queue-name profanity-queue | jq -r '.QueueUrl')
SQS_ARN_SENTIM=$(awslocal sqs get-queue-attributes \
  --queue-url "$QUEUE_URL_SENTIM" \
  --attribute-name QueueArn | jq -r '.Attributes.QueueArn')
SQS_ARN_PROFAN=$(awslocal sqs get-queue-attributes \
  --queue-url "$QUEUE_URL_PROFAN" \
  --attribute-name QueueArn | jq -r '.Attributes.QueueArn')


run_cmd awslocal s3api put-bucket-notification-configuration \
--bucket localstack-assignment3-reviews-processed \
--notification-configuration '{"EventBridgeConfiguration": {}}'

# Create EventBridge rule for sentiment_analysis and profanity_check
run_cmd awslocal events put-rule \
  --name ProcessedBridge \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["localstack-assignment3-reviews-processed"]
      }
    }
  }' \
  --state ENABLED


# Put target for rule as the queue arns for Sentiment
run_cmd awslocal events put-targets \
  --rule ProcessedBridge \
  --targets \
  "Id"="1","Arn"="$SQS_ARN_SENTIM" \
  "Id"="2","Arn"="$SQS_ARN_PROFAN"


# Finally, add event source mappings between queues and function calls
run_cmd awslocal lambda create-event-source-mapping \
  --event-source-arn $SQS_ARN_SENTIM \
  --function-name sentiment_analysis \
  --batch-size 512 \
  --maximum-batching-window-in-seconds 20 \
  --enabled

run_cmd awslocal lambda create-event-source-mapping \
  --event-source-arn $SQS_ARN_PROFAN \
  --function-name profanity_check \
  --batch-size 512 \
  --maximum-batching-window-in-seconds 20 \
  --enabled


# Call update-profanity-counter on insert into Profanity table
run_cmd awslocal lambda create-event-source-mapping \
  --event-source-arn $ARN_TABLE_PROFAN \
  --function-name update_profanity_counter \
  --batch-size 512 \
  --maximum-batching-window-in-seconds 20 \
  --starting-position LATEST


# Call summarize only one request event
run_cmd awslocal lambda create-function-url-config \
  --function-name summarize \
  --auth-type NONE