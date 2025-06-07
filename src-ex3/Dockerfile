# Dockerfile
FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PAGER=cat
ENV AWS_PAGER=""

# Install OS packages
RUN apt-get update && apt-get install -y \
    zip jq curl awscli bash git build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Default to bash shell
CMD ["/bin/bash"]