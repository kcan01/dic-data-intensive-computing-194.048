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
ARN_SENTIM=$(awslocal lambda get-function \
  --function-name sentiment-analysis \
  | jq -r '.Configuration.FunctionArn')
ARN_PROFAN=$(awslocal lambda get-function \
  --function-name profanity-check \
  | jq -r '.Configuration.FunctionArn')
ARN_UPDPC=$(awslocal lambda get-function \
  --function-name update-profanity-counter \
  | jq -r '.Configuration.FunctionArn')
ARN_SUMMAR=$(awslocal lambda get-function \
  --function-name summarize \
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


# Call sentiment analysis AND profanity check on insert into processed review bucket
awslocal s3api put-bucket-notification-configuration \
  --bucket localstack-assignment3-reviews-processed \
  --notification-configuration "{
    \"LambdaFunctionConfigurations\": [
      {
        \"LambdaFunctionArn\": \"$ARN_SENTIM\",
        \"Events\": [\"s3:ObjectCreated:*\"]

      },
      {
        \"LambdaFunctionArn\": \"$ARN_PROFAN\",
        \"Events\": [\"s3:ObjectCreated:*\"]

      }
    ]
  }"


# Call update-profanity-counter on insert into Profanity table
awslocal lambda create-event-source-mapping \
  --event-source-arn $ARN_TABLE_PROFAN \
  --function-name update-profanity-counter \
  --batch-size 1 \
  --starting-position LATEST


# Call summarize only one request event
awslocal lambda create-function-url-config \
  --function-name summarize \
  --auth-type NONE