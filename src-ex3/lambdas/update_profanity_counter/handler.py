import boto3
import json

def process_item(item):
    # Convert DynamoDB JSON to normal Python dict
    return {k: list(v.values())[0] for k, v in item.items()}


def handle_item(item):
    # This is your custom function for each item
    print(f"Handling item with ID: {item.get('id')}, sentiment: {item.get('sentiment')}")



def handler(event, context):
    for record in event['Records']:
        record['eventID']
        record['eventName']  # INSERT, MODIFY, REMOVE
        record['dynamodb']['Keys']
        if record['eventName'] == 'INSERT':
            raw_item = record['dynamodb']['NewImage']
            item = process_item(raw_item)
            handle_item(item)
