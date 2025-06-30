#!/bin/bash


# -------------------------------
# ENVIRONMENT SETUP (OPTIONAL)
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

run_cmd awslocal dynamodb create-table \
    --table-name Sentiment \
    --attribute-definitions \
        AttributeName=ReviewID,AttributeType=S \
    --key-schema \
        AttributeName=ReviewID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
run_cmd awslocal ssm put-parameter --name /localstack-assignment3/tables/sentiment --type "String" --value "Sentiment"

run_cmd awslocal dynamodb create-table \
    --table-name Profanity \
    --attribute-definitions \
        AttributeName=ReviewID,AttributeType=S \
    --key-schema \
        AttributeName=ReviewID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
run_cmd awslocal ssm put-parameter --name /localstack-assignment3/tables/profanity --type "String" --value "Profanity"
run_cmd awslocal dynamodb update-table \
  --table-name Profanity \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE



run_cmd awslocal dynamodb create-table \
    --table-name Users \
    --attribute-definitions \
        AttributeName=UserID,AttributeType=S \
    --key-schema \
        AttributeName=UserID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --table-class STANDARD
run_cmd awslocal ssm put-parameter --name /localstack-assignment3/tables/users --type "String" --value "Users"

