# Fix: Admin Users List Shows "No Users" When Users Exist

## Overview

Bug en el panel de administración donde el dashboard muestra correctamente la cantidad de usuarios, pero al hacer clic en "Ver Usuarios" desde el dashboard, se muestra el mensaje "No hay usuarios registrados en el sistema" incluso cuando sí existen usuarios activos.

## Functional Requirements

### FR-1: Reset Pagination on Dashboard View

**Description:** Al mostrar el dashboard, debe resetearse el número de página de usuarios para evitar que valores obsoletos causen problemas de paginación.

- **Acceptance:** Cuando el administrador abre el dashboard, `context.user_data["users_page"]` debe establecerse en 1 o eliminarse.

### FR-2: Validate Page Number in show_users

**Description:** El método `show_users` debe validar que el número de página solicitado no exceda el total de páginas disponibles.

- **Acceptance:** Si `users_page` es mayor que `total_pages`, debe ajustarse automáticamente a la última página válida o a la primera página.

### FR-3: Handle Edge Cases

**Description:** Manejar casos extremos como página 0, números negativos, o valores no numéricos en `users_page`.

- **Acceptance:** Cualquier valor inválido en `users_page` debe ser tratado como página 1.

## Non-Functional Requirements

### NFR-1: Performance

- **Target:** El fix no debe agregar overhead significativo a las operaciones existentes.
- **Verification:** Las llamadas a la base de datos deben mantenerse igual.

### NFR-2: Backward Compatibility

- **Target:** El fix no debe romper funcionalidad existente.
- **Verification:** Navegación normal entre páginas de usuarios debe seguir funcionando.

## Acceptance Criteria

- [ ] Dashboard resetea `users_page` cuando se muestra
- [ ] `show_users` valida y corrige números de página inválidos
- [ ] Usuarios se muestran correctamente incluso después de navegar por muchas páginas y volver
- [ ] Tests existentes siguen pasando
- [ ] Casos de borde (página 0, negativa, mayor al total) son manejados correctamente

## Scope

### In Scope

- Modificación de `show_dashboard()` en `handlers_admin.py` para resetear paginación
- Modificación de `show_users()` en `handlers_admin.py` para validar número de página
- Posible modificación de `get_users_paginated()` en `admin_service.py` para lógica de validación

### Out of Scope

- Cambios a la base de datos
- Modificación de otros handlers de admin
- Cambios a la UI/teclados

## Dependencies

### Internal

- `telegram_bot/features/admin/handlers_admin.py`
- `application/services/admin_service.py`

### External

- Ninguna

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Break pagination navigation | Medium | Probar navegación de páginas después del fix |
| Introducir regresión | Low | Ejecutar tests existentes antes de commit |

## Open Questions

- [x] ¿Cuál es la causa raíz? - Paginación con número de página inválido/stale
- [x] ¿Dónde debe ir el fix principal? - `show_dashboard()` y `show_users()`
