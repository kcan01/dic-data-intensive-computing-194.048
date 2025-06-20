#!/bin/bash

# Exit immediately if a command exits with a non-zero status
# set -e

# Optional: Echo each command before running it
set -x

# -------------------------------
# ENVIRONMENT SETUP (OPTIONAL)
# -------------------------------
# export EXAMPLE_ENV_VAR="some_value"

# -------------------------------
# COMMANDS TO RUN
# -------------------------------

echo "Starting setup script..."

awslocal s3 mb s3://localstack-assignment3-reviews-raw
awslocal ssm put-parameter --name /localstack-assignment3/buckets/reviewsraw --type "String" --value "localstack-assignment3-reviews-raw"

awslocal s3 mb s3://localstack-assignment3-reviews-processed
awslocal ssm put-parameter --name /localstack-assignment3/buckets/reviewsprocessed --type "String" --value "localstack-assignment3-reviews-processed"

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

echo "Started App, access at https://webapp.s3-website.localhost.localstack.cloud:4566/"
echo "Setup script completed successfully!"