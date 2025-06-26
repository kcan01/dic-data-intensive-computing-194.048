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

os.environ["AWS_DEFAULT_REGION"]    = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"]     = "test"
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

def get_bucket_name(name: str) -> str:
    parameter = ssm.get_parameter(Name=name)
    return parameter["Parameter"]["Value"]

@pytest.fixture(autouse=True)
def _wait_for_lambda():
    awslambda.get_waiter("function_active").wait(FunctionName="sentiment_analysis")
    yield

def get_table_name() -> str:
    param = ssm.get_parameter(Name="/localstack-assignment3/tables/sentiment")
    return param["Parameter"]["Value"]

from lambdas.sentiment_analysis.handler import get_deterministic_key

# def test_single_review_stored_in_dynamodb():
#     source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
#     table_name    = get_table_name()
#     table         = dynamodb.Table(table_name)
#
#     #file_path = os.path.join(os.path.dirname(__file__), "onereviewprocessed.json")
#     file_path = os.path.join(os.path.dirname(__file__), os.pardir, "onereviewprocessed.json")
#     key       = os.path.basename(file_path)[:-5] + "_TEST1.json"
#
#     with open(file_path, "r") as f:
#         review = json.load(f)
#     key_out = get_deterministic_key(review)
#
#     s3.upload_file(file_path, Bucket=source_bucket, Key=key)
#
#     found = False
#     for _ in range(20):
#         resp = table.get_item(Key={'ReviewID': key_out})
#         if 'Item' in resp:
#             found = True
#             break
#         time.sleep(1)
#     assert found, "Item was not written to DynamoDB"
#
#     table.delete_item(Key={'id': key_out})
#     s3.delete_object(Bucket=source_bucket, Key=key)
#
# def test_sentiment_label_and_score():
#     source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
#     table_name    = get_table_name()
#     table         = dynamodb.Table(table_name)
#
#     file_path = os.path.join(os.path.dirname(__file__), "onereviewprocessed.json")
#     key       = os.path.basename(file_path)[:-5] + "_TEST2.json"
#
#     with open(file_path, "r") as f:
#         review = json.load(f)
#     key_out = get_deterministic_key(review)
#
#     s3.upload_file(file_path, Bucket=source_bucket, Key=key)
#     for _ in range(20):
#         resp = table.get_item(Key={'ReviewID': key_out})
#         if 'Item' in resp:
#             item = resp['Item']
#             break
#         time.sleep(1)
#     assert 'Item' in resp
#
#     assert item['id'] == key_out
#     assert item['reviewerID'] == review.get('reviewerID', '')
#     assert item['asin']       == review.get('asin', '')
#     assert item['sentiment'] in ("positive", "neutral", "negative")
#     score = float(item['compoundScore'])
#     assert -1.0 <= score <= 1.0
#
#     table.delete_item(Key={'ReviewID': key_out})
#     s3.delete_object(Bucket=source_bucket, Key=key)

#  def test_multiple_reviews_written():
#     source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
#     table_name    = get_table_name()
#     table         = dynamodb.Table(table_name)
#
#     file_path = os.path.join(os.path.dirname(__file__), "tenreviews.json")
#     key       = os.path.basename(file_path)
#
#     keys_out = []
#     with open(file_path, "r") as f:
#         for line in f:
#             review = json.loads(line)
#             keys_out.append(get_deterministic_key(review))
#
#     s3.upload_file(file_path, Bucket=source_bucket, Key=key)
#
#     for key_out in keys_out:
#         for _ in range(20):
#             resp = table.get_item(Key={'id': key_out})
#             if 'Item' in resp:
#                 break
#             time.sleep(1)
#         assert 'Item' in resp
#         table.delete_item(Key={'id': key_out})
#
#     s3.delete_object(Bucket=source_bucket, Key=key)
