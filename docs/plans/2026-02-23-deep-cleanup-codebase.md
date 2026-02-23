# Limpieza Profunda del Codebase - Plan de Implementación

> **Investigación completada:** 2026-02-23
> **Objetivo:** Obtener un codebase limpio, robusto y bien organizado

---

## RESUMEN DE HALLAZGOS

### 🗑️ Archivos Sin Uso (6 archivos)
| # | Archivo | Líneas | Motivo |
|---|---------|--------|--------|
| 1 | `utils/datetime_utils.py` | 24 | No importado en ningún lugar |
| 2 | `utils/sip_prompts.py` | 212 | Funcionalidad AI no implementada |
| 3 | `telegram_bot/common/patterns.py` | 373 | Patrones nunca adoptados |
| 4 | `core/lifespan.py` | 75 | FastAPI no usado |
| 5 | `domain/interfaces/ivpn_service.py` | 24 | Protocol sin uso |
| 6 | `application/services/payment_service.py` | 145 | Solo usado en tests |

### 📁 Carpetas Vacías (2 carpetas)
| # | Carpeta | Acción |
|---|---------|--------|
| 1 | `temp/` | Eliminar |
| 2 | `application/ports/` | Eliminar (solo __init__.py vacío) |

### 🔄 Código Duplicado
| # | Ubicación | Problema |
|---|-----------|----------|
| 1 | `container.py:122-167` | 4 funciones duplicadas |
| 2 | `user_repository.py:80-81` | `get_user()` alias redundante |
| 3 | 6+ archivos mensajes | Error classes duplicados |
| 4 | 6+ archivos keyboards | `back_to_main_menu` duplicado |
| 5 | 9 handlers | Patrón registration duplicado |

### 📄 Documentación Obsoleta
- 23 archivos en `docs/plans/` de implementaciones completadas

---

## FASES DE IMPLEMENTACIÓN

## FASE 1: Eliminar Archivos Sin Uso

### Issue 1.1: Eliminar archivos completamente sin uso

**Archivos a eliminar:**
```bash
rm utils/datetime_utils.py
rm utils/sip_prompts.py
rm telegram_bot/common/patterns.py
rm core/lifespan.py
rm domain/interfaces/ivpn_service.py
```

**Verificación:**
```bash
pytest -v
```

---

### Issue 1.2: Eliminar PaymentService y actualizar tests

**Acciones:**
1. Eliminar `application/services/payment_service.py`
2. Eliminar `tests/application/services/test_payment_service.py`
3. Verificar que no hay imports rotos

**Verificación:**
```bash
pytest -v
grep -r "PaymentService" --include="*.py" | grep -v venv
```

---

## FASE 2: Eliminar Carpetas Vacías

### Issue 2.1: Limpiar carpetas vacías

```bash
rm -rf temp/
rm -rf application/ports/
```

**Nota:** `application/ports/` solo contiene `__init__.py` vacío

---

## FASE 3: Consolidar Código Duplicado

### Issue 3.1: Corregir container.py - funciones duplicadas

**Problema:** Líneas 122-136 y 153-167 tienen funciones idénticas

**Solución:** Eliminar las funciones duplicadas en `_configure_application_services()`
que ya están definidas en `_configure_repositories()`

---

### Issue 3.2: Eliminar método redundante en user_repository.py

**Problema:** `get_user()` es un alias innecesario de `get_by_id()`

**Solución:** Eliminar método `get_user()` y actualizar callers si existen

---

### Issue 3.3: Consolidar mensajes de error duplicados

**Archivos afectados:**
- `telegram_bot/features/key_management/messages_key_management.py`
- `telegram_bot/features/admin/messages_admin.py`
- `telegram_bot/features/buy_gb/messages_buy_gb.py`
- `telegram_bot/features/operations/messages_operations.py`
- `telegram_bot/features/referral/messages_referral.py`

**Solución:** Usar `CommonMessages.Error` de `telegram_bot/common/messages.py`

---

### Issue 3.4: Consolidar keyboards de navegación

**Archivos afectados:**
- `telegram_bot/features/key_management/keyboards_key_management.py`
- `telegram_bot/features/admin/keyboards_admin.py`
- `telegram_bot/features/operations/keyboards_operations.py`
- `telegram_bot/features/tickets/keyboards_tickets.py`

**Solución:** Usar `CommonKeyboards.back_to_main_menu()` de `telegram_bot/common/keyboards.py`

---

## FASE 4: Limpieza de Documentación

### Issue 4.1: Archivar planes obsoletos

**Acción:** Crear carpeta `docs/plans/archive/` y mover planes completados

```bash
mkdir -p docs/plans/archive/
mv docs/plans/2026-02-21-*.md docs/plans/archive/
mv docs/plans/2026-02-22-*.md docs/plans/archive/
```

---

### Issue 4.2: Actualizar README.md

**Mejoras:**
- Agregar badges actualizados
- Agregar sección de arquitectura
- Actualizar comandos de instalación
- Agregar link a AGENTS.md

---

## FASE 5: Verificación Final

### Issue 5.1: Ejecutar suite de tests completa

```bash
pytest -v --cov=.
```

### Issue 5.2: Verificar imports y tipos

```bash
python -m py_compile main.py
```

### Issue 5.3: Commit final y merge

```bash
git add -A
git commit -m "chore: deep codebase cleanup

- Remove unused files (datetime_utils, sip_prompts, patterns, lifespan, ivpn_service, payment_service)
- Remove empty directories (temp, application/ports)
- Fix duplicate functions in container.py
- Remove redundant get_user() method in user_repository
- Archive completed implementation plans
- Update README.md

Refs: #[issue-number]"
```

---

## ORDEN DE EJECUCIÓN

1. **Issue 1.1** → Eliminar archivos sin uso (sin tests)
2. **Issue 2.1** → Eliminar carpetas vacías
3. **Issue 1.2** → Eliminar PaymentService y tests
4. **Issue 3.1** → Corregir container.py
5. **Issue 3.2** → Eliminar método redundante
6. **Issue 3.3** → Consolidar mensajes de error
7. **Issue 3.4** → Consolidar keyboards
8. **Issue 4.1** → Archivar planes obsoletos
9. **Issue 4.2** → Actualizar README
10. **Issue 5.1-5.3** → Verificación y merge

---

## ESTIMACIÓN

| Fase | Issues | Tiempo |
|------|--------|--------|
| Fase 1 | 2 | 15 min |
| Fase 2 | 1 | 5 min |
| Fase 3 | 4 | 45 min |
| Fase 4 | 2 | 15 min |
| Fase 5 | 3 | 15 min |
| **Total** | **12** | **~1.5h** |
