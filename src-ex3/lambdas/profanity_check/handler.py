import json
import os
import typing
import hashlib
from urllib.parse import unquote_plus
import uuid
import boto3
from botocore.exceptions import ClientError

from profanity_filter import ProfanityFilter

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

endpoint_url = None
if os.getenv("STAGE") == "local":
    endpoint_url = "http://localhost:4566"

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

pf = ProfanityFilter()

def get_table_name() -> str:
    parameter = ssm.get_parameter(Name="/localstack-assignment3/dynamodb/profanity")
    return parameter["Parameter"]["Value"]


def get_deterministic_key(data: dict) -> str:
    reviewer = data.get("reviewerID", "")
    date = data.get("unixReviewTime", "")
    asin = data.get("asin", "")
    identifier = f"{reviewer}+{date}+{asin}"
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()

def flag_profanity(review: dict) -> dict:
    review_text = review.get("reviewText", "")
    summary = review.get("summary", "")

    contains_profanity = pf.is_profane(review_text) or pf.is_profane(summary)

    return {
        "id": get_deterministic_key(review),
        "reviewerID": review.get("reviewerID", ""),
        "asin": review.get("asin", ""),
        "reviewText": review_text,
        "summary": summary,
        "contains_profanity": contains_profanity
    }

def write_to_dynamodb(review_item: dict, table_name: str):
    table = dynamodb.Table(table_name)
    table.put_item(Item=review_item)
    
class ReviewSplitter:
    def __init__(self, source_bucket: str, key: str):
        self.bucket = source_bucket
        self.key = key.replace("/", "")
        self.download_path = f"/tmp/{uuid.uuid4()}{self.key}"
        s3.download_file(self.bucket, self.key, self.download_path)

    def get(self):
        with open(self.download_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue


def handler(event, context):
    table_name = get_table_name()

    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])

        print(f"Checking profanity and writing to DynamoDB: {key}")

        reviews = ReviewSplitter(source_bucket, key)
        for review in reviews.get():
            item = flag_profanity(review)
            write_to_dynamodb(item, table_name)
