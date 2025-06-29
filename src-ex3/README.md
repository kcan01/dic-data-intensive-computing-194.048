# DIC Ex3

## Setup

- Make sure Docker is running
- Start localstack server in a terminal
  -  create/activate environment as described in Environment_Setup.pdf
  - Install requirements txt
  -  On Windows: run
  ```bash
  set LOCALSTACK_ACTIVATE_PRO=0 &&  set LOCALSTACK_DEBUG=1 && localstack start
  ```
  - On Linux/Mac (At least I think this works on Mac)
  ```bash
  LOCALSTACK_ACTIVATE_PRO=0 LOCALSTACK_DEBUG=1 localstack start
  ```
- Open a new terminal
- In it, run
```bash
docker-compose build 
```
- and then
```bash
docker-compose run --rm dic-shell
```
- This creates a new docker container and puts you inside it. You should then be in its terminal.
- Inside this terminal, you can now run
```bash
bash setup-tutorial.sh
```
- This sets up everything from the tutorial. You can then access the web interface.
- For the actual exercise, try
```bash
bash setup.sh
```
- Do testing/developement/whatever you want. Run 
  ```bash refresh_functions.sh && bash refresh_buckets.sh```
- if you make any code changes and want to upload them to aws. You will probably have to add your function to this file.
- You can upload a test file using 
- ```bash
  awslocal s3 cp onereview.json s3://localstack-assignment3-reviews-raw
  ```
- Or the larger test file containing 10 reviews
- ```bash
  awslocal s3 cp tenreviews.json s3://localstack-assignment3-reviews-raw
  ```
- Use ```exit``` to exit the containers shell and go back to your terminal

## Useful commands
View all inserts in a table (replace Profanity with Sentiment or Users if necessary)
```bash
awslocal dynamodb scan --table-name Profanity
```
View all files in a bucket (replace )
```bash
awslocal s3 ls s3://localstack-assignment3-reviews-raw
```
and 
```bash
awslocal s3 ls s3://localstack-assignment3-reviews-processed
```
Remove all files from one bucket
```bash
awslocal s3 rm s3://localstack-assignment3-reviews-processed --recursive
```
