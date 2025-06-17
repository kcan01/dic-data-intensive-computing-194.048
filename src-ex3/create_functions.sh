#!/bin/bash


# Optional: Echo each command before running it
set -x


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

# Create Preprocessing function
(
  cd lambdas/preprocessing
  rm -f lambda.zip
  zip lambda.zip handler.py;
)
awslocal lambda create-function \
--function-name preprocessing \
--handler handler.handler \
--zip-file fileb://lambdas/preprocessing/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"


# Sentiment Analysis Function
(
  cd lambdas/sentiment-analysis
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name sentiment-analysis \
--handler handler.handler \
--zip-file fileb://lambdas/sentiment-analysis/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"


# Create Profanity Check function
(
  cd lambdas/profanity-check
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name profanity-check \
--handler handler.handler \
--zip-file fileb://lambdas/profanity-check/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"


# Update Profanity Counter Function
(
  cd lambdas/update-profanity-counter
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name update-profanity-counter \
--handler handler.handler \
--zip-file fileb://lambdas/update-profanity-counter/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"


# Create summarize function
(
  cd lambdas/summarize
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda create-function \
--function-name summarize \
--handler handler.handler \
--zip-file fileb://lambdas/summarize/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}"