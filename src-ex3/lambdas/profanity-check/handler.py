def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        print(f"New file added: {key} in bucket {bucket}")

        # Download or read the file content
        # response = s3.get_object(Bucket=bucket, Key=key)