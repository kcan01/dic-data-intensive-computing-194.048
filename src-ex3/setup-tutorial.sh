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

awslocal s3 mb s3://localstack-thumbnails-app-images
awslocal ssm put-parameter --name /localstack-thumbnail-app/buckets/images --type "String" --value "localstack-thumbnails-app-images"

awslocal s3 mb s3://localstack-thumbnails-app-resized
awslocal ssm put-parameter --name /localstack-thumbnail-app/buckets/resized --type "String" --value "localstack-thumbnails-app-resized"

# Presign function creation and initialization
(
  cd lambdas/presign
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name presign \
--runtime python3.11 \
--timeout 10 \
--zip-file fileb://lambdas/presign/lambda.zip \
--handler handler.handler \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"

awslocal lambda create-function-url-config \
--function-name presign \
--auth-type NONE

# List function creation
(
  cd lambdas/list
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name list \
--handler handler.handler \
--zip-file fileb://lambdas/list/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"

awslocal lambda create-function-url-config \
--function-name list \
--auth-type NONE

# Resize function creation
(
  cd lambdas/resize
  rm -rf package lambda.zip;
  mkdir package
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  zip lambda.zip handler.py
  cd package
  zip -r ../lambda.zip *;
)

awslocal lambda create-function \
--function-name resize \
--runtime python3.11 \
--timeout 10 \
--zip-file fileb://lambdas/resize/lambda.zip \
--handler handler.handler \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"

# Add event trigger to run function on image creation
awslocal s3api put-bucket-notification-configuration \
--bucket localstack-thumbnails-app-images \
--notification-configuration "{\"LambdaFunctionConfigurations\": [{\"LambdaFunctionArn\": \"$(awslocal lambda get-function --function-name resize | jq -r .Configuration.FunctionArn)\", \"Events\": [\"s3:ObjectCreated:*\"]}]}"

# Static S3 web app
awslocal s3 mb s3://webapp
awslocal s3 sync --delete ./website s3://webapp
awslocal s3 website s3://webapp --index-document index.html

# You can add your own commands below
# ./your_script.py
# python my_app.py
# curl https://example.com

echo "Started App, access at https://webapp.s3-website.localhost.localstack.cloud:4566/"
echo "Setup script completed successfully!"