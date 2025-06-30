#!/bin/bash


# -------------------------------
# ENVIRONMENT SETUP (OPTIONAL)
# -------------------------------
# export EXAMPLE_ENV_VAR="some_value"

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

echo "Starting setup script..."

run_cmd awslocal s3 mb s3://localstack-assignment3-reviews-raw
run_cmd awslocal ssm put-parameter --name /localstack-assignment3/buckets/reviewsraw --type "String" --value "localstack-assignment3-reviews-raw"

run_cmd awslocal s3 mb s3://localstack-assignment3-reviews-processed
run_cmd awslocal ssm put-parameter --name /localstack-assignment3/buckets/reviewsprocessed --type "String" --value "localstack-assignment3-reviews-processed"

bash create_tables.sh

bash create_functions.sh

# Wait for some time seconds so that the function can be correctly created in the background
sleep 10s

bash create_events.sh

# Add path to updated website/webapp here
# Static S3 web app
#awslocal s3 mb s3://webapp
#awslocal s3 sync --delete ./website s3://webapp
#awslocal s3 website s3://webapp --index-document index.html

# You can add your own commands below
# ./your_script.py
# python my_app.py
# curl https://example.com


echo "Setup script completed!"