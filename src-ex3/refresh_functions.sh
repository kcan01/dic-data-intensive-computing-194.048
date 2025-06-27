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
  rm -rf package lambda.zip;
  mkdir -p package/nltk_data
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  python3 -m nltk.downloader punkt stopwords punkt_tab wordnet -d package/nltk_data
  python3 prune.py
  zip lambda.zip handler.py
  cd package
  zip -r ../lambda.zip * nltk_data;
)

awslocal lambda update-function-code \
--function-name preprocessing \
--zip-file fileb://lambdas/preprocessing/lambda.zip


# sentiment_analysis function refresh
(
  cd lambdas/sentiment_analysis
  rm -f lambda.zip
  mkdir -p package/nltk_data
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  python3 -m nltk.downloader vader_lexicon -d package/nltk_data
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip * nltk_data;
)

awslocal lambda update-function-code \
--function-name sentiment_analysis \
--zip-file fileb://lambdas/sentiment_analysis/lambda.zip


# profanity_check function refresh
(
  cd lambdas/profanity_check
  rm -rf lambda.zip
  zip lambda.zip handler.py
)


awslocal lambda update-function-code \
--function-name profanity_check \
--zip-file fileb://lambdas/profanity_check/lambda.zip


# update_profanity_counter function refresh
(
  cd lambdas/update_profanity_counter
  rm -rf lambda.zip
  zip lambda.zip handler.py
)

awslocal lambda update-function-code \
--function-name update_profanity_counter \
--zip-file fileb://lambdas/update_profanity_counter/lambda.zip


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