# Estandarización de parse_mode a Markdown

## Overview

Migrar TODO el codebase de Telegram Bot a `parse_mode="Markdown"` (normal), eliminando el uso inconsistente de MarkdownV2 que requiere escapes innecesarios para caracteres como `#`, `.`, `|`, `!`.

## Functional Requirements

### FR-1: Migrar handlers de MarkdownV2 a Markdown

Migrar todos los handlers que actualmente usan `parse_mode="MarkdownV2"` a `parse_mode="Markdown"`.

- Acceptance: Ningún archivo usa `parse_mode="MarkdownV2"` después del cambio
- Acceptance: `grep -r 'parse_mode="MarkdownV2"' --include="*.py" telegram_bot/` retorna vacío

### FR-2: Limpiar escapes innecesarios en mensajes

Eliminar escapes innecesarios como `\\#`, `\\.`, `\\|`, `\\!` de los archivos de mensajes que eran necesarios solo para MarkdownV2.

- Acceptance: Mensajes se renderizan correctamente sin escapes
- Acceptance: Variables dinámicas funcionan correctamente en los mensajes

### FR-3: Simplificar utilidad escape_markdown()

Revisar y simplificar/eliminar la función `escape_markdown()` en `utils/telegram_utils.py` si ya no es necesaria para Markdown normal.

- Acceptance: Función actualizada o eliminada si es redundante
- Acceptance: Código más legible en handlers

## Non-Functional Requirements

### NFR-1: Consistencia de código

Todo el codebase debe usar un único estándar de parse_mode.

- Target: 100% de archivos usando `parse_mode="Markdown"`
- Verification: `grep -r 'parse_mode="Markdown"' --include="*.py" telegram_bot/ | wc -l` debe ser ~195

### NFR-2: Reducción de complejidad

Eliminar código innecesario y comentarios redundantes.

- Target: Reducir ~50 líneas de código entre mensajes y utilidades
- Verification: Conteo de líneas antes/después

## Acceptance Criteria

- [ ] Ningún archivo usa `parse_mode="MarkdownV2"`
- [ ] Todos los mensajes se renderizan correctamente sin escapes innecesarios
- [ ] Los mensajes con variables dinámicas funcionan correctamente
- [ ] No hay regresiones visuales
- [ ] `escape_markdown()` simplificada o eliminada
- [ ] Todos los tests pasan
- [ ] flake8, black, mypy pasan sin errores

## Scope

### In Scope

- Migrar handlers: key_management, tickets, vpn_keys, user_management, admin
- Limpiar mensajes: messages_key_management.py, messages_tickets.py, messages_vpn_keys.py
- Actualizar utilidad escape_markdown()
- Actualizar comentarios "MarkdownV2 Compatible" en mensajes

### Out of Scope

- Cambios funcionales al comportamiento del bot
- Modificación de mensajes de otros features (buy_gb ya usa Markdown consistentemente)
- Cambios a la lógica de negocio

## Dependencies

### Internal

- Ninguno - refactorización autónoma

### External

- Ninguno

## Risks and Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Caracteres especiales rompen renderizado | Medium | Testing manual de flujos críticos después del cambio |
| Variables dinámicas con caracteres especiales | Medium | Revisar cada uso de escape_markdown() |
| Regresiones visuales | Low | Verificación visual de mensajes clave |

## Open Questions

- [x] ¿Es seguro eliminar completamente escape_markdown()? Sí, para Markdown normal solo necesitamos escapar backticks y backslashes en casos muy específicos.
