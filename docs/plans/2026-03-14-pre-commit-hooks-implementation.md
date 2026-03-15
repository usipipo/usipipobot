# Pre-commit Hooks & CI/CD Enhancement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement professional pre-commit hooks with auto-formatting and enhance CI/CD pipeline with comprehensive quality gates.

**Architecture:** Two-tier quality gate system: fast pre-commit hooks for local development (auto-fix formatting) + thorough CI checks for pull requests (linting, type checking, security).

**Tech Stack:** pre-commit, black, isort, flake8, mypy, bandit, GitHub Actions.

---

## Overview

This plan implements:
1. Pre-commit configuration with 7 hooks (auto-fix capable)
2. Enhanced CI/CD workflow with pre-commit job
3. isort configuration for import sorting
4. Developer documentation and setup scripts

---

### Task 1: Create Pre-commit Configuration File

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Create the pre-commit configuration**

```yaml
# =============================================================================
# PRE-COMMIT HOOKS CONFIGURATION
# =============================================================================
# Install: uv run pre-commit install
# Run manually: uv run pre-commit run --all-files
# Update hooks: uv run pre-commit autoupdate
# =============================================================================

repos:
  # =============================================================================
  # STANDARD HOOKS (pre-commit-hooks)
  # =============================================================================
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # Remove trailing whitespace
      - id: trailing-whitespace
        description: Removes trailing whitespace from files
      
      # Ensure files end with a newline
      - id: end-of-file-fixer
        description: Ensures files end with a newline
      
      # Validate YAML syntax
      - id: check-yaml
        description: Validates YAML syntax
        args: ['--unsafe']  # Allow custom tags
      
      # Validate JSON syntax
      - id: check-json
        description: Validates JSON syntax
      
      # Detect private keys
      - id: detect-private-key
        description: Detects presence of private keys
      
      # Check for merge conflicts
      - id: check-merge-conflict
        description: Checks for merge conflict markers
      
      # Check added files for symlinks
      - id: check-symlinks
        description: Checks for broken symlinks

  # =============================================================================
  # IMPORT SORTING (isort)
  # =============================================================================
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        name: isort (python)
        description: Sorts imports in Python files
        args: ['--profile', 'black', '--filter-files']

  # =============================================================================
  # CODE FORMATTING (Black)
  # =============================================================================
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        description: Formats Python code
        language_version: python3.13
        args: ['--config', 'pyproject.toml']

  # =============================================================================
  # SECURITY: SECRET DETECTION
  # =============================================================================
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        description: Detects secrets in code
        args: ['--baseline', '.secrets.baseline']
        exclude: |
          (?x)^(
            .venv/|
            venv/|
            android_app/.venv/|
            android_app/venv/|
            \.git/|
            logs/|
            .*\.json$|
            .*\.yaml$|
            .*\.yml$|
            package-lock\.json
          )

  # =============================================================================
  # SECURITY: PYTHON LINTING (Flake8)
  # =============================================================================
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        description: Lints Python code
        additional_dependencies: [
          'flake8-bugbear',
          'flake8-comprehensions',
          'flake8-simplify',
        ]
        args: [
          '--max-line-length=100',
          '--max-complexity=10',
          '--select=E9,F63,F7,F82,B,C4,SIM',
          '--extend-ignore=E203,E501,W503',
          '--exclude=.venv,venv,android_app/.venv,android_app/venv,.git,logs,migrations/versions',
        ]
```

**Step 2: Verify YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"`
Expected: No errors, prints dict

**Step 3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "feat: add pre-commit hooks configuration with auto-formatting"
```

---

### Task 2: Add Pre-commit to Development Dependencies

**Files:**
- Modify: `pyproject.toml` (add pre-commit to dev dependencies)

**Step 1: Add pre-commit dependency**

Locate the `[project.optional-dependencies]` section and add `pre-commit`:

```toml
[project.optional-dependencies]
dev = [
    "pre-commit==3.6.0",
    "pytest==9.0.2",
    "pytest-asyncio==1.3.0",
    "flake8",
    "black",
    "mypy",
]
```

Also add to `[dependency-groups]` section:

```toml
[dependency-groups]
dev = [
    "pre-commit==3.6.0",
    "pytest==9.0.2",
    "pytest-asyncio==1.3.0",
    "flake8",
    "black",
    "mypy",
]
```

**Step 2: Sync dependencies**

Run: `uv sync --dev`
Expected: pre-commit installed in .venv

**Step 3: Verify installation**

Run: `uv run pre-commit --version`
Expected: `pre-commit 3.6.0`

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pre-commit to development dependencies"
```

---

### Task 3: Add isort Configuration to pyproject.toml

**Files:**
- Modify: `pyproject.toml` (add isort configuration section)

**Step 1: Add isort configuration**

Add after the `[tool.black]` section:

```toml
# =============================================================================
# isort Configuration
# =============================================================================

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
known_first_party = ["domain", "application", "infrastructure", "telegram_bot", "miniapp", "utils", "config", "android_app"]
known_third_party = ["pytest", "pydantic", "sqlalchemy", "fastapi", "telegram", "httpx", "aiohttp"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]
skip = [".venv", "venv", "android_app/.venv", "android_app/venv", ".git", "migrations/versions"]
```

**Step 2: Verify configuration**

Run: `uv run isort --show-config`
Expected: Shows config with profile=black, line_length=100

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add isort configuration compatible with black"
```

---

### Task 4: Update .gitignore for Pre-commit Cache

**Files:**
- Modify: `.gitignore`

**Step 1: Add pre-commit cache directory**

Add to the end of `.gitignore`:

```gitignore
# =============================================================================
# PRE-COMMIT
# =============================================================================
.pre-commit/
.secrets.baseline
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add pre-commit cache to gitignore"
```

---

### Task 5: Enhance CI/CD Workflow with Pre-commit Job

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Add pre-commit job**

Add the `pre-commit` job BEFORE the existing `test` job:

```yaml
  pre-commit:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: "pip"

      - name: Install pre-commit
        run: |
          python -m pip install --upgrade pip
          pip install pre-commit

      - name: Run pre-commit hooks
        run: |
          pre-commit run --all-files --show-diff-on-failure
```

**Step 2: Update lint job to add isort**

In the existing `lint` job, add isort step after black:

```yaml
      - name: Run Black
        run: black --check --diff .

      - name: Run isort
        run: isort --check-only --diff . --profile black

      - name: Run Flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=venv,.venv,env,.git,migrations/versions
```

**Step 3: Update mypy step to be less noisy**

Modify the mypy step to use project config:

```yaml
      - name: Run MyPy
        continue-on-error: true
        run: mypy . --config-file pyproject.toml
```

**Step 4: Update job dependencies (optional)**

If you want jobs to run in sequence, add `needs: [pre-commit]` to test job.

**Step 5: Verify YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: No errors

**Step 6: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add pre-commit job and isort to CI pipeline"
```

---

### Task 6: Create Initial Secrets Baseline

**Files:**
- Create: `.secrets.baseline` (generated by detect-secrets)

**Step 1: Install detect-secrets**

Run: `uv run pip install detect-secrets`

**Step 2: Generate baseline**

Run: `uv run detect-secrets scan --baseline .secrets.baseline`
Expected: Creates baseline file (may have false positives)

**Step 3: Review baseline**

Open `.secrets.baseline` and review detected secrets. Remove false positives if needed.

**Step 4: Commit**

```bash
git add .secrets.baseline
git commit -m "chore: create initial secrets baseline for detect-secrets"
```

---

### Task 7: Install Pre-commit Locally and Test

**Files:**
- N/A (local setup)

**Step 1: Install pre-commit git hooks**

Run: `uv run pre-commit install`
Expected: `pre-commit installed at .git/hooks/pre-commit`

**Step 2: Test on a single file**

Run: `uv run pre-commit run black --files main.py`
Expected: Shows black formatting result

**Step 3: Run all hooks on all files**

Run: `uv run pre-commit run --all-files`
Expected: Runs all hooks, may auto-fix some files

**Step 4: Review and commit any changes**

If pre-commit modified files:

```bash
git add .
git commit -m "style: auto-format codebase with pre-commit hooks"
```

---

### Task 8: Create Developer Setup Script

**Files:**
- Create: `scripts/setup-pre-commit.sh`

**Step 1: Create setup script**

```bash
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
```

**Step 2: Make script executable**

Run: `chmod +x scripts/setup-pre-commit.sh`

**Step 3: Test the script**

Run: `./scripts/setup-pre-commit.sh`
Expected: Shows setup output, installs hooks

**Step 4: Commit**

```bash
git add scripts/setup-pre-commit.sh
git commit -m "docs: add pre-commit setup script for developers"
```

---

### Task 9: Update Documentation

**Files:**
- Modify: `AGENTS.md` (add pre-commit section)
- Modify: `README.md` (add pre-commit setup)

**Step 1: Add to AGENTS.md**

Add a new section after "Code Quality":

```markdown
## Pre-commit Hooks

The project uses pre-commit hooks for automatic code formatting and quality checks.

### Setup (One-time)

```bash
# Install pre-commit hooks
./scripts/setup-pre-commit.sh
# Or manually:
uv run pre-commit install
```

### Usage

```bash
# Hooks run automatically on git commit
git add .
git commit -m "feat: new feature"

# Run manually on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black --files main.py

# Update hook versions
uv run pre-commit autoupdate
```

### Hooks Configured

| Hook | Purpose | Auto-fix |
|------|---------|----------|
| trailing-whitespace | Remove trailing spaces | ✅ |
| end-of-file-fixer | Ensure newline at EOF | ✅ |
| check-yaml | Validate YAML syntax | ❌ |
| check-json | Validate JSON syntax | ❌ |
| detect-private-key | Detect leaked secrets | ❌ |
| isort | Sort imports | ✅ |
| black | Format code | ✅ |
| detect-secrets | Advanced secret detection | ❌ |
| flake8 | Python linting | ❌ |
```

**Step 2: Add to README.md**

Add to the "Development" or "Getting Started" section:

```markdown
### Pre-commit Setup (Recommended)

```bash
# Install pre-commit hooks for automatic formatting
./scripts/setup-pre-commit.sh
```

This ensures code quality and consistent formatting across the project.
```

**Step 3: Commit**

```bash
git add AGENTS.md README.md
git commit -m "docs: add pre-commit setup documentation"
```

---

### Task 10: Final Verification and Testing

**Files:**
- N/A (verification)

**Step 1: Run all pre-commit hooks**

Run: `uv run pre-commit run --all-files --show-diff-on-failure`
Expected: All hooks pass

**Step 2: Test commit workflow**

```bash
# Create a test file with bad formatting
echo "def test( ): print('bad')" > /tmp/test_bad.py
cp /tmp/test_bad.py telegram_bot/handlers/test_precommit.py

# Try to commit
git add telegram_bot/handlers/test_precommit.py
git commit -m "test: pre-commit test"
```

Expected: Pre-commit hooks auto-fix the file and re-run

**Step 3: Clean up test file**

```bash
git reset HEAD~1
rm telegram_bot/handlers/test_precommit.py
```

**Step 4: Verify CI workflow syntax**

Run: `python -c "import yaml; print('CI workflow valid')" .github/workflows/ci.yml`

**Step 5: Final commit if any changes**

```bash
git add .
git commit -m "chore: final pre-commit setup verification"
```

---

### Task 11: Create Summary and Usage Guide

**Files:**
- Create: `docs/PRECOMMIT_USAGE.md`

**Step 1: Create usage guide**

```markdown
# Pre-commit Hooks Usage Guide

## Quick Start

```bash
# One-time setup
./scripts/setup-pre-commit.sh

# Verify installation
uv run pre-commit --version
```

## How It Works

Pre-commit hooks run automatically when you execute `git commit`. They:

1. **Check staged files only** - Fast, doesn't scan entire codebase
2. **Auto-fix issues** - Black formats code, isort organizes imports
3. **Block bad commits** - Prevents committing secrets or broken code

## Common Scenarios

### Scenario 1: Normal Commit (hooks pass)

```bash
git add .
git commit -m "feat: add new feature"
# ✅ Hooks run, commit succeeds
```

### Scenario 2: Auto-fix Required

```bash
git add .
git commit -m "feat: add new feature"
# ⚠️ Black reformats files
# Stage the reformatted files:
git add .
git commit -m "feat: add new feature"
# ✅ Commit succeeds
```

### Scenario 3: Emergency Bypass

```bash
# Only use for WIP commits, not for production code
git commit --no-verify -m "WIP: work in progress"
```

## Manual Commands

```bash
# Run all hooks on all files (good for PRs)
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black --files main.py

# Update hook versions
uv run pre-commit autoupdate

# Uninstall hooks
uv run pre-commit uninstall
```

## Troubleshooting

### "Hook black failed with exit code 1"

This means black reformatted files. Stage the changes and commit again:

```bash
git add .
git commit -m "your message"
```

### "detect-secrets found potential secrets"

Review the file for actual secrets. If it's a false positive:

```bash
# Update baseline (only if you're sure it's not a real secret)
uv run detect-secrets scan --baseline .secrets.baseline
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

### "isort changed my imports"

isort organizes imports alphabetically. Stage and commit:

```bash
git add .
git commit -m "your message"
```

## CI/CD Integration

Pre-commit hooks also run in GitHub Actions on every push/PR. If hooks pass locally, they'll pass in CI.

## Best Practices

1. ✅ **Install hooks locally** - Catch issues before CI
2. ✅ **Commit often** - Smaller commits = faster hook runs
3. ✅ **Don't bypass hooks** - Only use `--no-verify` for WIP
4. ✅ **Update regularly** - `pre-commit autoupdate` monthly

## Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
```

**Step 2: Commit**

```bash
git add docs/PRECOMMIT_USAGE.md
git commit -m "docs: add comprehensive pre-commit usage guide"
```

---

## Completion Checklist

- [ ] `.pre-commit-config.yaml` created with 7+ hooks
- [ ] `pre-commit` added to dev dependencies
- [ ] isort configuration added to `pyproject.toml`
- [ ] `.gitignore` updated with pre-commit cache
- [ ] CI workflow enhanced with pre-commit job
- [ ] Secrets baseline created
- [ ] Pre-commit hooks installed and tested locally
- [ ] Setup script created and tested
- [ ] Documentation updated (AGENTS.md, README.md)
- [ ] Usage guide created (docs/PRECOMMIT_USAGE.md)
- [ ] All tests passing
- [ ] CI pipeline green

---

## Next Steps After Implementation

1. **Push to GitHub** - Test CI workflow
2. **Team onboarding** - Share setup instructions
3. **Monitor CI** - Ensure pre-commit job passes
4. **Regular updates** - Run `pre-commit autoupdate` monthly
