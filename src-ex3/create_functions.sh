#!/bin/bash




# Helper function to run a command quietly, but print command + error if it fails
run_cmd() {
  # Run the command passed as argument, redirect stdout to /dev/null, stderr captured
  if ! output=$("$@" 2>&1 >/dev/null); then
    echo "Error running command: $*"
    echo "$output"
    exit 1
  fi
}

run_cmd_subshell() {
  if ! output=$(bash -c "$1" 2>&1 >/dev/null); then
    echo "Error running block:"
    echo "$1"
    echo "$output"
    exit 1
  fi
}

# Create Preprocessing function
run_cmd_subshell '
  cd lambdas/preprocessing
  rm -rf package lambda.zip;
  mkdir -p package/nltk_data
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  python3 -m nltk.downloader punkt stopwords punkt_tab wordnet -d package/nltk_data
  python3 prune.py
  zip lambda.zip handler.py
  cd package
  zip -r ../lambda.zip * nltk_data;
'

run_cmd awslocal lambda create-function \
--function-name preprocessing \
--handler handler.handler \
--zip-file fileb://lambdas/preprocessing/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}" \
--memory-size 1024 \
--timeout 900


# Sentiment Analysis Function
run_cmd_subshell '
  cd lambdas/sentiment_analysis
  rm -f lambda.zip
  mkdir -p package/nltk_data
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  python3 -m nltk.downloader vader_lexicon -d package/nltk_data
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip * nltk_data;
'

run_cmd awslocal lambda create-function \
--function-name sentiment_analysis \
--handler handler.handler \
--zip-file fileb://lambdas/sentiment_analysis/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}" \
--memory-size 128 \
--timeout 45


# Create Profanity Check function
run_cmd_subshell '
  cd lambdas/profanity_check
  rm -f lambda.zip
  mkdir -p package
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip *;
'

run_cmd awslocal lambda create-function \
--function-name profanity_check \
--handler handler.handler \
--zip-file fileb://lambdas/profanity_check/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}" \
--memory-size 128 \
--timeout 45


# Update Profanity Counter Function
run_cmd_subshell '
  cd lambdas/update_profanity_counter
  rm -f lambda.zip
  zip lambda.zip handler.py;
'

run_cmd awslocal lambda create-function \
--function-name update_profanity_counter \
--handler handler.handler \
--zip-file fileb://lambdas/update_profanity_counter/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}" \
--memory-size 256 \
--timeout 45


# Create summarize function
run_cmd_subshell '
  cd lambdas/summarize
  rm -f lambda.zip
  zip lambda.zip handler.py;
'

run_cmd awslocal lambda create-function \
--function-name summarize \
--handler handler.handler \
--zip-file fileb://lambdas/summarize/lambda.zip \
--runtime python3.11 \
--role arn:aws:iam::000000000000:role/lambda-role \
--environment Variables="{STAGE=local}" \
--memory-size 512 \
--timeout 900