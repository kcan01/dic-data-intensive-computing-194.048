import typing
import pytest
import os
import json
import boto3
import uuid
import time

if typing.TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBServiceResource


os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"


ssm: "SSMClient" = boto3.client(
    "ssm", endpoint_url="http://localhost.localstack.cloud:4566"
)
awslambda: "LambdaClient" = boto3.client(
    "lambda", endpoint_url="http://localhost.localstack.cloud:4566"
)
dynamodb: "DynamoDBServiceResource" = boto3.resource(
    "dynamodb", endpoint_url="http://localhost.localstack.cloud:4566"
)


def get_users_table_name():
    response = ssm.get_parameter(Name="/localstack-assignment3/tables/users")
    return response["Parameter"]["Value"]


@pytest.fixture(autouse=True)
def _wait_for_lambdas():
    # makes sure that the lambdas are available before running integration tests
    awslambda.get_waiter("function_active").wait(FunctionName="update_profanity_counter")
    yield


def test_update_profanity_counter_inserts_user():
    table_name = get_users_table_name()
    table = dynamodb.Table(table_name)

    # generate random uuid for user_id
    user_id = f"test-user-{uuid.uuid4()}"
    print(user_id)
    
    # simulate INSERT event from DynamoDB stream
    event = {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "UserID": {"S": user_id},
                        "contains_profanity": {"BOOL": True}
                    }
                }
            }
        ]
    }

    # Invoke the Lambda directly
    response = awslambda.invoke(
        FunctionName="update_profanity_counter",
        Payload=json.dumps(event).encode("utf-8"),
        InvocationType="RequestResponse"
    )
    assert response["StatusCode"] == 200

    # validate that the user was added in Users table
    for _ in range(5):
        response = table.get_item(Key={"UserID": user_id})
        if "Item" in response:
            break
        time.sleep(1)
    assert "Item" in response, "User not found in table"

    user = response.get("Item")
    assert user is not None, "User not found in table"
    assert user["n_profane_reviews"] == 1
    assert user["is_banned"] is False


def test_ban_user_after_more_than_three_profanities():
    table_name = get_users_table_name()
    table = dynamodb.Table(table_name)

    ban_user_id = f"NEW-test-user-ban-{uuid.uuid4()}"

    # pre-insert a user with 3 offenses
    table.put_item(Item={
        "UserID": ban_user_id,
        "n_profane_reviews": 3,
        "is_banned": False,
    })

    # simulate a fourth profane review
    event = {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "UserID": {"S": ban_user_id},
                        "contains_profanity": {"BOOL": True}
                    }
                }
            }
        ]
    }

    awslambda.invoke(
        FunctionName="update_profanity_counter",
        Payload=json.dumps(event).encode("utf-8"),
        InvocationType="RequestResponse",
    )

    for _ in range(5):
        response = table.get_item(Key={"UserID": ban_user_id})
        if "Item" in response:
            break
        time.sleep(1)
    assert "Item" in response, "User not found in table"

    user = response.get("Item")

    assert user is not None
    assert user["n_profane_reviews"] == 4
    assert user["is_banned"] is True
