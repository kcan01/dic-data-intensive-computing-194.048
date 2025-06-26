
import os
import json
import boto3
from urllib.parse import unquote_plus
from better_profanity import profanity
import typing
import hashlib

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource
    
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


# Profanity Init
profanity.load_censor_words()

def get_table_name() -> str:
    response = ssm.get_parameter(Name="/localstack-assignment3/tables/profanity")
    return response["Parameter"]["Value"]


def flag_profanity(review: dict) -> dict:
    review_text = review.get("reviewText", "")
    summary = review.get("summary", "")
    contains_profanity = profanity.contains_profanity(review_text) or profanity.contains_profanity(summary)

    return {
        "reviewerID": review.get("reviewerID", ""),
        "reviewText": review_text,
        "summary": summary,
        "contains_profanity": contains_profanity
    }

def handler(event, context):
    table_name = get_table_name()

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])
        print(f"Processing file: {key} from bucket: {bucket}")

        obj = s3.get_object(Bucket=bucket, Key=key)
        review = json.loads(obj["Body"].read().decode("utf-8"))

        result = flag_profanity(review)

        dynamodb.put_item(
            TableName=table_name,
            Item={
                "reviewerID": {"S": result["reviewerID"]},
                "reviewText": {"S": result["reviewText"]},
                "summary": {"S": result["summary"]},
                "contains_profanity": {"BOOL": result["contains_profanity"]},
            }
        )

        print(f"Inserted review {result['id']} with profanity={result['contains_profanity']}")
