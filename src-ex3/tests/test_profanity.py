import typing
import pytest
import json
import os
import sys
import hashlib
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re
import boto3
from boto3.dynamodb.conditions import Key

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

s3: "S3Client" = boto3.client(
    "s3", endpoint_url="http://localhost.localstack.cloud:4566"
)
ssm: "SSMClient" = boto3.client(
    "ssm", endpoint_url="http://localhost.localstack.cloud:4566"
)
awslambda: "LambdaClient" = boto3.client(
    "lambda", endpoint_url="http://localhost.localstack.cloud:4566"
)
dynamodb = boto3.resource(
    "dynamodb", endpoint_url="http://localhost.localstack.cloud:4566"
)


#from lambdas.preprocessing.handler import get_deterministic_key
def get_deterministic_key(data: dict) -> str:
    reviewer = data.get("reviewerID", "")
    date = data.get("unixReviewTime", "")
    asin = data.get("asin", "")
    identifier = f"{reviewer}+{date}+{asin}"
    hash_digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return f"review_{hash_digest}.json"

def get_review_id(filename: str) -> str:
    match = re.fullmatch(r'review_(.+)\.json', filename)
    if match:
        return match.group(1)
    else:
        return "UNKNOWN"
    
def get_review_id_from_key(key: str) -> str:
    import re
    match = re.fullmatch(r'review_(.+)\.json', key)
    return match.group(1) if match else "UNKNOWN"
    
def get_bucket_name(name) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]

def get_table_name(name) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]

@pytest.fixture(autouse=True)
def _wait_for_lambda():
    awslambda.get_waiter("function_active").wait(FunctionName="profanity_check")
    yield

def test_profanity_detection():
    file = os.path.join("onereview.json")
    key = os.path.basename(file)[:-5] + "TEST1" + ".json"

    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
    target_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")

    #uploads original file 
    with open(file, "r") as f:
        review = json.load(f)
        keys_out = get_deterministic_key(review)
        reviewerID = review["reviewerID"]  
    s3.upload_file(file, Bucket=source_bucket, Key=key)
    
    #now needs to check, if the data is in the dynamo table 
    table_name = get_table_name("/localstack-assignment3/tables/profanity")
    table = dynamodb.Table(table_name)
    
    # Wait for all items to appear in DynamoDB
    #waiter = dynamodb.get_waiter("table_exists")
    #waiter.wait(TableName=table)

    # Poll for each item
    review_id = get_review_id_from_key(keys_out) 
    found = False
    for _ in range(10):  # retry loop (up to ~10 seconds)
        response = table.get_item(Key={"ReviewID": review_id})
        #response = table.get_item(Key={"id": key})
        assert "Item" in response, f"Review {review_id} not found in DynamoDB"
        assert "contains_profanity" in response["Item"]
        assert isinstance(response["Item"]["contains_profanity"], bool)

    # Optional: cleanup
    s3.delete_object(Bucket=source_bucket, Key=key)
    s3.delete_object(Bucket=target_bucket, Key=keys_out)
    for key_out in keys_out:
        table.delete_item(Key={"ReviewID": reviewerID})
        
        
        
