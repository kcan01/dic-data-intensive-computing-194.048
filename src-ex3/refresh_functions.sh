#!/bin/bash


# Optional: Echo each command before running it
set -x


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

echo "Starting refresh script..."

# Preprocessing function refresh
#(
#  cd lambdas/preprocessing
#  rm -rf package lambda.zip;
#  mkdir -p package/nltk_data
#  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
#  python3 -m nltk.downloader punkt stopwords punkt_tab wordnet -d package/nltk_data
#  python3 prune.py
#  zip lambda.zip handler.py
#  cd package
#  zip -r ../lambda.zip * nltk_data;
#)

#awslocal lambda update-function-code \
#--function-name preprocessing \
#--zip-file fileb://lambdas/preprocessing/lambda.zip


# sentiment_analysis function refresh
(
  cd lambdas/sentiment_analysis
  rm -f lambda.zip
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip * nltk_data;
)

awslocal lambda update-function-code \
--function-name sentiment_analysis \
--zip-file fileb://lambdas/sentiment_analysis/lambda.zip

# Update Profanity Check function
(
  cd lambdas/profanity_check
  rm -f lambda.zip
  mkdir -p package
  pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all:
  zip lambda.zip handler.py;
  cd package
  zip -r ../lambda.zip *;
)

awslocal lambda update-function-code \
--function-name profanity_check \
--zip-file fileb://lambdas/profanity_check/lambda.zip

# Update update Profanity Counter Function
(
  cd lambdas/update_profanity_counter
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda update-function-code \
--function-name update_profanity_counter \
--zip-file fileb://lambdas/update_profanity_counter/lambda.zip 



#summarize function update
(
  cd lambdas/summarize
  rm -f lambda.zip
  zip lambda.zip handler.py;
)

awslocal lambda update-function-code \
--function-name summarize \
--zip-file fileb://lambdas/summarize/lambda.zip 




echo "Finished script completed successfully!"