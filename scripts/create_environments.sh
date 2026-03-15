#!/bin/bash
# Create GitHub environments

REPO="usipipo/usipipobot"
TOKEN=$(gh auth token)

create_environment() {
    local name=$1
    local url=$2
    
    echo "Creating environment: $name..."
    
    if [ -n "$url" ]; then
        response=$(curl -s \
            -X PUT \
            -H "Authorization: token $TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.github.com/repos/$REPO/environments/$name" \
            -d "{\"deployment_branch_policy\":{\"protected_branches\":false,\"custom_branches\":true},\"wait_timer\":0}")
    else
        response=$(curl -s \
            -X PUT \
            -H "Authorization: token $TOKEN" \
            -H "Accept: application/vnd.github+json" \
            -H "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.github.com/repos/$REPO/environments/$name" \
            -d '{}')
    fi
    
    if echo "$response" | jq -e '.name' > /dev/null 2>&1; then
        echo "  ✅ $name created"
    elif echo "$response" | jq -e '.message' | grep -q "Already"; then
        echo "  ℹ️  $name already exists"
    else
        error=$(echo "$response" | jq -r '.message // "Unknown error"')
        echo "  ❌ $name - $error"
    fi
}

echo "🔧 Creating GitHub environments..."

create_environment "staging" "https://staging.usipipo.com"
create_environment "release" ""

echo ""
echo "Done!"
