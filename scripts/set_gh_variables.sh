#!/bin/bash
# Script to set GitHub Actions variables via API

REPO="usipipo/usipipobot"
TOKEN=$(gh auth token)

# Variables to set
declare -A VARS=(
    ["QWEN_BASE_URL"]="https://dashscope.aliyuncs.com/compatible-mode/v1"
    ["QWEN_MODEL"]="qwen-max"
    ["QWEN_CLI_VERSION"]="latest"
    ["UPLOAD_ARTIFACTS"]="true"
    ["DEBUG"]="false"
    ["TELEGRAM_CHAT_ID"]="-1001234567890"
)

echo "🔧 Setting GitHub Actions variables..."

for name in "${!VARS[@]}"; do
    value="${VARS[$name]}"
    echo "  Setting $name..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X PUT \
        -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        -H "Content-Type: application/json" \
        "https://api.github.com/repos/$REPO/actions/variables/$name" \
        -d "{\"name\":\"$name\",\"value\":\"$value\"}")
    
    if [ "$response" = "204" ]; then
        echo "  ✅ $name"
    else
        echo "  ❌ $name (HTTP $response)"
    fi
done

echo "Done!"
