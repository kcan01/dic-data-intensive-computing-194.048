#!/bin/bash

# Exit immediately if a command exits with a non-zero status
# set -e

# Optional: Echo each command before running it
set -x

# -------------------------------
# ENVIRONMENT SETUP (OPTIONAL)
# -------------------------------
# export EXAMPLE_ENV_VAR="some_value"
awslocal dynamodb create-table \
    --table-name Sentiment \
    --attribute-definitions \
        AttributeName=ReviewID,AttributeType=S \
    --key-schema \
        AttributeName=ReviewID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
awslocal ssm put-parameter --name /localstack-assignment3/tables/sentiment --type "String" --value "Sentiment"

awslocal dynamodb create-table \
    --table-name Profanity \
    --attribute-definitions \
        AttributeName=ReviewID,AttributeType=S \
    --key-schema \
        AttributeName=ReviewID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
awslocal ssm put-parameter --name /localstack-assignment3/tables/profanity --type "String" --value "Profanity"
awslocal dynamodb update-table \
  --table-name Profanity \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE



awslocal dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=UserID,AttributeType=S \
    --key-schema \
        AttributeName=UserID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
awslocal ssm put-parameter --name /localstack-assignment3/tables/users --type "String" --value "Users"

