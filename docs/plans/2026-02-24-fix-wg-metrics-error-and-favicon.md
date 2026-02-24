# Fix WireGuard Metrics Error and Favicon 404

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix two bugs: (1) Empty error message when getting WireGuard metrics during sync job, (2) Missing favicon causing 404 errors in Mini App web.

**Architecture:** 
1. Add proper error handling and logging in `WireGuardClient.get_usage()` to capture actual error messages
2. Add caching with TTL for WireGuard metrics to prevent race conditions
3. Add favicon.ico to Mini App static assets

**Tech Stack:** Python asyncio, functools.lru_cache (or custom async cache), FastAPI static files

---

## Investigation Summary

### Bug 1: WireGuard Metrics Error (CRITICAL)
- **Location:** `infrastructure/api_clients/client_wireguard.py:273`
- **Symptom:** Error log shows empty message: "Error obteniendo métricas WG: "
- **Frequency:** Exactly 2 errors per sync cycle (every 30 minutes)
- **Impact:** Metrics are lost for those keys, but sync continues without errors
- **Root Cause:** Exception is caught but `{e}` in f-string may be empty, OR there's a race condition when multiple async tasks call `get_usage()` simultaneously

### Bug 2: Favicon 404 (MINOR)
- **Location:** Missing file in Mini App web server
- **Symptom:** HTTP 404 for `/favicon.ico`
- **Impact:** Browser shows missing icon, no functional impact

---

## Task 1: Improve Error Handling in WireGuardClient

**Files:**
- Modify: `infrastructure/api_clients/client_wireguard.py:254-275`
- Test: `tests/infrastructure/api_clients/test_wireguard_client.py`

**Step 1: Write the failing test for error message capture**

Create test to verify error message is properly captured and logged:

```python
# tests/infrastructure/api_clients/test_wireguard_client.py

@pytest.mark.asyncio
async def test_get_usage_captures_error_message():
    """Test that get_usage logs actual error messages."""
    client = WireGuardClient()
    client.interface = "nonexistent"
    
    with patch.object(client, '_run_cmd', side_effect=Exception("Detailed error message")):
        with patch('infrastructure.api_clients.client_wireguard.logger') as mock_logger:
            result = await client.get_usage()
            
            assert result == []
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Detailed error message" in call_args
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/infrastructure/api_clients/test_wireguard_client.py::test_get_usage_captures_error_message -v`
Expected: FAIL (error message not in log)

**Step 3: Improve error handling in get_usage()**

```python
# infrastructure/api_clients/client_wireguard.py

async def get_usage(self) -> List[Dict]:
    try:
        output = await self._run_cmd(f"wg show {self.interface} dump")
        lines = output.split("\n")[1:]

        usage = []
        for line in lines:
            cols = line.split("\t")
            if len(cols) >= 7:
                usage.append(
                    {
                        "public_key": cols[0],
                        "rx": int(cols[5]),
                        "tx": int(cols[6]),
                        "total": int(cols[5]) + int(cols[6]),
                    }
                )
        return usage
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e) or "Unknown error (empty exception)"
        logger.error(f"Error obteniendo métricas WG: {error_msg}", exc_info=True)
        return []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/infrastructure/api_clients/test_wireguard_client.py::test_get_usage_captures_error_message -v`
Expected: PASS

**Step 5: Commit**

```bash
git add infrastructure/api_clients/client_wireguard.py tests/infrastructure/api_clients/test_wireguard_client.py
git commit -m "fix: improve error handling in WireGuard get_usage()"
```

---

## Task 2: Add Async Caching for WireGuard Metrics

**Files:**
- Modify: `infrastructure/api_clients/client_wireguard.py`
- Test: `tests/infrastructure/api_clients/test_wireguard_client.py`

**Step 1: Write the failing test for caching**

```python
@pytest.mark.asyncio
async def test_get_usage_caches_results():
    """Test that get_usage caches results to prevent race conditions."""
    client = WireGuardClient()
    
    with patch.object(client, '_run_cmd', return_value="private\tkey\tport\t0\npub\tkey\tendpoint\tallowed\t0\t100\t200\toff") as mock_cmd:
        # First call
        result1 = await client.get_usage()
        # Second call within cache TTL
        result2 = await client.get_usage()
        
        # Should only call _run_cmd once due to caching
        assert mock_cmd.call_count == 1
        assert result1 == result2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/infrastructure/api_clients/test_wireguard_client.py::test_get_usage_caches_results -v`
Expected: FAIL (call_count > 1)

**Step 3: Implement async caching with TTL**

```python
# infrastructure/api_clients/client_wireguard.py

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple

class WireGuardClient:
    def __init__(self):
        self.interface = settings.WG_INTERFACE or "wg0"
        self.base_path = Path(settings.WG_PATH or "/etc/wireguard")
        self.conf_path = self.base_path / f"{self.interface}.conf"
        self.clients_dir = self.base_path / "clients"
        self.default_quota = 10 * 1024 * 1024 * 1024
        self._permissions_checked = False
        
        # Cache for get_usage results
        self._usage_cache: Optional[Tuple[List[Dict], datetime]] = None
        self._cache_ttl = timedelta(seconds=10)  # Cache for 10 seconds
        self._cache_lock = asyncio.Lock()
        
        os.makedirs(self.clients_dir, exist_ok=True)

    async def get_usage(self) -> List[Dict]:
        """Get WireGuard usage metrics with caching to prevent race conditions."""
        async with self._cache_lock:
            # Check cache
            if self._usage_cache is not None:
                cached_data, cached_time = self._usage_cache
                if datetime.now() - cached_time < self._cache_ttl:
                    logger.debug("Returning cached WireGuard usage metrics")
                    return cached_data
            
            # Cache miss or expired - fetch fresh data
            try:
                output = await self._run_cmd(f"wg show {self.interface} dump")
                lines = output.split("\n")[1:]

                usage = []
                for line in lines:
                    cols = line.split("\t")
                    if len(cols) >= 7:
                        usage.append(
                            {
                                "public_key": cols[0],
                                "rx": int(cols[5]),
                                "tx": int(cols[6]),
                                "total": int(cols[5]) + int(cols[6]),
                            }
                        )
                
                # Update cache
                self._usage_cache = (usage, datetime.now())
                return usage
            except Exception as e:
                error_msg = str(e) if str(e) else repr(e) or "Unknown error (empty exception)"
                logger.error(f"Error obteniendo métricas WG: {error_msg}", exc_info=True)
                return []
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/infrastructure/api_clients/test_wireguard_client.py::test_get_usage_caches_results -v`
Expected: PASS

**Step 5: Commit**

```bash
git add infrastructure/api_clients/client_wireguard.py tests/infrastructure/api_clients/test_wireguard_client.py
git commit -m "fix: add caching to WireGuard get_usage() to prevent race conditions"
```

---

## Task 3: Add Favicon to Mini App

**Files:**
- Create: `miniapp/static/favicon.ico` (or use SVG)
- Modify: `infrastructure/api/server.py`

**Step 1: Create SVG favicon**

Create file `miniapp/static/favicon.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="45" fill="#4F46E5"/>
  <path d="M30 50 L50 30 L70 50 L50 70 Z" fill="white"/>
  <circle cx="50" cy="50" r="8" fill="#4F46E5"/>
</svg>
```

**Step 2: Add favicon route to server**

```python
# infrastructure/api/server.py

from fastapi.responses import FileResponse

# Add after the health check endpoint:
@app.get("/favicon.ico")
async def favicon():
    favicon_path = Path(__file__).parent.parent.parent / "miniapp" / "static" / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"detail": "Not found"})
```

**Step 3: Test favicon endpoint**

Run: `pytest -v` (all tests should still pass)

**Step 4: Commit**

```bash
git add miniapp/static/favicon.svg infrastructure/api/server.py
git commit -m "fix: add favicon to Mini App web"
```

---

## Task 4: Run Full Test Suite

**Step 1: Run all tests**

Run: `pytest -v --cov=.`

Expected: All tests pass

**Step 2: Verify no regressions**

Check that:
- WireGuard client tests pass
- VPN service tests pass
- Mini App tests pass

**Step 3: Commit if needed**

```bash
git add -A
git commit -m "test: verify all tests pass after fixes"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `CHANGELOG.md` or create release notes

**Step 1: Document fixes**

Add entry to changelog:

```markdown
## [Unreleased]

### Fixed
- WireGuard metrics error now shows detailed error message instead of empty string
- Added caching to `WireGuardClient.get_usage()` to prevent race conditions during sync
- Added favicon to Mini App web to prevent 404 errors
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: update changelog with bug fixes"
```

---

## Verification Checklist

After implementing all tasks:

- [ ] Error messages are now captured and logged properly
- [ ] Caching prevents multiple simultaneous `wg show` calls
- [ ] Favicon loads without 404 errors
- [ ] All tests pass
- [ ] No regressions in existing functionality
- [ ] Logs show improved error messages if errors occur
- [ ] Sync job completes without empty error messages

---

## Notes

- The caching TTL of 10 seconds is appropriate because the sync job runs every 30 minutes
- The cache lock prevents race conditions when multiple async tasks try to fetch metrics simultaneously
- The favicon is a simple SVG that represents a VPN/shield concept
- All fixes follow existing code patterns and conventions