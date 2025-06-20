import json
import os
import typing
import hashlib
from urllib.parse import unquote_plus
import uuid

import boto3
from botocore.exceptions import ClientError

import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
nltk.data.path.append(nltk_data_path)

if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient

endpoint_url = None
if os.getenv("STAGE") == "local":
    endpoint_url = "https://localhost.localstack.cloud:4566"

s3: "S3Client" = boto3.client("s3", endpoint_url=endpoint_url)
ssm: "SSMClient" = boto3.client("ssm", endpoint_url=endpoint_url)



lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))
punct_table = str.maketrans("", "", string.punctuation)


def get_bucket_name() -> str:
    parameter = ssm.get_parameter(Name="/localstack-assignment3/buckets/reviewsprocessed")
    return parameter["Parameter"]["Value"]

class ReviewSplitter:
    def __init__(self, source_bucket: str, key: str):
        self.bucket = source_bucket
        self.key = key.replace("/", "")
        self.download_path = f"/tmp/{uuid.uuid4()}{self.key}"
        s3.download_file(self.bucket, self.key, self.download_path)

    def get(self):
        decode_success = 0
        decode_failure = 0
        with open(self.download_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    single_review = json.loads(line)
                    decode_success += 1
                    yield single_review
                except json.decoder.JSONDecodeError:
                    decode_failure += 1
                    continue

        print(f"Finished preprocessing, {decode_success} reviews processed, {decode_failure} failures ")

def s3_object_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise

def upload_dict_to_s3(data: dict, bucket: str):
    def get_deterministic_key(review_str: str) -> str:
        hash_digest = hashlib.sha256(review_str.encode("utf-8")).hexdigest()
        return f"review_{hash_digest}.json"
        
    review_str = json.dumps(data, sort_keys=True)
    key = get_deterministic_key(review_str)
    if not s3_object_exists(bucket, key):
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=review_str,
            ContentType="application/json"
        )

def preprocess_single_review(review: dict) -> dict:
    preprocessed_review = {}
    def preprocess(text):
        tokens = nltk.word_tokenize(text.lower().translate(punct_table))
        return [
            lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalpha() and token not in stop_words
        ]
    preprocessed_review["reviewerID"] = review.get("reviewerID", "")
    preprocessed_review["reviewText"] = preprocess(review.get("reviewText", ""))
    preprocessed_review["summary"] = preprocess(review.get("summary", ""))
    return preprocessed_review

def handler(event, context):
    target_bucket = get_bucket_name()

    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        key = unquote_plus(key)

        print(f"New file added: {key} in bucket {source_bucket}")

        Iterator = ReviewSplitter(source_bucket, key)
        for review in Iterator.get():
            cleaned_review = preprocess_single_review(review)
            upload_dict_to_s3(cleaned_review, target_bucket)


