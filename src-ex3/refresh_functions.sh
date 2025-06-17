#!/bin/bash


# Optional: Echo each command before running it
set -x


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

echo "Starting refresh script..."

# Preprocessing function refresh
(
  cd lambdas/preprocessing
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name preprocessing \
--zip-file fileb://lambdas/preprocessing/lambda.zip


# sentiment-analysis function refresh
(
  cd lambdas/sentiment-analysis
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name sentiment-analysis \
--zip-file fileb://lambdas/sentiment-analysis/lambda.zip


# profanity-check function refresh
(
  cd lambdas/profanity-check
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name profanity-check \
--zip-file fileb://lambdas/profanity-check/lambda.zip


# update-profanity-counter function refresh
(
  cd lambdas/update-profanity-counter
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name update-profanity-counter \
--zip-file fileb://lambdas/update-profanity-counter/lambda.zip


# summarize function refresh
(
  cd lambdas/summarize
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name summarize \
--zip-file fileb://lambdas/summarize/lambda.zip

echo "Finished script completed successfully!"