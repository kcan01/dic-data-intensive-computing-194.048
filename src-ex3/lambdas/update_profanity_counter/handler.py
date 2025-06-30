import boto3
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
client: "DynamoDBClient" = boto3.client("dynamodb", endpoint_url=endpoint_url)
dynamodb: "DynamoDBServiceResource" = boto3.resource("dynamodb", endpoint_url=endpoint_url)



def get_users_table_name():
    response = ssm.get_parameter(Name="/localstack-assignment3/tables/users")
    return response["Parameter"]["Value"]

USERS_TABLE = get_users_table_name()
table = dynamodb.Table(USERS_TABLE)


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
            response = table.get_item(Key={"UserID": user_id})
            item = response.get("Item", {})
        except Exception as e:
            print(f"Error fetching user {user_id}: {e}")
            continue

        # get current count or start from 0
        current_count = item.get("n_profane_reviews", 0)
        new_count = current_count + 1
        is_banned = new_count > 3

        # update or insert user with new count and ban status
        try:
            table.put_item(
                Item={
                    "UserID": user_id,
                    "n_profane_reviews": new_count,
                    "is_banned": is_banned,
                }
            )
            print(f"Updated user {user_id}: count={new_count}, banned={is_banned}")
        except Exception as e:
            print(f"Failed to update user {user_id}: {e}")
