# Plan de Implementación: Estandarización de Parse Mode

Track ID: `markdown-standardization_20250227`  
Status: pending  
Creado: 2025-02-27

## Fase 1: Análisis Detallado y Preparación

### Tasks

- [ ] **Task 1.1**: Documentar todos los usos de MarkdownV2 por archivo
  - Crear lista completa de líneas que usan `parse_mode="MarkdownV2"`
 - Identificar mensajes asociados que requieren limpieza de escapes

- [ ] **Task 1.2**: Crear script de verificación visual
  - Script que capture screenshots o texto renderizado antes del cambio
  - Permite comparar before/after

- [ ] **Task 1.3**: Preparar entorno de testing
  - Verificar que tests existentes pasan
  - Identificar tests que verifican contenido de mensajes

### Verification

- [ ] **Verify 1.1**: Lista completa de 46 usos de MarkdownV2 documentada
- [ ] **Verify 1.2**: Script de verificación funciona correctamente
- [ ] **Verify 1.3**: Todos los tests pasan en estado inicial

---

## Fase 2: Migración de Handlers Principales

### Tasks

- [ ] **Task 2.1**: Migrar `vpn_keys/handlers_vpn_keys.py`
  - Cambiar 8 usos de `MarkdownV2` a `Markdown`
  - Verificar mensajes en `messages_vpn_keys.py` no requieren escapes

- [ ] **Task 2.2**: Migrar `key_management/handlers_key_management.py`
  - Cambiar 23 usos de `MarkdownV2` a `Markdown`
  - Limpiar escapes en `messages_key_management.py`
  - Nota: Línea 279 comenta "Usar caracteres que no requieren escape en MarkdownV2" - verificar

- [ ] **Task 2.3**: Migrar `tickets/handlers_tickets.py`
  - Cambiar 8 usos de `MarkdownV2` a `Markdown`
  - Limpiar escapes en `messages_tickets.py` (`\#`, `\.`, etc.)

- [ ] **Task 2.4**: Migrar `user_management/handlers_user_management.py`
  - Cambiar 2 usos de `MarkdownV2` a `Markdown` (líneas 204, 211)

- [ ] **Task 2.5**: Migrar `admin/handlers_admin.py`
  - Cambiar 3 usos de `MarkdownV2` a `Markdown`

### Verification

- [ ] **Verify 2.1**: Todos los handlers migrados, 0 usos de MarkdownV2 restantes
- [ ] **Verify 2.2**: Mensajes se renderizan correctamente (comparar con baseline)
- [ ] **Verify 2.3**: Todos los tests pasan

---

## Fase 3: Limpieza de Archivos de Mensajes

### Tasks

- [ ] **Task 3.1**: Limpiar `messages_vpn_keys.py`
  - Eliminar header "Version: 3.2.0 - MarkdownV2 Compatible"
  - Eliminar comentarios "MarkdownV2 OK"
  - Verificar escapes `\|` en línea 74

- [ ] **Task 3.2**: Limpiar `messages_key_management.py`
  - Eliminar header "Version: 3.2.0 - MarkdownV2 Compatible"
  - Eliminar comentarios "MarkdownV2 OK"
  - Verificar escapes `\!` en línea 100

- [ ] **Task 3.3**: Limpiar `messages_tickets.py`
  - Eliminar escapes `\#` (líneas 11, 26, 46, 56)
  - Eliminar escapes `\.` (líneas 14, 21, 22, 61, 62, 63)

- [ ] **Task 3.4**: Revisar otros archivos de mensajes
  - Verificar si hay escapes innecesarios en `messages_buy_gb.py`
  - Verificar `messages_user_management.py`

### Verification

- [ ] **Verify 3.1**: Mensajes limpios sin referencias a MarkdownV2
- [ ] **Verify 3.2**: Visualmente idénticos al estado anterior
- [ ] **Verify 3.3**: No hay caracteres escapados innecesariamente

---

## Fase 4: Actualización de Utilidades

### Tasks

- [ ] **Task 4.1**: Actualizar `telegram_utils.py`
  - Modificar `escape_markdown()` para usar Markdown normal o deprecar
  - Actualizar `safe_edit_message()` para usar Markdown por defecto

- [ ] **Task 4.2**: Actualizar imports y referencias
  - Buscar usos de `escape_markdown()` en handlers
  - Eliminar o simplificar llamadas innecesarias

- [ ] **Task 4.3**: Actualizar documentación
  - Modificar docstrings que mencionan MarkdownV2
  - Actualizar comentarios en código

### Verification

- [ ] **Verify 4.1**: `escape_markdown()` simplificada o eliminada
- [ ] **Verify 4.2**: `safe_edit_message()` usa Markdown por defecto
- [ ] **Verify 4.3**: No hay referencias obsoletas a MarkdownV2 en utilidades

---

## Fase 5: Testing y Validación Final

### Tasks

- [ ] **Task 5.1**: Ejecutar suite completa de tests
  ```bash
  pytest -v
  flake8 .
  black --check .
  mypy .
  ```

- [ ] **Task 5.2**: Testing manual de flujos críticos
  - /start
  - Creación de llaves VPN
  - Gestión de llaves
  - Tickets de soporte
  - Panel admin

- [ ] **Task 5.3**: Verificación final de parse_mode
  ```bash
  grep -r 'parse_mode="MarkdownV2"' --include="*.py"
  # Debe retornar vacío
  ```

- [ ] **Task 5.4**: Conteo de líneas de código
  - Comparar LOC antes/después
  - Verificar reducción esperada (~12%)

### Verification

- [ ] **Verify 5.1**: Todos los tests pasan
- [ ] **Verify 5.2**: Linters pasan sin errores
- [ ] **Verify 5.3**: No hay usos de MarkdownV2 en el codebase
- [ ] **Verify 5.4**: Documentación actualizada

---

## Checkpoints

| Phase   | Checkpoint SHA | Date | Status  |
|---------|----------------|------|---------|
| Phase 1 |                |      | pending |
| Phase 2 |                |      | pending |
| Phase 3 |                |      | pending |
| Phase 4 |                |      | pending |
| Phase 5 |                |      | pending |

## Notas de Implementación

### Patrones de Reemplazo

```python
# ANTES (MarkdownV2):
parse_mode="MarkdownV2"
# En mensajes:
"ID: \\#{ticket_id}\n"
"Texto con punto final\\."

# DESPUÉS (Markdown):
parse_mode="Markdown"
# En mensajes:
"ID: #{ticket_id}\n"
"Texto con punto final."
```

### Archivos Prioritarios

1. **Alta prioridad**: `key_management/handlers_key_management.py` (23 usos)
2. **Alta prioridad**: `tickets/` (handlers + mensajes con muchos escapes)
3. **Media prioridad**: `vpn_keys/` (8 usos)
4. **Baja prioridad**: `admin/`, `user_management/` (pocos usos)

### Comandos Útiles

```bash
# Buscar usos de MarkdownV2
grep -rn 'parse_mode="MarkdownV2"' --include="*.py"

# Buscar escapes MarkdownV2 en mensajes
grep -rn '\\\\#' --include="*.py" telegram_bot/features/
grep -rn '\\\\\.' --include="*.py" telegram_bot/features/
grep -rn '\\\\|' --include="*.py" telegram_bot/features/

# Contar líneas de código
find telegram_bot/features -name "messages_*.py" -exec wc -l {} +
```
