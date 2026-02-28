# Track: Menu Operaciones + Historial Transacciones

## Overview

Mejorar el diseño del menú de operaciones del bot de Telegram y agregar un nuevo botón para visualizar el historial completo de transacciones del usuario, incluyendo todas las transacciones de crypto (pendientes, completadas, fallidas, expiradas, canceladas).

## Type

feature

## Functional Requirements

### FR-1: Rediseño del Menú de Operaciones
- Mejorar el layout visual del menú actual
- Organizar botones en secciones lógicas
- Mantener compatibilidad con funcionalidad existente

### FR-2: Botón de Historial de Transacciones
- Agregar nuevo botón "📜 Historial" al menú de operaciones
- Implementar handler para mostrar lista de transacciones
- Soportar paginación si hay muchas transacciones

### FR-3: Visualización de Transacciones Crypto
- Mostrar órdenes de crypto con estados: pending, completed, failed, expired
- Incluir detalles: tipo de paquete, monto, fecha, estado
- Usar emojis e indicadores visuales para cada estado

### FR-4: Estados de Transacciones
- **Pendiente**: ⏳ Esperando pago
- **Completada**: ✅ Pagada y procesada
- **Fallida**: ❌ Error en el pago
- **Expirada**: ⏰ Tiempo de pago agotado
- **Cancelada**: 🚫 Cancelada por usuario

## Non-Functional Requirements

### NFR-1: Performance
- Cargar historial en menos de 2 segundos
- Limitar a 20 transacciones por página

### NFR-2: UX
- Mensajes claros y formateados con Markdown
- Botones intuitivos para navegación
- Mensaje informativo cuando no hay transacciones

### NFR-3: Seguridad
- Solo mostrar transacciones del usuario autenticado
- No exponer datos sensibles (wallet addresses completos)

## Acceptance Criteria

- [ ] El menú de operaciones tiene diseño mejorado
- [ ] Botón "📜 Historial" visible en menú de operaciones
- [ ] Al hacer clic se muestra lista de transacciones del usuario
- [ ] Cada transacción muestra: tipo, monto, fecha, estado con emoji
- [ ] Estados visualizados correctamente con emojis correspondientes
- [ ] Mensaje amigable cuando usuario no tiene transacciones
- [ ] Botón para volver al menú de operaciones
- [ ] Tests unitarios para nuevos handlers

## Scope

### In Scope
- Modificación de `keyboards_operations.py`
- Modificación de `handlers_operations.py`
- Modificación de `messages_operations.py`
- Nuevo servicio o método para obtener historial de transacciones
- Tests para nueva funcionalidad

### Out of Scope
- Modificación de base de datos (ya existe crypto_orders)
- Nuevos tipos de transacciones
- Exportación de historial
- Filtros avanzados de búsqueda

## Dependencies

### Internal
- `CryptoOrderRepository` - ya implementado
- `OperationsHandler` - ya implementado
- `CryptoOrder` entity - ya implementado

### External
- python-telegram-bot library

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cambios rompen menú existente | Medium | Mantener todos los callback_data existentes |
| Muchas transacciones ralentizan bot | Low | Implementar paginación desde inicio |
| Datos sensibles expuestos | Low | Enmascarar direcciones de wallet |

## Open Questions

- [x] ¿Cuántas transacciones mostrar por página? → 10
- [x] ¿Mostrar transacciones de Telegram Stars también? → Fase 2
