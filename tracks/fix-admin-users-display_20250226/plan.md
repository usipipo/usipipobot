# Implementation Plan: Fix Admin Users Display Bug

Track ID: `fix-admin-users-display_20250226`
Created: 2025-02-26
Status: in-progress

## Overview

Implementar fix para el bug donde el dashboard de admin muestra usuarios correctamente pero "Ver Usuarios" muestra "No hay usuarios registrados" debido a paginación con valores stale/inválidos.

## Phase 1: Root Cause Verification

### Tasks

- [x] **Task 1.1**: Analizar código de `show_dashboard()` y `show_users()`
  - Identificar que `show_dashboard` no resetea `users_page`
  - Identificar que `show_users` usa `users_page` sin validación
- [x] **Task 1.2**: Confirmar hipótesis del bug
  - Valores stale de `users_page` causan offset inválido
  - Slice de lista vacío cuando página > total_pages

### Verification

- [x] **Verify 1.1**: Documentar flujo exacto del bug en spec.md

## Phase 2: Implementation

### Tasks

- [ ] **Task 2.1**: Modificar `show_dashboard()` para resetear paginación
  - Agregar `context.user_data["users_page"] = 1` antes de mostrar dashboard
  - Ubicación: `telegram_bot/features/admin/handlers_admin.py` línea ~939
  
- [ ] **Task 2.2**: Modificar `show_users()` para validar número de página
  - Después de obtener `total_pages`, validar que `page <= total_pages`
  - Si `page > total_pages`, establecer `page = total_pages` (o 1 si total_pages = 0)
  - Si `page < 1`, establecer `page = 1`
  - Ubicación: `telegram_bot/features/admin/handlers_admin.py` líneas ~115-121

- [ ] **Task 2.3**: Aplicar misma lógica a `_show_users_page()`
  - Método usado para navegación entre páginas
  - Asegurar consistencia en validación
  - Ubicación: `telegram_bot/features/admin/handlers_admin.py` líneas ~167-211

### Verification

- [ ] **Verify 2.1**: Revisar código modificado con flake8/black
- [ ] **Verify 2.2**: Ejecutar tests de admin handlers

## Phase 3: Testing & Validation

### Tasks

- [ ] **Task 3.1**: Ejecutar tests existentes
  ```bash
  pytest tests/telegram_bot/features/admin/ -v
  ```

- [ ] **Task 3.2**: Verificar fix con escenario simulado
  - Simular `users_page = 100` con solo 25 usuarios
  - Verificar que ahora muestra página 1 (o última válida)

- [ ] **Task 3.3**: Verificar navegación normal sigue funcionando
  - Navegar página 1 → 2 → 3
  - Volver al menú → Dashboard → Ver Usuarios
  - Confirmar que siempre muestra usuarios correctamente

### Verification

- [ ] **Verify 3.1**: Todos los tests pasan
- [ ] **Verify 3.2**: Escenario del bug está corregido
- [ ] **Verify 3.3**: No hay regresiones en navegación

## Phase 4: Finalization

### Tasks

- [ ] **Task 4.1**: Commit de cambios
  - Mensaje: "fix(admin): reset pagination on dashboard and validate page numbers
    
    Fixes issue where 'Ver Usuarios' showed 'No users' after stale page number
    from previous session caused empty pagination result."

- [ ] **Task 4.2**: Merge a develop
  - Crear PR/MR si es necesario
  - Merge una vez aprobado

- [ ] **Task 4.3**: Push a origin
  - Asegurar que develop está actualizado

- [ ] **Task 4.4**: Cleanup
  - Eliminar branch de feature
  - Cerrar issue de GitHub

### Verification

- [ ] **Verify 4.1**: Código en develop
- [ ] **Verify 4.2**: Issue cerrado

## Checkpoints

| Phase | Checkpoint SHA | Date | Status |
|-------|----------------|------|--------|
| Phase 1 | - | 2025-02-26 | completed |
| Phase 2 | - | - | pending |
| Phase 3 | - | - | pending |
| Phase 4 | - | - | pending |

## Notes

- El fix es mínimo y enfocado
- No requiere cambios en base de datos
- Tests existentes deberían pasar sin modificaciones
