# Data Visualization Implementation Plan (Issue #79)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar visualización detallada del consumo de datos mostrando paquetes individuales, Plan Free y total disponible.

**Architecture:** Extender `DataPackageService.get_user_data_summary()` para incluir datos del Plan Free y detalles de cada paquete. Actualizar mensajes y handler para el nuevo formato.

**Tech Stack:** Python, asyncio, pytest

---

## Task 1: Tests para estructura de datos extendida

**Files:**
- Modify: `tests/application/services/test_data_package_service.py:96-124`

**Step 1: Write the failing test**

Add to `TestGetUserDataSummary` class:

```python
@pytest.mark.asyncio
async def test_returns_detailed_packages_info(self, service, mock_package_repo, mock_user_repo):
    from datetime import datetime, timezone, timedelta
    from domain.entities.user import User
    
    expires_at = datetime.now(timezone.utc) + timedelta(days=15)
    mock_package_repo.get_valid_by_user.return_value = [
        DataPackage(
            id=uuid.uuid4(),
            user_id=123,
            package_type=PackageType.BASIC,
            data_limit_bytes=10 * 1024**3,
            stars_paid=50,
            data_used_bytes=3.2 * 1024**3,
            expires_at=expires_at,
            purchased_at=datetime.now(timezone.utc) - timedelta(days=20)
        )
    ]
    mock_user_repo.get_by_id.return_value = User(
        telegram_id=123,
        free_data_limit_bytes=10 * 1024**3,
        free_data_used_bytes=1.5 * 1024**3
    )
    
    result = await service.get_user_data_summary(123, current_user_id=123)
    
    assert "packages" in result
    assert len(result["packages"]) == 1
    assert result["packages"][0]["name"] == "Básico"
    assert result["packages"][0]["days_remaining"] > 0
    assert "free_plan" in result
    assert result["free_plan"]["remaining_gb"] == 8.5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/application/services/test_data_package_service.py::TestGetUserDataSummary::test_returns_detailed_packages_info -v`
Expected: FAIL with "KeyError: 'packages'" or similar

**Step 3: Commit**

```bash
git add tests/application/services/test_data_package_service.py
git commit -m "test: add test for detailed data summary structure"
```

---

## Task 2: Extender get_user_data_summary()

**Files:**
- Modify: `application/services/data_package_service.py:96-108`

**Step 1: Implement extended summary**

Replace the `get_user_data_summary` method:

```python
async def get_user_data_summary(self, user_id: int, current_user_id: int) -> Dict[str, Any]:
    packages = await self.package_repo.get_valid_by_user(user_id, current_user_id)
    user = await self.user_repo.get_by_id(user_id, current_user_id)
    
    now = datetime.now(timezone.utc)
    packages_detail = []
    
    for pkg in packages:
        expires_at = pkg.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        days_remaining = max(0, (expires_at - now).days)
        
        option = self._get_package_option(pkg.package_type.value)
        package_name = option.name if option else pkg.package_type.value.title()
        
        packages_detail.append({
            "name": package_name,
            "total_gb": pkg.data_limit_bytes / (1024**3),
            "used_gb": pkg.data_used_bytes / (1024**3),
            "remaining_gb": pkg.remaining_bytes / (1024**3),
            "days_remaining": days_remaining
        })
    
    total_limit_bytes = sum(p.data_limit_bytes for p in packages)
    total_used_bytes = sum(p.data_used_bytes for p in packages)
    
    free_plan = {
        "limit_gb": 0.0,
        "used_gb": 0.0,
        "remaining_gb": 0.0
    }
    
    if user:
        free_plan = {
            "limit_gb": user.free_data_limit_bytes / (1024**3),
            "used_gb": user.free_data_used_bytes / (1024**3),
            "remaining_gb": user.free_data_remaining_bytes / (1024**3)
        }
    
    total_remaining = (total_limit_bytes - total_used_bytes) + (user.free_data_remaining_bytes if user else 0)
    
    return {
        "active_packages": len(packages),
        "packages": packages_detail,
        "free_plan": free_plan,
        "total_limit_gb": total_limit_bytes / (1024**3),
        "total_used_gb": total_used_bytes / (1024**3),
        "remaining_gb": total_remaining / (1024**3)
    }
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/application/services/test_data_package_service.py::TestGetUserDataSummary -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add application/services/data_package_service.py
git commit -m "feat: extend get_user_data_summary with detailed packages and free plan"
```

---

## Task 3: Actualizar mensajes de datos

**Files:**
- Modify: `telegram_bot/features/buy_gb/messages_buy_gb.py:78-96`

**Step 1: Replace BuyGbMessages.Data class**

```python
class Data:
    """Mensajes para comando /data."""

    HEADER = "💾 *Tu Consumo de Datos*\n"
    SEPARATOR = "═══════════════════════\n"

    @staticmethod
    def format_packages_list(packages: list) -> str:
        if not packages:
            return ""
        lines = ["📦 *Paquetes Activos:*"]
        for pkg in packages:
            lines.append(f"   • {pkg['name']} {pkg['total_gb']:.0f}GB ({pkg['days_remaining']} días restantes)")
            lines.append(f"     Usado: {pkg['used_gb']:.1f} GB / {pkg['total_gb']:.0f} GB")
            lines.append(f"     Disponible: {pkg['remaining_gb']:.1f} GB")
        return "\n".join(lines)

    @staticmethod
    def format_free_plan(free_plan: dict) -> str:
        return (
            f"🎁 *Plan Free:*\n"
            f"   Disponible: {free_plan['remaining_gb']:.1f} GB"
        )

    @staticmethod
    def DATA_INFO(summary: dict) -> str:
        lines = [BuyGbMessages.Data.HEADER]
        lines.append("")
        lines.append(BuyGbMessages.Data.SEPARATOR)
        lines.append("")
        
        if summary.get("packages"):
            lines.append(BuyGbMessages.Data.format_packages_list(summary["packages"]))
            lines.append("")
            lines.append(BuyGbMessages.Data.SEPARATOR)
            lines.append("")
        
        lines.append(BuyGbMessages.Data.format_free_plan(summary["free_plan"]))
        lines.append("")
        lines.append(BuyGbMessages.Data.SEPARATOR)
        lines.append("")
        lines.append(f"📊 *TOTAL DISPONIBLE:* {summary['remaining_gb']:.1f} GB")
        lines.append("")
        lines.append("💡 El consumo usa primero los paquetes comprados")
        
        return "\n".join(lines)

    NO_DATA = (
        "💾 *Mis Datos*\n\n"
        "No tienes paquetes de datos activos.\n\n"
        "Usa /buy para adquirir más datos."
    )
```

**Step 2: Commit**

```bash
git add telegram_bot/features/buy_gb/messages_buy_gb.py
git commit -m "feat: add detailed data visualization message format"
```

---

## Task 4: Actualizar handler de datos

**Files:**
- Modify: `telegram_bot/features/buy_gb/handlers_buy_gb.py:244-275`

**Step 1: Update data_handler method**

```python
async def data_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el consumo de datos del usuario."""
    user_id = update.effective_user.id
    logger.info(f"💾 /data ejecutado por usuario {user_id}")

    try:
        summary = await self.data_package_service.get_user_data_summary(
            user_id=user_id,
            current_user_id=user_id
        )

        if summary["active_packages"] == 0 and summary["free_plan"]["remaining_gb"] <= 0:
            message = BuyGbMessages.Data.NO_DATA
        else:
            message = BuyGbMessages.Data.DATA_INFO(summary)

        await update.message.reply_text(
            text=message,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error en data_handler: {e}")
        await update.message.reply_text(
            text=BuyGbMessages.Error.SYSTEM_ERROR,
            parse_mode="Markdown"
        )
```

**Step 2: Run tests**

Run: `pytest tests/ -v -k "data_package"`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add telegram_bot/features/buy_gb/handlers_buy_gb.py
git commit -m "feat: update data_handler to use detailed summary format"
```

---

## Task 5: Test de integración manual

**Step 1: Start the bot**

Run: `python main.py`

**Step 2: Test /data command**

Send `/data` to the bot and verify:
- Shows individual packages with days remaining
- Shows Plan Free section
- Shows total available
- Shows usage hint

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat(issue-79): complete data visualization implementation"
```

---

## Verification

- [ ] Tests unitarios pasan
- [ ] Comando `/data` muestra formato correcto
- [ ] Paquetes individuales con días restantes
- [ ] Plan Free visible
- [ ] Total calculado correctamente
