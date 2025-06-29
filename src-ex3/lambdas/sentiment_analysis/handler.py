import json
import os
import typing
from urllib.parse import unquote_plus
import re

import boto3
from botocore.exceptions import ClientError

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

endpoint_url = None
if os.getenv("STAGE") == "local":
    endpoint_url = "https://localhost.localstack.cloud:4566"


s3: "S3Client" = boto3.client("s3", endpoint_url=endpoint_url)
ssm: "SSMClient" = boto3.client("ssm", endpoint_url=endpoint_url)
client: "DynamoDBServiceResource" = boto3.client("dynamodb", endpoint_url=endpoint_url)
dynamodb: "DynamoDBClient" = boto3.resource("dynamodb", endpoint_url=endpoint_url)

nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
nltk.data.path.append(nltk_data_path)

analyzer = SentimentIntensityAnalyzer()

def test_ssm_connection():
    try:
        response = ssm.describe_parameters(MaxResults=1)
        return True
    except Exception as e:
        print("[SSM Connection] Failed:", e)
        return False

def get_table_name():
    test_ssm_connection()
    try:
        param = ssm.get_parameter(Name="/localstack-assignment3/tables/sentiment", WithDecryption=False)
        return param["Parameter"]["Value"]
    except Exception as e:
        print("[get_table_name] Error:", e)
        raise


def flag_sentiment(review: dict) -> dict:
    text    = " ".join(review.get("reviewText", []))
    summary = " ".join(review.get("summary",    []))
    combined = f"{text} {summary}".strip()

    scores   = analyzer.polarity_scores(combined)
    compound = scores["compound"]
    # maybe still change the definition of neutral?
    if compound >=  0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "UserID":     review.get("reviewerID", "UNKNOWN"),
        "sentiment":      label,
        "sentimentScore":  str(compound)
    }


def get_review_id(filename: str) -> str:
    match = re.fullmatch(r'review_(.+)\.json', filename)
    if match:
        return match.group(1)
    else:
        return "UNKNOWN"

def handler(event, context):
    table_name = get_table_name()
    table = dynamodb.Table(table_name)

    for record in event["Records"]:
        body_str = record["body"]
        body = json.loads(body_str)  # Parse JSON string to dict

        detail = body.get("detail", {})
        bucket = detail["bucket"]["name"]
        key = unquote_plus(detail["object"]["key"])

        obj = s3.get_object(Bucket=bucket, Key=key)
        review = json.loads(obj["Body"].read().decode("utf-8"))

        result = flag_sentiment(review)
        result["ReviewID"] = get_review_id(key)

        table.put_item(Item=result)

    return
