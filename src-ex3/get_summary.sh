#!/bin/bash

url=$(awslocal lambda get-function-url-config --function-name summarize | jq -r '.FunctionUrl')
response=$(curl -s "$url")

echo "$response" | jq
echo "$response" > summary.json
