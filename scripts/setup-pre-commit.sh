#!/usr/bin/env bash
# =============================================================================
# Pre-commit Setup Script for uSipipo VPN Bot
# =============================================================================
# Usage: ./scripts/setup-pre-commit.sh
# =============================================================================

set -e

echo "🔧 Setting up pre-commit hooks for uSipipo VPN Bot..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if we're in the project directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Are you in the project root?"
    exit 1
fi

# Sync dependencies
echo "📦 Syncing development dependencies..."
uv sync --dev

# Install pre-commit hooks
echo "🔗 Installing pre-commit git hooks..."
uv run pre-commit install

# Verify installation
echo ""
echo "✅ Pre-commit setup complete!"
echo ""
echo "📝 Quick reference:"
echo "   • Hooks run automatically on 'git commit'"
echo "   • Run manually: uv run pre-commit run --all-files"
echo "   • Update hooks: uv run pre-commit autoupdate"
echo "   • Bypass hooks (emergency): git commit --no-verify"
echo ""
