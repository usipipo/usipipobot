#!/bin/bash
# Check existing variables

REPO="usipipo/usipipobot"
TOKEN=$(gh auth token)

echo "📋 Checking existing variables..."
curl -s \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$REPO/actions/variables" | jq '.'
