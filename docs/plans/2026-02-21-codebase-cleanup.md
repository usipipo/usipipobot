# Limpieza de Codebase - Implementación Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminar archivos, carpetas y código obsoleto del codebase desde la implementación del issue 70.

**Architecture:** Limpieza sistemática en fases: scripts shell → carpetas vacías → servicios obsoletos → features no implementadas → documentación obsoleta → actualización de imports.

**Tech Stack:** Python 3.13, pytest, flake8, black, isort

---

## Fase 1: Scripts Shell Obsoletos

### Task 1: Eliminar scripts de shell antiguos

**Files:**
- Delete: `bot.sh`
- Delete: `install.sh`
- Delete: `ol_server.sh`
- Delete: `wg_server.sh`
- Delete: `update_version.py`

**Step 1: Verificar que los scripts no son referenciados**

Run: `grep -r "bot.sh\|install.sh\|ol_server.sh\|wg_server.sh\|update_version" --include="*.py" --include="*.sh" --include="*.md" | grep -v venv | grep -v __pycache__`
Expected: No references found (except in this plan)

**Step 2: Eliminar scripts**

```bash
rm bot.sh install.sh ol_server.sh wg_server.sh update_version.py
```

**Step 3: Verificar eliminación**

Run: `ls -la *.sh 2>/dev/null || echo "No shell scripts found"`
Expected: "No shell scripts found"

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete shell scripts and update_version.py"
```

---

## Fase 2: Carpetas Vacías

### Task 2: Eliminar carpetas vacías y sin uso

**Files:**
- Delete: `api/` (completely empty endpoints)
- Delete: `templates/` (empty)
- Delete: `static/` (empty subdirs)
- Delete: `temp/` (empty)

**Step 1: Verificar que las carpetas están vacías o sin uso**

Run: `find api/ templates/ static/ temp/ -type f 2>/dev/null | grep -v __pycache__ | grep -v __init__.py`
Expected: Empty or only __init__.py files

**Step 2: Eliminar carpetas**

```bash
rm -rf api/ templates/ static/ temp/
```

**Step 3: Verificar eliminación**

Run: `ls -la api/ templates/ static/ temp/ 2>&1 | head -1`
Expected: "ls: cannot access..." for all directories

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove empty directories (api, templates, static, temp)"
```

---

## Fase 3: Servicios Obsoletos

### Task 3: Eliminar achievement_service.py (stub vacío)

**Files:**
- Delete: `application/services/achievement_service.py`
- Modify: `telegram_bot/features/user_management/handlers_user_management.py`
- Modify: `application/services/common/container.py`

**Step 1: Eliminar archivo achievement_service**

```bash
rm application/services/achievement_service.py
```

**Step 2: Actualizar handlers_user_management.py para remover imports y referencias**

En `telegram_bot/features/user_management/handlers_user_management.py`:
- Eliminar línea 19: `from application.services.achievement_service import AchievementService`
- Modificar constructor para remover achievement_service
- Eliminar referencias a self.achievement_service
- Simplificar info_handler para no usar achievement_service

**Step 3: Verificar que no hay imports rotos**

Run: `python -c "from telegram_bot.features.user_management.handlers_user_management import *"`
Expected: No errors

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove empty achievement_service and references"
```

---

## Fase 4: Features No Implementadas

### Task 4: Limpiar operations/ de funcionalidad no implementada

**Files:**
- Modify: `telegram_bot/features/operations/handlers_operations.py`
- Modify: `telegram_bot/features/operations/messages_operations.py`
- Modify: `telegram_bot/features/operations/keyboards_operations.py`

**Step 1: Remover handlers no implementados (VIP, games, referrals)**

En `handlers_operations.py`:
- Eliminar `show_vip_plans` method
- Eliminar `show_game_menu` method
- Eliminar `referidos` method
- Actualizar `get_operations_handlers` y `get_operations_callback_handlers`

**Step 2: Actualizar messages_operations.py**

Remover secciones VIP, Game, Referral de mensajes.

**Step 3: Actualizar keyboards_operations.py**

Remover teclados VIP, Game, Referral.

**Step 4: Verificar imports**

Run: `python -c "from telegram_bot.features.operations.handlers_operations import *"`
Expected: No errors

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove unimplemented VIP, game, referral from operations"
```

---

## Fase 5: Documentación Obsoleta

### Task 5: Limpiar documentación de planes completados

**Files:**
- Delete: `docs/plans/2026-02-20-data-visualization-design.md`
- Delete: `docs/plans/2026-02-20-data-visualization.md`
- Delete: `docs/plans/2026-02-20-issue-76-main-menu.md`
- Delete: `docs/plans/2026-02-20-issue-80-basic-commands.md`
- Delete: `docs/plans/2026-02-21-cicd-github-actions.md`
- Delete: `docs/plans/2026-02-21-issue-78-vpn-key-flow.md`

**Step 1: Verificar que los issues están cerrados**

Run: `gh issue view 76 78 79 80 --json state,number`
Expected: All issues are CLOSED

**Step 2: Eliminar planes completados**

```bash
rm docs/plans/2026-02-20-*.md docs/plans/2026-02-21-*.md
```

**Step 3: Verificar que docs/plans está vacío o solo tiene este plan**

Run: `ls docs/plans/`
Expected: Only this cleanup plan

**Step 4: Commit**

```bash
git add -A
git commit -m "docs: remove completed implementation plans"
```

---

## Fase 6: Actualización de Imports y Container

### Task 6: Limpiar container.py de referencias obsoletas

**Files:**
- Modify: `application/services/common/container.py`

**Step 1: Remover imports no usados**

En `container.py`:
- Verificar y remover imports de features eliminados
- Simplificar handlers registration

**Step 2: Verificar que el container funciona**

Run: `python -c "from application.services.common.container import get_container; c = get_container(); print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add -A
git commit -m "refactor: clean up container.py imports"
```

---

## Fase 7: Verificación Final

### Task 7: Ejecutar tests y linting

**Step 1: Ejecutar tests**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Ejecutar flake8**

Run: `flake8 . --exclude=venv,.venv,__pycache__,.git,migrations`
Expected: No errors

**Step 3: Ejecutar verificación de imports**

Run: `python -c "import main; print('Main imports OK')"`
Expected: Main imports OK

**Step 4: Commit final**

```bash
git add -A
git commit -m "chore: verify cleanup - all tests and linting pass"
```

---

## Resumen de Archivos Eliminados

| Archivo/Carpeta | Razón |
|-----------------|-------|
| `bot.sh` | Script shell obsoleto |
| `install.sh` | Script shell obsoleto |
| `ol_server.sh` | Script shell obsoleto |
| `wg_server.sh` | Script shell obsoleto |
| `update_version.py` | Script no usado |
| `api/` | Carpeta vacía |
| `templates/` | Carpeta vacía |
| `static/` | Carpetas vacías |
| `temp/` | Carpeta vacía |
| `achievement_service.py` | Stub vacío |
| `docs/plans/*.md` | Planes completados |

## Resumen de Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `handlers_user_management.py` | Remover achievement_service |
| `handlers_operations.py` | Remover VIP/game/referral |
| `messages_operations.py` | Remover mensajes obsoletos |
| `keyboards_operations.py` | Remover teclados obsoletos |
| `container.py` | Limpiar imports |

---

**Execution Options:**

1. **Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks
2. **Parallel Session (separate)** - Open new session with executing-plans skill