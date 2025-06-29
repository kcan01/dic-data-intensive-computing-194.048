import boto3
from boto3.dynamodb.conditions import Key
import os
import typing

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


def get_users_table_name():
    response = ssm.get_parameter(Name="/localstack-assignment3/tables/users")
    return response["Parameter"]["Value"]

USERS_TABLE = get_users_table_name()


def handler(event, context):
    for record in event.get("Records", []):
        if record["eventName"] != "INSERT":
            continue

        new_image = record["dynamodb"].get("NewImage", {})
        user_id = new_image.get("UserID", {}).get("S")
        contains_profanity = new_image.get("contains_profanity", {}).get("BOOL", False)

        if not user_id:
            print("Missing UserID in the record, therefore skipping.")
            continue

        if not contains_profanity:
            print("No information on profanity, therefore skipping.")
            continue

        # try to get the current user's item
        try:
            response = dynamodb.get_item(
                TableName=USERS_TABLE,
                Key={"UserID": {"S": user_id}},
            )
            item = response.get("Item", {})
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            continue

        # get current count or start from 0
        current_count = int(item.get("n_profane_reviews", {}).get("N", "0"))
        new_count = current_count + 1
        is_banned = new_count > 0

        # update or insert user with new count and ban status
        try:
            dynamodb.put_item(
                TableName=USERS_TABLE,
                Item={
                    "UserID": {"S": user_id},
                    "n_profane_reviews": {"N": str(new_count)},
                    "is_banned": {"BOOL": is_banned},
                }
            )
            print(f"Updated user {user_id}: count={new_count}, banned={is_banned}")
        except Exception as e:
            print(f"Failed to update user {user_id}: {e}")
