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
  --function-name sentiment_analysis \
  | jq -r '.Configuration.FunctionArn')

ARN_SUMMAR=$(awslocal lambda get-function \
  --function-name summarize \
  | jq -r '.Configuration.FunctionArn')




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

      }
    ]
  }"




# Call summarize only one request event
awslocal lambda create-function-url-config \
  --function-name summarize \
  --auth-type NONE