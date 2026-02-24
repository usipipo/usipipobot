# Fix Mini App Authorization Bug - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the "No autorizado: initData requerido" error when opening the Telegram Mini App for the first time.

**Architecture:** Create a public entry endpoint that handles initial authentication by redirecting with proper query parameters after obtaining initData from Telegram WebApp SDK.

**Tech Stack:** Python, FastAPI, JavaScript, Telegram WebApp SDK

---

## Root Cause Analysis

**Problem:** When Telegram opens the mini app with the base URL `/miniapp/`, it does NOT automatically include `tgWebAppData` in the URL query parameters. The backend requires immediate authentication (line 72-73 in `router.py`), but the frontend JavaScript that obtains `initData` from the Telegram WebApp SDK object only executes AFTER the page loads.

**Evidence:**
- Error: `{"detail":"No autorizado: initData requerido"}`
- Log: `INFO: 165.140.241.96:0 - "GET /miniapp/ HTTP/1.1" 401 Unauthorized`
- Backend expects `initData` in: query params, headers, or form data (router.py:60-69)
- Frontend obtains `initData` from `tg.initData` object (app.js:42-44)
- Mismatch: Backend auth happens before frontend JavaScript runs

**Solution Pattern:** Telegram Mini Apps require a public entry page that:
1. Loads without backend authentication
2. Uses client-side JavaScript to get `initData` from Telegram SDK
3. Redirects to authenticated pages with proper query parameters

---

## Implementation Tasks

### Task 1: Create Public Entry Endpoint

**Files:**
- Modify: `miniapp/router.py:82-128`
- Create: `miniapp/templates/entry.html`

**Step 1: Add public entry endpoint**

Add a new public endpoint before the dashboard endpoint:

```python
@router.get("/entry", response_class=HTMLResponse)
async def miniapp_entry(request: Request):
    """
    Página de entrada pública para la Mini App.
    
    Esta página se carga sin autenticación para obtener initData
    del SDK de Telegram y redirigir al dashboard autenticado.
    """
    return templates.TemplateResponse(
        "entry.html",
        {
            "request": request,
            "bot_username": settings.BOT_USERNAME,
        },
    )
```

**Step 2: Create entry.html template**

Create `miniapp/templates/entry.html`:

```html
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>uSipipo VPN - Cargando...</title>
    
    <script src="https://telegram.org/js/telegram-web-app.js?59"></script>
    
    <style>
        :root {
            --bg-void: #0a0a0f;
            --neon-cyan: #00f0ff;
            --text-primary: #e0e0e0;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: var(--bg-void);
            color: var(--text-primary);
            font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }
        
        .loader {
            text-align: center;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(0, 240, 255, 0.1);
            border-top-color: var(--neon-cyan);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .title {
            font-size: 24px;
            font-weight: 700;
            color: var(--neon-cyan);
            text-shadow: 0 0 20px rgba(0, 240, 255, 0.5);
            margin-bottom: 8px;
        }
        
        .message {
            font-size: 14px;
            color: var(--text-primary);
            opacity: 0.7;
        }
        
        .error {
            background: rgba(255, 0, 170, 0.1);
            border: 1px solid #ff00aa;
            border-radius: 8px;
            padding: 16px;
            margin-top: 20px;
            max-width: 300px;
            display: none;
        }
        
        .error.show {
            display: block;
        }
        
        .error-title {
            color: #ff00aa;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .error-message {
            font-size: 12px;
            color: var(--text-primary);
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <div class="title">uSipipo VPN</div>
        <div class="message">Inicializando Mini App...</div>
        
        <div class="error" id="errorBox">
            <div class="error-title">⚠️ Error de Autenticación</div>
            <div class="error-message" id="errorMessage"></div>
        </div>
    </div>
    
    <script>
        (function() {
            'use strict';
            
            const tg = window.Telegram?.WebApp;
            const errorBox = document.getElementById('errorBox');
            const errorMessage = document.getElementById('errorMessage');
            const messageDiv = document.querySelector('.message');
            
            function showError(msg) {
                errorBox.classList.add('show');
                errorMessage.textContent = msg;
                document.querySelector('.spinner').style.display = 'none';
            }
            
            if (!tg) {
                showError('Esta aplicación solo funciona dentro de Telegram. Por favor, abre la Mini App desde el bot de Telegram.');
                return;
            }
            
            tg.ready();
            tg.expand();
            tg.setHeaderColor('#0a0a0f');
            tg.setBackgroundColor('#0a0a0f');
            
            messageDiv.textContent = 'Obteniendo datos de autenticación...';
            
            setTimeout(function() {
                const initData = tg.initData;
                
                if (!initData) {
                    showError('No se pudieron obtener los datos de autenticación. Por favor, cierra y vuelve a abrir la Mini App desde Telegram.');
                    return;
                }
                
                messageDiv.textContent = 'Redirigiendo al dashboard...';
                
                const dashboardUrl = new URL('/miniapp/', window.location.origin);
                dashboardUrl.searchParams.set('tgWebAppData', initData);
                
                window.location.replace(dashboardUrl.toString());
            }, 500);
        })();
    </script>
</body>
</html>
```

**Step 3: Test the entry endpoint**

Run: `pytest tests/ -v -k miniapp`
Expected: All tests pass (or create new test if needed)

**Step 4: Commit**

```bash
git add miniapp/router.py miniapp/templates/entry.html
git commit -m "feat: add public entry endpoint for Mini App authentication"
```

---

### Task 2: Update Mini App Configuration

**Files:**
- Modify: `infrastructure/api/server.py:81`

**Step 1: Update Mini App menu button configuration**

Verify that the menu button or inline keyboard points to `/miniapp/entry` instead of `/miniapp/`.

**Step 2: Search for Mini App URL references**

Run: `grep -r "miniapp/" --include="*.py" --include="*.md"`

Identify all places where the Mini App URL is configured.

**Step 3: Update Bot configuration**

Update the bot's menu button or start command to point to the new entry endpoint.

**Step 4: Commit**

```bash
git add infrastructure/api/server.py telegram_bot/
git commit -m "feat: update Mini App URL to use entry endpoint"
```

---

### Task 3: Add Tests for Entry Endpoint

**Files:**
- Create: `tests/miniapp/test_entry_endpoint.py`

**Step 1: Write failing tests**

```python
import pytest
from httpx import AsyncClient
from infrastructure.api.server import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_entry_endpoint_returns_200(client):
    """Test that entry endpoint is accessible without authentication."""
    response = await client.get("/miniapp/entry")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_entry_endpoint_contains_telegram_sdk(client):
    """Test that entry page includes Telegram WebApp SDK."""
    response = await client.get("/miniapp/entry")
    assert b"telegram-web-app.js" in response.content

@pytest.mark.asyncio
async def test_entry_endpoint_contains_redirect_logic(client):
    """Test that entry page has JavaScript redirect logic."""
    response = await client.get("/miniapp/entry")
    assert b"tgWebAppData" in response.content
    assert b"/miniapp/" in response.content

@pytest.mark.asyncio
async def test_dashboard_requires_authentication(client):
    """Test that dashboard still requires authentication."""
    response = await client.get("/miniapp/")
    assert response.status_code == 401
    assert "No autorizado" in response.text
```

**Step 2: Run tests**

Run: `pytest tests/miniapp/test_entry_endpoint.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/miniapp/test_entry_endpoint.py
git commit -m "test: add tests for Mini App entry endpoint"
```

---

### Task 4: Update Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/miniapp.md` (if exists)

**Step 1: Add Mini App authentication flow to documentation**

Document the authentication flow:
1. User opens Mini App → `/miniapp/entry` (public)
2. Entry page loads Telegram SDK
3. JavaScript gets `initData` from SDK
4. Redirects to `/miniapp/?tgWebAppData=...` (authenticated)

**Step 2: Commit**

```bash
git add README.md docs/
git commit -m "docs: document Mini App authentication flow"
```

---

### Task 5: Integration Testing

**Step 1: Test in development**

Run the bot locally and test the Mini App flow:
1. Open the Mini App from Telegram
2. Verify the entry page loads
3. Verify redirect to dashboard with authentication

**Step 2: Check logs**

Verify no 401 errors in logs when opening the Mini App.

**Step 3: Test error scenarios**

Test what happens when:
- Opening outside Telegram (should show error)
- Invalid initData (should redirect with error)

---

## Verification Checklist

- [ ] Entry endpoint accessible without authentication
- [ ] Entry page loads Telegram WebApp SDK
- [ ] JavaScript obtains initData and redirects
- [ ] Dashboard still requires authentication
- [ ] All existing tests pass
- [ ] New tests for entry endpoint pass
- [ ] No 401 errors when opening Mini App from Telegram
- [ ] Documentation updated

---

## Expected Outcome

After implementing this fix:
- Users can open the Mini App from Telegram without seeing 401 errors
- The authentication flow happens automatically via the entry page
- All existing functionality remains intact
- The Mini App loads successfully for authenticated users
