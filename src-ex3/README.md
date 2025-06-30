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
bash setup.sh
```
- Do testing/developement/whatever you want. Run 
  ```bash refresh_functions.sh && bash refresh_buckets.sh```
- if you make any code changes and want to upload them to aws. You will probably have to add your function to this file.
- You can upload a test file using 
- ```bash
  awslocal s3 cp onereview.json s3://localstack-assignment3-reviews-raw
  ```
- Or the entire review file `reviews_devset.json` with > 70 000 reviews
- ```bash
   python upload_batched.py reviews_devset.json 2000 5
   ```
  this uploads the file `reviews_devset.json` in batches of 2000 reviews with 5 Minute delay between batches
- To get the Summary about Sentiment, Profanity and banned Users for all reviews currently in the DynamoDB Tables, run
```bash
bash get_summary.sh
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
