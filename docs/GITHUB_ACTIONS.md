# GitHub Actions Workflows - uSipipo VPN Manager

This document provides an overview of all GitHub Actions workflows configured for the uSipipo VPN Manager project.

## 📋 Workflow Overview

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI** | `ci.yml` | Push/PR to main | Backend testing, linting, security scanning |
| **Docker** | `docker.yml` | Push/PR to main | Docker image build and push to GHCR |
| **CodeQL** | `codeql.yml` | Push/PR/Schedule | Security vulnerability analysis |
| **Release** | `release.yml` | Tag push | Automatic changelog and release creation |
| **Manual Deploy** | `manual-deploy.yml` | Manual trigger | Manual deployment to environments |
| **Performance** | `performance.yml` | Push/PR/Manual | Performance benchmarks and load tests |
| **Deploy** | `deploy.yml` | Tag push | Production deployment notification |

---

## 🔧 Workflow Details

### 1. CI (Continuous Integration)

**File:** `.github/workflows/ci.yml`

**Triggers:**
- Push to `main`, `develop` (filtered by paths)
- Pull requests to `main`

**Jobs:**
| Job | Description |
|-----|-------------|
| `pre-commit` | Runs pre-commit hooks (black, isort, flake8) |
| `test` | Runs pytest with coverage (Python 3.11, 3.12) |
| `lint` | Code formatting and type checking |
| `security` | Trivy filesystem vulnerability scan |

**Services:**
- PostgreSQL 15 for integration tests

**Artifacts:**
- Coverage report uploaded to Codecov

---

### 3. Docker Build

**File:** `.github/workflows/docker.yml`

**Triggers:**
- Push to `main`
- Tags (v*)
- Pull requests to `main`

**Jobs:**
| Job | Description |
|-----|-------------|
| `build` | Build and push Docker image to GHCR |

**Image Tags:**
- `main` - Latest from main branch
- `v1.0.0` - Semantic version tags
- `sha-{short}` - Commit SHA

**Registry:** `ghcr.io/usipipo/usipipobot`

---

### 4. CodeQL Security Analysis

**File:** `.github/workflows/codeql.yml`

**Triggers:**
- Push to `main`
- Pull requests to `main`
- Weekly schedule (Sundays at 00:00 UTC)

**Jobs:**
| Job | Description |
|-----|-------------|
| `analyze` | CodeQL security analysis for Python |

**Languages:**
- Python

---

### 5. Release Automation

**File:** `.github/workflows/release.yml`

**Triggers:**
- Tag push (v*)

**Jobs:**
| Job | Description |
|-----|-------------|
| `generate-changelog` | Generate changelog from commits/PRs |
| `create-release` | Create GitHub release with changelog |
| `notify-telegram` | Send release notification to Telegram (optional) |

**Changelog Categories:**
- 🚀 Features
- 🐛 Bug Fixes
- 📝 Documentation
- 🔒 Security
- 🧪 Tests
- ⚙️ CI/CD
- 📦 Dependencies

**Variables Required (for Telegram notification):**
| Variable | Description |
|----------|-------------|
| `TELEGRAM_CHAT_ID` | Telegram chat ID for notifications |

**Secrets Required (for Telegram notification):**
| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Bot token for notifications |

---

### 6. Manual Deployment

**File:** `.github/workflows/manual-deploy.yml`

**Triggers:**
- Manual workflow dispatch

**Inputs:**
| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | choice | `staging` | Target environment (staging/production) |
| `version` | string | `main` | Version to deploy (e.g., v1.0.0) |
| `run_tests` | boolean | `true` | Run tests before deployment |

**Jobs:**
| Job | Description |
|-----|-------------|
| `pre-deployment-tests` | Run test suite before deployment |
| `deploy` | Deploy to target environment |
| `notify-deployment` | Send deployment notification |

**Deployment Methods (configure one):**
1. **SSH** - Deploy via SSH to remote server
2. **Kubernetes** - Deploy to K8s cluster
3. **Docker Swarm** - Deploy to Swarm cluster

**Environments Required:**
- `staging`
- `production`

**Secrets Required (by deployment method):**

**SSH:**
| Secret | Description |
|--------|-------------|
| `DEPLOY_HOST` | Server hostname/IP |
| `DEPLOY_USER` | SSH username |
| `DEPLOY_KEY` | SSH private key |

**Kubernetes:**
| Secret | Description |
|--------|-------------|
| `K8S_ENDPOINT` | Kubernetes API endpoint |
| `K8S_TOKEN` | Kubernetes service account token |

---

### 7. Performance Testing

**File:** `.github/workflows/performance.yml`

**Triggers:**
- Push to `main`, `develop` (filtered by paths)
- Pull requests to `main`
- Manual workflow dispatch

**Inputs (manual):**
| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `test_type` | choice | `api` | Test type (api/database/full) |

**Jobs:**
| Job | Description |
|-----|-------------|
| `api-performance` | API benchmark tests with pytest-benchmark |
| `database-performance` | Database query performance tests |
| `load-test` | Load testing with Locust (full test only) |
| `performance-summary` | Aggregate performance results |

**Dependencies:**
- pytest-benchmark
- locust

**Artifacts:**
- Benchmark results (JSON)
- Load test report (HTML)

---

## 🔐 Secrets Management

### Required Secrets

Configure these secrets in **GitHub Repository Settings → Secrets and variables → Actions**:

| Secret | Scope | Description |
|--------|-------|-------------|
| `GITHUB_TOKEN` | Auto | Automatic GitHub authentication |
| `TELEGRAM_BOT_TOKEN` | Optional | Bot token for release notifications |
| `DEPLOY_HOST` | Optional | Deployment server hostname |
| `DEPLOY_USER` | Optional | Deployment SSH username |
| `DEPLOY_KEY` | Optional | Deployment SSH private key |

### Required Variables

| Variable | Scope | Description |
|----------|-------|-------------|
| `TELEGRAM_CHAT_ID` | Optional | Telegram chat ID for notifications |
| `APP_URL` | Environment | Application URL for deployment |

---

## 🌍 Environments

Configure environments in **GitHub Repository Settings → Environments**:

### `staging`
- **Purpose:** Pre-production testing
- **URL:** `https://staging.usipipo.com` (example)
- **Required reviewers:** Optional
- **Secrets:** Staging-specific secrets

### `production`
- **Purpose:** Production deployment
- **URL:** `https://usipipo.com` (example)
- **Required reviewers:** Recommended
- **Wait timer:** Optional (e.g., 5 minutes)
- **Deployment branches:** `main` only

### `release`
- **Purpose:** Release automation
- **URL:** GitHub Releases page
- **Required reviewers:** Optional

---

## 📊 Path Filtering

Workflows use path filtering to avoid unnecessary runs:

### Backend Paths
```
domain/**
application/**
infrastructure/**
telegram_bot/**
miniapp/**
utils/**
config.py
main.py
tests/**
requirements*.txt
pyproject.toml
uv.lock
```

### Docker Paths
```
Dockerfile
.dockerignore
```

---

## 🚀 Usage Examples

### Trigger Manual Deployment

```bash
# Via GitHub UI:
# 1. Go to Actions → Manual Deployment
# 2. Click "Run workflow"
# 3. Select environment and version
# 4. Click "Run workflow"

# Via GitHub CLI:
gh workflow run manual-deploy.yml \
  -f environment=production \
  -f version=v1.0.0 \
  -f run_tests=true
```

### Trigger Performance Tests

```bash
# Full performance suite
gh workflow run performance.yml \
  -f test_type=full

# API tests only
gh workflow run performance.yml \
  -f test_type=api
```

---

## 📈 Monitoring Workflows

### View Workflow Runs

```bash
# List recent runs
gh run list --workflow ci.yml

# View specific run
gh run view <run-id>

# Watch a running workflow
gh run watch <run-id>

# Download artifacts
gh run download <run-id> --name benchmark-results
```

### Workflow Status Badges

Add these to your README.md:

```markdown
[![CI](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/ci.yml)
[![Docker](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/docker.yml)
[![CodeQL](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml/badge.svg)](https://github.com/usipipo/usipipobot/actions/workflows/codeql.yml)
```

---

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Workflow not triggering | Check path filters and branch filters |
| Secrets not available | Verify secrets are set at correct level (repo/org/env) |
| PostgreSQL connection fails | Check service health check configuration |
| Permission denied errors | Verify workflow permissions in workflow file |

### Debug Mode

Enable debug logging by setting these secrets:

| Secret | Value |
|--------|-------|
| `ACTIONS_RUNNER_DEBUG` | `true` |
| `ACTIONS_STEP_DEBUG` | `true` |
| `RUNNER_DEBUG` | `1` |

### Re-run Failed Jobs

```bash
# Re-run failed jobs
gh run rerun <run-id> --failed

# Re-run specific job
gh run rerun <run-id> --job <job-id>
```

---

## 📝 Best Practices

1. **Keep workflows modular** - Separate concerns into different workflow files
2. **Use path filtering** - Avoid unnecessary workflow runs
3. **Cache dependencies** - Use `actions/cache` for faster builds
4. **Set appropriate timeouts** - Prevent hung workflows
5. **Use environments** - Separate staging/production deployments
6. **Require reviewers** - For production deployments
7. **Monitor costs** - Be aware of GitHub Actions minutes usage
8. **Clean up artifacts** - Set retention policies for artifacts

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Awesome GitHub Actions](https://github.com/sdras/awesome-actions)

---

## 🔄 Recent Updates

| Date | Change |
|------|--------|
| 2026-03-15 | Added release automation workflow |
| 2026-03-15 | Added manual deployment workflow |
| 2026-03-15 | Added performance testing workflow |
| 2026-03-15 | Updated documentation |

---

*Last updated: March 15, 2026*
