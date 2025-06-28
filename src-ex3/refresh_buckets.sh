#!/bin/bash


# Optional: Echo each command before running it
set -x


# -------------------------------
# COMMANDS TO RUN
# -------------------------------

echo "Starting refresh script..."

awslocal s3 rm s3://localstack-assignment3-reviews-raw --recursive
awslocal s3 rm s3://localstack-assignment3-reviews-processed --recursive

echo "Finished script completed successfully!"