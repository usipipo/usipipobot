#!/bin/bash
# Script to set GitHub Actions variables via API

REPO="usipipo/usipipobot"
TOKEN=$(gh auth token)

set_variable() {
    local name=$1
    local value=$2
    
    response=$(curl -s \
        -X PUT \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        -H "Content-Type: application/json" \
        "https://api.github.com/repos/$REPO/actions/variables/$name" \
        -d "{\"value\":\"$value\"}")
    
    if [ -z "$response" ]; then
        echo "  ✅ $name"
        return 0
    else
        error=$(echo "$response" | jq -r '.message // "Unknown error"')
        echo "  ❌ $name - $error"
        return 1
    fi
}

echo "🔧 Setting GitHub Actions variables..."
echo ""

# Repository variables
echo "📋 Repository Variables:"
set_variable "QWEN_BASE_URL" "https://dashscope.aliyuncs.com/compatible-mode/v1"
set_variable "QWEN_MODEL" "qwen-max"
set_variable "QWEN_CLI_VERSION" "latest"
set_variable "UPLOAD_ARTIFACTS" "true"
set_variable "DEBUG" "false"
set_variable "TELEGRAM_CHAT_ID" "1058749165"

echo ""
echo "✅ Done!"
echo ""
echo "Note: If you see 'Not Found' errors, you need to set these variables manually via GitHub UI:"
echo "  https://github.com/usipipo/usipipobot/settings/actions/variables"
