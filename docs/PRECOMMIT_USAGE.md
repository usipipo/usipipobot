# Pre-commit Hooks - Usage Guide

## Quick Start

```bash
# One-time setup
./scripts/setup-pre-commit.sh

# Verify installation
uv run pre-commit --version
```

---

## What Are Pre-commit Hooks?

Pre-commit hooks are automated checks that run **before every git commit**. They ensure code quality and consistency across the project by:

- ✅ **Auto-fixing** formatting issues (Black, isort)
- ✅ **Cleaning** whitespace and file endings
- ✅ **Validating** YAML/JSON syntax
- ✅ **Detecting** secrets and private keys
- ✅ **Linting** Python code for critical issues

---

## How It Works

```
Developer makes changes → git add → git commit → Pre-commit hooks run
                                                              ↓
                        ┌─────────────────────────────────────┴─────────────────────────────────────┐
                        │                                                                           │
                  ✅ All hooks pass                                                           ❌ Hook fails
                        │                                                                           │
                        ↓                                                                           ↓
                Commit succeeds                                                              Commit blocked
                                                                                           (auto-fix or error)
                                                                                                   │
                                                                                                   ↓
                                                                                           Fix issues → git add → git commit again
```

---

## Hooks Configured

| # | Hook | Purpose | Auto-fix | Speed |
|---|------|---------|----------|-------|
| 1 | `trailing-whitespace` | Remove trailing spaces | ✅ | ⚡ |
| 2 | `end-of-file-fixer` | Ensure newline at EOF | ✅ | ⚡ |
| 3 | `check-yaml` | Validate YAML syntax | ❌ | ⚡ |
| 4 | `check-json` | Validate JSON syntax | ❌ | ⚡ |
| 5 | `detect-private-key` | Detect leaked secrets | ❌ | ⚡ |
| 6 | `check-merge-conflict` | Check for merge markers | ❌ | ⚡ |
| 7 | `check-symlinks` | Check for broken symlinks | ❌ | ⚡ |
| 8 | `isort` | Sort imports alphabetically | ✅ | ⚡ |
| 9 | `black` | Format Python code | ✅ | ⚡⚡ |
| 10 | `detect-secrets` | Advanced secret detection | ❌ | ⚡⚡ |
| 11 | `flake8` | Python linting (critical only) | ❌ | ⚡⚡ |

**Total run time:** 2-5 seconds for typical commits

---

## Common Scenarios

### Scenario 1: Normal Commit (Hooks Pass)

```bash
git add .
git commit -m "feat: add new feature"
# ✅ Hooks run automatically
# ✅ Commit succeeds
```

---

### Scenario 2: Auto-fix Required (Black/isort reformats)

```bash
git add .
git commit -m "feat: add new feature"
# ⚠️ Black reformats files
# ⚠️ isort reorganizes imports
# Output: "files were modified by this hook"

# Stage the reformatted files:
git add .
git commit -m "feat: add new feature"
# ✅ Commit succeeds
```

**This is normal!** Pre-commit auto-fixed your code.

---

### Scenario 3: Hook Fails (Syntax Error)

```bash
git add .
git commit -m "feat: add new feature"
# ❌ check-yaml failed
# Error: Invalid YAML syntax in config.yaml

# Fix the error:
nano config.yaml  # Fix YAML syntax
git add config.yaml
git commit -m "feat: add new feature"
# ✅ Now passes
```

---

### Scenario 4: Secret Detected

```bash
git add .
git commit -m "feat: add config"
# ❌ detect-secrets found potential secrets
# File: .env, Line 5: Possible secret

# Review the file:
nano .env

# If it's a real secret: REMOVE IT
# If it's a false positive: Update baseline
uv run detect-secrets scan --baseline .secrets.baseline
git add .secrets.baseline
git commit -m "chore: update secrets baseline"
```

---

### Scenario 5: Emergency Bypass (Use Sparingly!)

```bash
# Only for WIP commits, NOT for production code
git commit --no-verify -m "WIP: work in progress"

# ⚠️ Warning: Hooks are skipped!
# Fix and re-commit properly before pushing
```

---

## Manual Commands

```bash
# Run all hooks on all files (good for PRs)
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black --files main.py
uv run pre-commit run isort --files src/*.py

# Update hook versions (monthly)
uv run pre-commit autoupdate

# Uninstall hooks
uv run pre-commit uninstall

# See all available commands
uv run pre-commit --help
```

---

## Troubleshooting

### "Hook black failed with exit code 1"

**Cause:** Black reformatted your files.

**Solution:**
```bash
git add .  # Stage reformatted files
git commit -m "your message"  # Commit again
```

---

### "isort changed my imports"

**Cause:** isort organizes imports alphabetically.

**Solution:**
```bash
git add .  # Stage reformatted files
git commit -m "your message"  # Commit again
```

**To prevent:** Follow import order in AGENTS.md:
1. Standard library
2. Third-party
3. Local imports (domain → application → infrastructure)

---

### "detect-secrets found potential secrets"

**Cause:** Possible secret detected in code.

**Solution:**

1. **If it's a real secret:** REMOVE IT IMMEDIATELY
   ```bash
   # Remove secret from file
   nano file.py
   git add file.py
   git commit -m "fix: remove secret"
   ```

2. **If it's a false positive:** Update baseline
   ```bash
   uv run detect-secrets scan --baseline .secrets.baseline
   git add .secrets.baseline
   git commit -m "chore: update secrets baseline"
   ```

---

### "flake8: B008 Do not perform function calls in argument defaults"

**Cause:** Function call in default argument (potential bug).

**Example:**
```python
# ❌ Bad
def get_user(user_id: int, session=get_session()):
    pass

# ✅ Good
def get_user(user_id: int, session=None):
    if session is None:
        session = get_session()
```

**Solution:** Refactor to avoid function calls in defaults.

---

### "F821 undefined name 'e'"

**Cause:** Using undefined variable (typo or missing import).

**Solution:**
```python
# ❌ Bad
try:
    risky_operation()
except Exception as ex:
    logger.error(f"Error: {e}")  # 'e' undefined!

# ✅ Good
try:
    risky_operation()
except Exception as e:
    logger.error(f"Error: {e}")
```

---

## CI/CD Integration

Pre-commit hooks also run in **GitHub Actions** on every push/PR:

```yaml
# .github/workflows/ci.yml
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pre-commit hooks
        run: pre-commit run --all-files
```

**If hooks pass locally, they'll pass in CI!**

---

## Best Practices

1. ✅ **Install hooks locally** - Catch issues before CI
   ```bash
   ./scripts/setup-pre-commit.sh
   ```

2. ✅ **Commit often** - Smaller commits = faster hook runs

3. ✅ **Don't bypass hooks** - Only use `--no-verify` for WIP

4. ✅ **Update regularly** - Run `pre-commit autoupdate` monthly

5. ✅ **Fix issues immediately** - Don't accumulate technical debt

---

## Configuration Files

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Hook definitions and versions |
| `.secrets.baseline` | Known secrets baseline (auto-generated) |
| `scripts/setup-pre-commit.sh` | Developer setup script |
| `pyproject.toml` | Black and isort configuration |
| `.gitignore` | Ignores `.pre-commit/` cache |

---

## Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
- [Flake8 Documentation](https://flake8.pycqa.org/)

---

## Questions?

- Check `AGENTS.md` for development guidelines
- Review `.pre-commit-config.yaml` for hook configuration
- Run `uv run pre-commit --help` for command reference
