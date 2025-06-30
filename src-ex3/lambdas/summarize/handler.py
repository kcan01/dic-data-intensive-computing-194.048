import json
import os
import boto3
import typing
from datetime import datetime

if typing.TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient
    from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

endpoint_url = None
if os.getenv("STAGE") == "local":
    endpoint_url = "https://localhost.localstack.cloud:4566"

ssm: "SSMClient" = boto3.client("ssm", endpoint_url=endpoint_url)
dynamodb: "DynamoDBClient" = boto3.resource("dynamodb", endpoint_url=endpoint_url)

def get_table_name(table_type: str) -> str:
    parameter = ssm.get_parameter(Name=f"/localstack-assignment3/tables/{table_type}")
    return parameter["Parameter"]["Value"]

def handler(event, context):
    try:
        #get table references
        sentiment_table = dynamodb.Table(get_table_name("sentiment"))
        profanity_table = dynamodb.Table(get_table_name("profanity"))
        users_table = dynamodb.Table(get_table_name("users"))
        
        #scan sentiment table
        response = sentiment_table.scan()
        sentiment_items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = sentiment_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            sentiment_items.extend(response['Items'])
        
        #count sentiments
        sentiment_counts = {
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        for item in sentiment_items:
            sentiment = item.get('sentiment', 'unknown')
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
        
        #scan profanity table
        response = profanity_table.scan()
        profanity_items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = profanity_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            profanity_items.extend(response['Items'])
        
        #count profanity failures
        profanity_count = sum(1 for item in profanity_items if item.get('contains_profanity', False))
        
        #scan users table
        response = users_table.scan()
        users_items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = users_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            users_items.extend(response['Items'])
        
        #find banned users
        banned_users = []
        for item in users_items:
            if item.get('n_profane_reviews', 0) > 3 or item.get('is_banned', False):
                banned_users.append(item['UserID'])
        
        #create summary
        total_reviews = len(sentiment_items)
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_reviews_processed": total_reviews,
            "sentiment_breakdown": {
                "positive": sentiment_counts['positive'],
                "neutral": sentiment_counts['neutral'],
                "negative": sentiment_counts['negative']
            },
            "profanity_check": {
                "failed_reviews": profanity_count,
                "passed_reviews": total_reviews - profanity_count
            },
            "banned_users": {
                "count": len(banned_users),
                "user_ids": banned_users
            }
        }
        
        #output to logs
        print("=== REVIEW PROCESSING SUMMARY ===")
        print(json.dumps(summary, indent=2))
        print("================================")
        
        #return http response
        return {
            'statusCode': 200,
            'body': json.dumps(summary, indent=2),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        error_msg = f"Error generating summary: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()  #debug
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }