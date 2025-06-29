import os
import json
import boto3
from urllib.parse import unquote_plus
from better_profanity import profanity
import typing
import re

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

# Profanity Init
profanity.load_censor_words()

def get_table_name() -> str:
    response = ssm.get_parameter(Name="/localstack-assignment3/tables/profanity")
    return response["Parameter"]["Value"]


def flag_profanity(review: dict) -> dict:
    review_text = review.get("reviewText", "")
    summary = review.get("summary", "")
    contains_profanity = profanity.contains_profanity(" ".join(review_text)) or profanity.contains_profanity(" ".join(summary))

    return {
        "UserID": review.get("reviewerID", ""),
        "contains_profanity": bool(contains_profanity)
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

        result = flag_profanity(review)
        result['ReviewID'] = get_review_id(key)

        table.put_item(
            Item=result
        )
