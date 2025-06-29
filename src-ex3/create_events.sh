#!/bin/bash

# Optional: Echo each command before running it
set -x

# -------------------------------
# ENVIRONMENT SETUP (OPTIONAL)
# -------------------------------
# export EXAMPLE_ENV_VAR="some_value"

# -------------------------------
# COMMANDS TO RUN
# -------------------------------

# Get ARNs for all functions
ARN_PREPROC=$(awslocal lambda get-function \
  --function-name preprocessing \
  | jq -r '.Configuration.FunctionArn')

# Get ARN for Profanity table in dynamodb
ARN_TABLE_PROFAN=$(awslocal dynamodb describe-table \
  --table-name Profanity \
  | jq -r '.Table.LatestStreamArn')


# Call preprocessing on insert into raw review bucket
awslocal s3api put-bucket-notification-configuration \
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
awslocal sqs create-queue --queue-name sentiment-queue
awslocal sqs create-queue --queue-name profanity-queue

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


awslocal s3api put-bucket-notification-configuration \
--bucket localstack-assignment3-reviews-processed \
--notification-configuration '{"EventBridgeConfiguration": {}}'

# Create EventBridge rule for sentiment_analysis and profanity_check
awslocal events put-rule \
  --name ProcessedBridge \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["localstack-assignment3-reviews-processed"]
      }
    }
  }'
  --state ENABLED


# Put target for rule as the queue arns for Sentiment
awslocal events put-targets \
  --rule ProcessedBridge \
  --targets \
  "Id"="1","Arn"="$SQS_ARN_SENTIM" \
  "Id"="2","Arn"="$SQS_ARN_PROFAN"


# Finally, add event source mappings between queues and function calls
awslocal lambda create-event-source-mapping \
  --event-source-arn $SQS_ARN_SENTIM \
  --function-name sentiment_analysis \
  --batch-size 32 \
  --maximum-batching-window-in-seconds 5 \
  --enabled

awslocal lambda create-event-source-mapping \
  --event-source-arn $SQS_ARN_PROFAN \
  --function-name profanity_check \
  --batch-size 32 \
  --maximum-batching-window-in-seconds 5 \
  --enabled


# Call update-profanity-counter on insert into Profanity table
awslocal lambda create-event-source-mapping \
  --event-source-arn $ARN_TABLE_PROFAN \
  --function-name update_profanity_counter \
  --batch-size 32 \
  --maximum-batching-window-in-seconds 10 \
  --starting-position LATEST


# Call summarize only one request event
awslocal lambda create-function-url-config \
  --function-name summarize \
  --auth-type NONE