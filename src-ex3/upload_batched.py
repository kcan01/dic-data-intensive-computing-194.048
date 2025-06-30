import os

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"

import typing
import argparse
import json
import time
from pathlib import Path
if typing.TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_ssm import SSMClient
import boto3


endpoint_url = "https://localhost.localstack.cloud:4566"

s3: "S3Client" = boto3.client("s3", endpoint_url=endpoint_url)
ssm: "SSMClient" = boto3.client("ssm", endpoint_url=endpoint_url)

def get_bucket_name() -> str:
    parameter = ssm.get_parameter(Name="/localstack-assignment3/buckets/reviewsraw")
    return parameter["Parameter"]["Value"]

def parse_args():
    parser = argparse.ArgumentParser(description="Upload a file to S3 in batches.")
    parser.add_argument("filename", type=str, help="Path to the input file (JSON lines or array).")
    parser.add_argument("batchsize", type=int, help="Number of reviews per batch.")
    parser.add_argument("time_between", type=float, help="Minutes to sleep between batches.")
    return parser.parse_args()

def load_reviews(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        try:
            return json.loads(content)  # If it's a full JSON array
        except json.JSONDecodeError:
            f.seek(0)
            return [json.loads(line.strip()) for line in f if line.strip()]  # JSONL

def upload_batches(file_path, batchsize, time_between):
    bucket = get_bucket_name()
    prefix = file_path.stem

    batch = []
    batch_index = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            batch.append(line)

            if len(batch) == batchsize:
                batch_key = f"{prefix}_{batch_index:04d}.json"
                print(f"Uploading batch {batch_index + 1} ({len(batch)} lines) to s3://{bucket}/{batch_key}")
                s3.put_object(
                    Bucket=bucket,
                    Key=batch_key,
                    Body="".join(batch).encode("utf-8"),
                    ContentType="application/json"
                )
                batch = []
                batch_index += 1
                time.sleep(int(time_between * 60))

    # Upload any remaining reviews in the last batch
    if batch:
        batch_key = f"{prefix}_{batch_index:04d}.json"
        print(f"Uploading final batch {batch_index + 1} ({len(batch)} lines) to s3://{bucket}/{batch_key}")
        s3.put_object(
            Bucket=bucket,
            Key=batch_key,
            Body="".join(batch).encode("utf-8"),
            ContentType="application/json"
        )

def main():
    args = parse_args()

    file_path = Path(args.filename)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    upload_batches(file_path, args.batchsize, args.time_between)

if __name__ == "__main__":
    main()
