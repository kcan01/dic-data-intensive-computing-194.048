import typing
import pytest
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient


import nltk
nltk_data_path = os.path.join(os.path.dirname(__file__), "..", "lambdas", "sentiment-analysis", "package", "nltk_data")
nltk.data.path.append(nltk_data_path)

os.environ["STAGE"] = "local"
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

def get_current_notifications(bucket):
    response = s3.get_bucket_notification_configuration(Bucket=bucket)
    valid_keys = ['TopicConfigurations', 'QueueConfigurations', 'LambdaFunctionConfigurations', 'EventBridgeConfiguration']
    return {k: v for k, v in response.items() if k in valid_keys}

def disable_bucket_notifications(bucket):
    s3.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration={})

def restore_notifications(bucket, original_config):
    s3.put_bucket_notification_configuration(Bucket=bucket, NotificationConfiguration=original_config)

def get_bucket_name(name) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]




def get_parameter_value(name: str) -> str:
    resp = ssm.get_parameter(Name=name)
    return resp["Parameter"]["Value"]


def get_table_name() -> str:
    return get_parameter_value("/localstack-assignment3/tables/sentiment")

@pytest.fixture(autouse=True)
def wait_for_lambda_ready():
    # Wait until the Lambda function is active
    awslambda.get_waiter("function_active").wait(FunctionName="sentiment_analysis")
    yield

def test_single_review_stored_in_dynamodb():
    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")
    table_name = get_table_name()
    table = dynamodb.Table(table_name)


    file_path = os.path.join(os.path.dirname(__file__), "onereviewprocessed.json")
    review_id = "TEST1"
    key = f"review_{review_id}.json"

    s3.upload_file(file_path, Bucket=source_bucket, Key=key)

    event = {
        "Records": [
            {"body": json.dumps({
                "detail": {
                    "bucket": {"name": source_bucket},
                    "object": {"key": key}
                }
            })}
        ]
    }
    awslambda.invoke(
        FunctionName="sentiment_analysis",
        InvocationType="Event",
        Payload=json.dumps(event).encode("utf-8")
    )

    found = False
    for _ in range(20):
        resp = table.get_item(Key={'ReviewID': review_id})
        if 'Item' in resp:
            found = True
            break
        time.sleep(1)
    assert found, f"Item with ReviewID '{review_id}' was not written to DynamoDB"
    found = False
    for _ in range(20):
        resp = table.get_item(Key={'ReviewID': review_id})
        if 'Item' in resp:
            found = True
            break
        time.sleep(1)
    assert found, f"Item with ReviewID '{review_id}' was not written to DynamoDB"

    table.delete_item(Key={'ReviewID': review_id})
    s3.delete_object(Bucket=source_bucket, Key=key)

def invoke_sentiment_lambda(bucket: str, key: str):
    event = {
        "Records": [
            {
                "body": json.dumps({
                    "detail": {
                        "bucket": {"name": bucket},
                        "object": {"key": key}
                    }
                })
            }
        ]
    }
    awslambda.invoke(
        FunctionName="sentiment_analysis",
        InvocationType="Event",
        Payload=json.dumps(event).encode("utf-8")
    )


def test_sentiment_label_and_score():
    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")
    table = dynamodb.Table(get_table_name())

    file_path = os.path.join(os.path.dirname(__file__), "onereviewprocessed.json")
    review_id = "TEST2"
    key = f"review_{review_id}.json"

    with open(file_path, "r") as f:
        review = json.load(f)

    s3.upload_file(file_path, Bucket=source_bucket, Key=key)
    invoke_sentiment_lambda(source_bucket, key)

    item = None
    for _ in range(20):
        resp = table.get_item(Key={'ReviewID': review_id})
        if 'Item' in resp:
            item = resp['Item']
            break
        time.sleep(1)
    assert item, f"Item with ReviewID '{review_id}' not found"

    assert item['ReviewID'] == review_id
    expected_user = review.get('reviewerID', 'UNKNOWN')
    assert item['UserID'] == expected_user, f"Expected UserID '{expected_user}', got '{item['UserID']}'"
    assert item['sentiment'] in ("positive", "neutral", "negative")
    score = float(item['sentimentScore'])
    assert -1.0 <= score <= 1.0, "sentimentScore out of range"

    table.delete_item(Key={'ReviewID': review_id})
    s3.delete_object(Bucket=source_bucket, Key=key)


