#!/bin/bash
# Check GitHub variables

REPO="usipipo/usipipobot"
TOKEN=$(gh auth token)

echo "📋 Checking GitHub Actions variables..."
echo ""

response=$(curl -s \
    -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$REPO/actions/variables")

echo "$response" | jq -r '
    if .variables then
        .variables[] | "✅ \(.name) = \(.value)"
    else
        "❌ Cannot read variables (may need admin permissions)"
    end
'

echo ""
echo "📋 Checking GitHub Actions secrets..."
gh secret list
