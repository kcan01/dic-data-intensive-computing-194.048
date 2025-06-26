import os
import sys
import json
import boto3
import hashlib
import pytest
from time import sleep
os.environ["AWS_DEFAULT_REGION"] =  "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
# Import handler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lambdas", "profanity")))
import handler as profanity_handler
endpoint_url = None
if os.getenv("STAGE") == "local":
    endpoint_url = "https://localhost.localstack.cloud:4566"

args = {
    "region_name": "us-east-1",
    "endpoint_url": "http://localhost:4566",
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
}
s3: "S3Client" = boto3.client("s3", **args)
ssm: "SSMClient" = boto3.client("ssm", **args)
client: "DynamoDBServiceResource" = boto3.client("dynamodb", **args)
dynamodb: "DynamoDBClient" = boto3.resource("dynamodb", **args)


def get_table_name():
    return ssm.get_parameter(Name="/localstack-assignment3/tables/profanity")["Parameter"]["Value"]

def get_deterministic_key(data: dict) -> str:
    reviewer = data.get("reviewerID", "")
    date = data.get("unixReviewTime", "")
    asin = data.get("asin", "")
    identifier = f"{reviewer}+{date}+{asin}"
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def test_profanity_check():
    # Setup
    input_file = "tworeview.json"
    bucket_name = ssm.get_parameter(Name="/localstack-assignment3/buckets/reviewsprocessed")["Parameter"]["Value"]
    s3.upload_file(input_file, bucket_name, "tworeview.json")

    # Lambda-S3-Event simulieren
    fake_event = {
        "Records": [{
            "s3": {
                "bucket": {"name": bucket_name},
                "object": {"key": "tworeview.json"}
            }
        }]
    }

    # Run handler
    profanity_handler.handler(fake_event, None)

    # Check
    with open(input_file, "r") as f:
        for line in f:
            review = json.loads(line)
            key = get_deterministic_key(review)
            table = dynamodb.Table(get_table_name())

            
            for _ in range(3):
                response = table.get_item(Key={"id": key})
                if "Item" in response:
                    break
                sleep(0.5)

            assert "Item" in response, f"Review {key} not found in DynamoDB"
            assert "contains_profanity" in response["Item"]
            assert isinstance(response["Item"]["contains_profanity"], bool)

    
            table.delete_item(Key={"id": key})

    s3.delete_object(Bucket=bucket_name, Key="tworeview.json")
