#!/bin/bash
set -e
echo "World Today Blog Container Starting"
required_vars=(GEMINI_API_KEY GITHUB_REPO_URL GITHUB_USER_NAME GITHUB_USER_EMAIL)
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required environment variable '$var' is not set."
        exit 1
    fi
done
echo "All required environment variables present."
exec python /app/scheduler.py
