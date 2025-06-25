#!/bin/bash


# Optional: Echo each command before running it
set -x


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

# Create Preprocessing function
(
  cd lambdas/preprocessing
  rm -rf package lambda.zip;
  mkdir -p package/nltk_data
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  python3 -m nltk.downloader punkt stopwords punkt_tab wordnet -d package/nltk_data
  python3 prune.py
  zip lambda.zip handler.py
  cd package
  zip -r ../lambda.zip * nltk_data;
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
  cd lambdas/sentiment_analysis
  rm -f lambda.zip
  mkdir -p package
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip *;
)

awslocal lambda create-function \
--function-name sentiment_analysis \
--handler handler.handler \
--zip-file fileb://lambdas/sentiment_analysis/lambda.zip \
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