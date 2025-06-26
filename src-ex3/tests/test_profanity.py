import typing
import pytest
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import boto3
from boto3.dynamodb.conditions import Key

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_dynamodb import DynamoDBClient

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

s3: "S3Client" = boto3.client("s3", endpoint_url="http://localhost.localstack.cloud:4566")
ssm: "SSMClient" = boto3.client("ssm", endpoint_url="http://localhost.localstack.cloud:4566")
awslambda: "LambdaClient" = boto3.client("lambda", endpoint_url="http://localhost.localstack.cloud:4566")
dynamodb: "DynamoDBClient" = boto3.client("dynamodb", endpoint_url="http://localhost.localstack.cloud:4566")

#from lambdas.preprocessing.handler import get_deterministic_key

def get_bucket_name(name) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]

def get_table_name(name) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]

@pytest.fixture(autouse=True)
def _wait_for_lambda():
    awslambda.get_waiter("function_active").wait(FunctionName="profanity")
    yield

def test_profanity_detection():
    file = os.path.join("tworeview.json")
    key = os.path.basename(file)

    bucket = get_bucket_name("/localstack-assignment3/buckets/reviewsprocessed")
    table = get_table_name("/localstack-assignment3/tables/profanity")

    with open(file, "r") as f:
        reviews = [json.loads(line) for line in f if line.strip()]

    keys_out = [get_deterministic_key(r) for r in reviews]

    # Upload the file to trigger the profanity lambda
    s3.upload_file(file, Bucket=bucket, Key=key)

    # Wait for all items to appear in DynamoDB
    waiter = dynamodb.get_waiter("table_exists")
    waiter.wait(TableName=table)

    # Poll for each item
    for key_out in keys_out:
        found = False
        for _ in range(10):  # retry loop (up to ~10 seconds)
            response = dynamodb.get_item(TableName=table, Key={"id": {"S": key_out}})
            #response = table.get_item(Key={"id": key})

            assert "Item" in response, f"Review {key} not found in DynamoDB"
            assert "contains_profanity" in response["Item"]
            assert isinstance(response["Item"]["contains_profanity"], bool)

    # Optional: cleanup
    s3.delete_object(Bucket=bucket, Key=key)
    for key_out in keys_out:
        dynamodb.delete_item(TableName=table, Key={"id": {"S": key_out}})
        
