# Implementation Plan: Estandarización de parse_mode a Markdown

Track ID: `markdown-standardization_20250227`
Created: 2025-02-27
Status: completed

## Overview

Migrar TODO el codebase a `parse_mode="Markdown"` (normal), eliminando el uso inconsistente de MarkdownV2.

## Phase 1: Migración de Handlers (Alta prioridad)

### Tasks

- [x] **Task 1.1**: Migrar `key_management/handlers_key_management.py`
  - Reemplazar 23 usos de `parse_mode="MarkdownV2"` con `"Markdown"`
  - Verificar que escape_markdown() aún funciona o simplificar

- [x] **Task 1.2**: Migrar `tickets/handlers_tickets.py`
  - Reemplazar 8 usos de `parse_mode="MarkdownV2"` con `"Markdown"`

- [x] **Task 1.3**: Migrar `vpn_keys/handlers_vpn_keys.py`
  - Reemplazar 8 usos de `parse_mode="MarkdownV2"` con `"Markdown"`

- [x] **Task 1.4**: Migrar `user_management/handlers_user_management.py`
  - Reemplazar 2 usos de `parse_mode="MarkdownV2"` con `"Markdown"`

- [x] **Task 1.5**: Migrar `admin/handlers_admin.py`
  - Reemplazar 3 usos de `parse_mode="MarkdownV2"` con `"Markdown"`

### Verification

- [x] **Verify 1.1**: `grep -r 'parse_mode="MarkdownV2"' --include="*.py" telegram_bot/` está vacío
- [x] **Verify 1.2**: `grep -r 'parse_mode="Markdown"' --include="*.py" telegram_bot/` muestra 189 usos

## Phase 2: Limpieza de Mensajes

### Tasks

- [x] **Task 2.1**: Limpiar `messages_key_management.py`
  - Eliminar comentarios "MarkdownV2 Compatible"
  - Limpiar escapes `\!`

- [x] **Task 2.2**: Limpiar `messages_tickets.py`
  - Eliminar comentarios "MarkdownV2 Compatible"
  - Limpiar escapes `\#`, `\.`, agregar docstrings

- [x] **Task 2.3**: Limpiar `messages_vpn_keys.py`
  - Eliminar comentarios "MarkdownV2 Compatible"
  - Limpiar escapes `\|`

### Verification

- [x] **Verify 2.1**: No quedan comentarios "MarkdownV2" en archivos de mensajes
- [x] **Verify 2.2**: Mensajes limpios y legibles

## Phase 3: Utilidades y Finalización

### Tasks

- [x] **Task 3.1**: Simplificar `escape_markdown()` en `utils/telegram_utils.py`
  - Reducida a solo escapar backticks para Markdown normal
  - Actualizada documentación

- [x] **Task 3.2**: Actualizar versiones en headers de archivos
  - Versiones actualizadas para reflejar el cambio

### Verification

- [x] **Verify 3.1**: Tests pasan: 26 tests de telegram_bot
- [x] **Verify 3.2**: No hay errores de sintaxis

## Phase 4: Validación Final

### Tasks

- [x] **Task 4.1**: Verificación completa de usos de parse_mode
  - Todos los 46 usos de MarkdownV2 migrados a Markdown
  - Total: 189 usos de parse_mode="Markdown"

- [x] **Task 4.2**: Actualizar documentación de track
  - Track marcado como completado

### Verification

- [x] **Verify 4.1**: Todos los criterios de aceptación cumplidos
- [x] **Verify 4.2**: Revisión de código final completada

## Resumen de Cambios

| Métrica | Antes | Después |
|---------|-------|---------|
| Usos de MarkdownV2 | 46 | 0 |
| Usos de Markdown | ~149 | 189 |
| Archivos modificados | 0 | 11 |
| Tests pasando | 26 | 26 |

## Archivos Modificados

### Handlers (5 archivos)
- `telegram_bot/features/key_management/handlers_key_management.py`
- `telegram_bot/features/tickets/handlers_tickets.py`
- `telegram_bot/features/vpn_keys/handlers_vpn_keys.py`
- `telegram_bot/features/user_management/handlers_user_management.py`
- `telegram_bot/features/admin/handlers_admin.py`

### Mensajes (3 archivos)
- `telegram_bot/features/key_management/messages_key_management.py`
- `telegram_bot/features/tickets/messages_tickets.py`
- `telegram_bot/features/vpn_keys/messages_vpn_keys.py`

### Utilidades (1 archivo)
- `utils/telegram_utils.py`

### Documentación del Track (2 archivos)
- `conductor/tracks/markdown-standardization_20250227/spec.md`
- `conductor/tracks/markdown-standardization_20250227/plan.md`

## Checkpoints

| Phase | Checkpoint SHA | Date | Status |
| ----- | -------------- | ---- | ------ |
| Phase 1 | 4d15ff9 | 2025-02-27 | completed |
| Phase 2 | 4d15ff9 | 2025-02-27 | completed |
| Phase 3 | 4d15ff9 | 2025-02-27 | completed |
| Phase 4 | 4d15ff9 | 2025-02-27 | completed |
