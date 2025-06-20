import typing
import pytest
import json
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import boto3

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_lambda import LambdaClient

import nltk
from nltk.corpus import stopwords
nltk_data_path = os.path.join(os.path.dirname(__file__), "..", "lambdas", "preprocessing", "package", "nltk_data")
nltk.data.path.append(nltk_data_path)


stop_words = set(stopwords.words('english'))


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


@pytest.fixture(autouse=True)
def _wait_for_lambdas():
    # makes sure that the lambdas are available before running integration tests
    awslambda.get_waiter("function_active").wait(FunctionName="preprocessing")

    # Disable bucket notifications on target bucket to prevent function chain
    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
    target_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")
    original_config = get_current_notifications(target_bucket)
    disable_bucket_notifications(target_bucket)

    # the actual tests are run here
    yield

    # restore bucket notifications
    restore_notifications(target_bucket, original_config)

print(os.getcwd())
from lambdas.preprocessing.handler import get_deterministic_key, s3_object_exists


def test_insert():
    file = os.path.join(os.path.dirname(__file__), "onereview.json")
    key = os.path.basename(file)[:-5] + "TEST1" + ".json"

    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
    target_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")

    with open(file, "r") as f:
        review = json.load(f)
    key_out = get_deterministic_key(review)

    s3.upload_file(file, Bucket=source_bucket, Key=key)
    # wait for the resized image to appear
    s3.get_waiter("object_exists").wait(Bucket=target_bucket, Key=key_out)

    s3.delete_object(Bucket=source_bucket, Key=key)
    s3.delete_object(Bucket=target_bucket, Key=key_out)


def test_preprocessing():
    file = os.path.join(os.path.dirname(__file__), "onereview.json")
    key = os.path.basename(file)[:-5] + "TEST2" + ".json"

    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
    target_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")

    with open(file, "r") as f:
        review = json.load(f)
    key_out = get_deterministic_key(review)

    s3.upload_file(file, Bucket=source_bucket, Key=key)
    # wait for the resized image to appear
    s3.get_waiter("object_exists").wait(Bucket=target_bucket, Key=key_out)

    s3.head_object(Bucket=target_bucket, Key=key_out)
    outfile = "/tmp/review_test.json"
    s3.download_file(
        Bucket=target_bucket, Key=key_out, Filename=outfile
    )

    with open(outfile, "r") as f:
        review_processed = json.load(f)

    id = review_processed["reviewerID"]
    tokens = review_processed["reviewText"]
    summary = review_processed["summary"]

    assert isinstance(id, str)
    assert isinstance(tokens, list)
    assert isinstance(summary, list)
    for token in tokens:
        assert isinstance(token, str)
        assert token.isalpha()
        assert token.islower()
    assert stop_words.isdisjoint(set(tokens))
    for token in summary:
        assert isinstance(token, str)
        assert token.isalpha()
        assert token.islower()
    assert stop_words.isdisjoint(set(summary))

    os.remove(outfile)
    s3.delete_object(Bucket=source_bucket, Key=key)
    s3.delete_object(Bucket=target_bucket, Key=key_out)



def test_review_splitting():
    file = os.path.join(os.path.dirname(__file__), "tenreviews.json")
    key = os.path.basename(file)

    source_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsraw")
    target_bucket = get_bucket_name(name="/localstack-assignment3/buckets/reviewsprocessed")

    keys_out=[]
    with open(file, "r") as f:
        for line in f:
            review = json.loads(line)
            keys_out.append( get_deterministic_key(review) )

    s3.upload_file(file, Bucket=source_bucket, Key=key)

    waiter = s3.get_waiter("object_exists")
    for key_out in keys_out:
        waiter.wait(Bucket=target_bucket, Key=key_out)
        s3.delete_object(Bucket=target_bucket, Key=key_out)

    s3.delete_object(Bucket=source_bucket, Key=key)

