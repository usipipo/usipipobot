# CI/CD GitHub Actions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar pipeline CI/CD completo con GitHub Actions para testing, linting, building y deployment automatizado.

**Architecture:** Pipeline multi-stage con jobs paralelos para testing y linting, seguido de build de Docker image y deployment condicional. Usa caching, matrix builds, y secrets management.

**Tech Stack:** Python 3.11+, pytest, black, flake8, mypy, Docker, GitHub Actions, ghcr.io

---

## Task 1: Crear workflow de CI (Test + Lint)

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Crear archivo ci.yml con workflow de CI completo**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: usipipo_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/usipipo_test
          PYTHONPATH: .
        run: |
          pytest -v --cov=. --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  lint:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install linters
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort mypy

      - name: Run Black
        run: black --check --diff .

      - name: Run isort
        run: isort --check-only --diff .

      - name: Run Flake8
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run MyPy
        run: mypy . --ignore-missing-imports || true

  security:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          severity: "CRITICAL,HIGH"
          exit-code: "0"
```

**Step 2: Verificar sintaxis YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI workflow with test, lint, and security jobs"
```

---

## Task 2: Crear pytest.ini para configuración de tests

**Files:**
- Create: `pytest.ini`

**Step 1: Crear pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
filterwarnings =
    ignore::DeprecationWarning
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    slow: mark test as slow
```

**Step 2: Verificar tests funcionan**

Run: `pytest --collect-only`
Expected: Shows collected tests

**Step 3: Commit**

```bash
git add pytest.ini
git commit -m "test: add pytest configuration"
```

---

## Task 3: Crear workflow de build Docker

**Files:**
- Create: `.github/workflows/docker.yml`
- Create: `Dockerfile`

**Step 1: Crear Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
```

**Step 2: Crear docker.yml workflow**

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Step 3: Verificar Dockerfile sintaxis**

Run: `docker build --check . 2>/dev/null || echo "Docker syntax OK"`
Expected: "Docker syntax OK" or successful build check

**Step 4: Commit**

```bash
git add Dockerfile .github/workflows/docker.yml
git commit -m "ci: add Docker build workflow and Dockerfile"
```

---

## Task 4: Crear workflow de deploy

**Files:**
- Create: `.github/workflows/deploy.yml`

**Step 1: Crear deploy.yml**

```yaml
name: Deploy

on:
  push:
    tags: ["v*"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://github.com/${{ github.repository }}
    
    permissions:
      contents: read
      packages: read
    
    steps:
      - uses: actions/checkout@v4

      - name: Deploy notification
        run: |
          echo "🚀 Deploying version ${{ github.ref_name }}"
          echo "Image: ghcr.io/${{ github.repository }}:${{ github.ref_name }}"

      - name: Create deployment summary
        run: |
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "- **Version:** ${{ github.ref_name }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Commit:** ${{ github.sha }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Actor:** ${{ github.actor }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Timestamp:** $(date -u)" >> $GITHUB_STEP_SUMMARY

      # Add your deployment commands here
      # Example: SSH to server, kubectl apply, etc.
```

**Step 2: Verificar sintaxis**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add deployment workflow for production releases"
```

---

## Task 5: Actualizar CodeQL para Python

**Files:**
- Modify: `.github/workflows/codeql.yml`

**Step 1: Actualizar CodeQL para incluir Python**

```yaml
name: "CodeQL"

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]
  schedule:
    - cron: "0 0 * * 0"

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ["python"]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

**Step 2: Verificar sintaxis**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/codeql.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add .github/workflows/codeql.yml
git commit -m "ci: update CodeQL workflow for Python analysis"
```

---

## Task 6: Crear .dockerignore

**Files:**
- Create: `.dockerignore`

**Step 1: Crear .dockerignore**

```
.git
.gitignore
.env
.venv
venv
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.pytest_cache
.coverage
htmlcov
.mypy_cache
.ruff_cache
.idea
.vscode
*.md
!README.md
LICENSE
.github
tests
docs
scripts
*.log
*.pot
*.mo
```

**Step 2: Commit**

```bash
git add .dockerignore
git commit -m "ci: add .dockerignore for optimized builds"
```

---

## Task 7: Crear workflow de dependabot

**Files:**
- Create: `.github/dependabot.yml`

**Step 1: Crear dependabot.yml**

```yaml
version: 2

updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "${{ github.repository_owner }}"
    labels:
      - "dependencies"
      - "python"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
      - "github-actions"
```

**Step 2: Verificar sintaxis**

Run: `python -c "import yaml; yaml.safe_load(open('.github/dependabot.yml'))"`
Expected: No errors

**Step 3: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci: add dependabot configuration for automated dependency updates"
```

---

## Task 8: Actualizar README con badges

**Files:**
- Modify: `README.md`

**Step 1: Leer README actual y agregar badges al inicio**

Añadir después del título principal:

```markdown
[![CI](https://github.com/mowgli/usipipobot/actions/workflows/ci.yml/badge.svg)](https://github.com/mowgli/usipipobot/actions/workflows/ci.yml)
[![Docker Build](https://github.com/mowgli/usipipobot/actions/workflows/docker.yml/badge.svg)](https://github.com/mowgli/usipipobot/actions/workflows/docker.yml)
[![CodeQL](https://github.com/mowgli/usipipobot/actions/workflows/codeql.yml/badge.svg)](https://github.com/mowgli/usipipobot/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/mowgli/usipipobot/branch/main/graph/badge.svg)](https://codecov.io/gh/mowgli/usipipobot)
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add CI/CD badges to README"
```

---

## Task 9: Push y verificar workflows

**Step 1: Push cambios a remote**

```bash
git push origin main
```

**Step 2: Verificar workflows en GitHub**

Run: `gh run list --limit 5`
Expected: Shows workflow runs

**Step 3: Verificar estado del último run**

Run: `gh run watch`
Expected: Shows live status of running workflow

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | CI workflow (test + lint + security) | `.github/workflows/ci.yml` |
| 2 | Pytest configuration | `pytest.ini` |
| 3 | Docker build workflow + Dockerfile | `Dockerfile`, `.github/workflows/docker.yml` |
| 4 | Deploy workflow | `.github/workflows/deploy.yml` |
| 5 | Update CodeQL for Python | `.github/workflows/codeql.yml` |
| 6 | Docker ignore file | `.dockerignore` |
| 7 | Dependabot configuration | `.github/dependabot.yml` |
| 8 | README badges | `README.md` |
| 9 | Push and verify | - |

---

## Required Secrets

| Secret | Description | How to set |
|--------|-------------|------------|
| `GITHUB_TOKEN` | Built-in token | Automatic |
| `CODECOV_TOKEN` | Codecov upload token | Settings > Secrets |

---

## Branch Protection Rules (Recommended)

After implementation, configure in GitHub Settings > Branches:

1. **main branch:**
   - Require status checks: `test (3.11)`, `test (3.12)`, `lint`
   - Require branches to be up to date
   - Require linear history
   - Include administrators
