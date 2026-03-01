# Cancelar Modo de Consumo en Cualquier Momento

## Overview

Implementar la funcionalidad que permite a los usuarios cancelar el modo de tarifa por consumo antes de que terminen los 30 días del ciclo. Al cancelar, el ciclo se cierra anticipadamente, se genera la factura correspondiente al consumo acumulado hasta ese momento, y el usuario debe pagar para continuar usando el servicio.

### Contexto del Cambio

En la implementación original del sistema pay-as-you-go, los usuarios NO podían cancelar el modo consumo antes de los 30 días (ver spec original: "¿Se puede desactivar manualmente antes de los 30 días? - No, el ciclo es fijo de 30 días una vez activado").

Este feature permite mayor flexibilidad a los usuarios que desean cambiar de plan o detener el consumo antes del ciclo completo.

### Flujo Principal

1. Usuario tiene modo consumo activo
2. Usuario solicita cancelar modo consumo desde el menú
3. Sistema muestra confirmación con resumen de consumo actual
4. Al confirmar:
   - Se cierra el ciclo de facturación anticipadamente
   - Se marca al usuario con deuda pendiente
   - Se bloquean las claves VPN
   - Se muestra opción para generar factura inmediata
5. Usuario paga la factura generada
6. Al pagar: se desbloquean claves, se desactiva modo consumo, se reactivan 5GB free

## Functional Requirements

### FR-1: Solicitud de Cancelación

El usuario debe poder solicitar la cancelación del modo consumo en cualquier momento.

- **Acceptance:**
  - Botón "Cancelar Modo Consumo" disponible solo si hay ciclo activo
  - Verificación de que el usuario tiene modo consumo activo
  - No permitir cancelación si ya hay deuda pendiente
  - No permitir cancelación si el ciclo ya está cerrado

### FR-2: Confirmación de Cancelación

El sistema debe mostrar un resumen antes de proceder con la cancelación.

- **Acceptance:**
  - Mostrar consumo acumulado hasta el momento
  - Mostrar costo calculado hasta el momento
  - Mostrar días transcurridos del ciclo
  - Advertencia clara de que las claves se bloquearán
  - Requerir confirmación explícita del usuario

### FR-3: Cierre Anticipado de Ciclo

Al confirmar la cancelación, el ciclo debe cerrarse anticipadamente.

- **Acceptance:**
  - Estado del billing cambia a CLOSED
  - Fecha de fin se registra como el momento de cancelación
  - Cálculo final de costo basado en MB consumidos
  - Usuario se marca con has_pending_debt = true
  - Modo consumo se mantiene activo hasta que se pague (para tracking)

### FR-4: Bloqueo de Claves Post-Cancelación

Las claves VPN deben bloquearse tras la cancelación hasta el pago.

- **Acceptance:**
  - Todas las claves del usuario se bloquean al cancelar
  - Usuario no puede crear nuevas claves mientras tenga deuda
  - Mensaje claro indicando que debe pagar para desbloquear

### FR-5: Generación de Factura Post-Cancelación

El usuario debe poder generar y pagar la factura inmediatamente tras cancelar.

- **Acceptance:**
  - Botón "Generar Factura" disponible tras cancelación
  - Factura generada con el consumo acumulado hasta la cancelación
  - Mismo flujo de pago que el cierre normal de ciclo
  - Al pagar: desbloqueo de claves y desactivación completa del modo consumo

### FR-6: Notificación de Cancelación

El usuario debe recibir notificación confirmando la cancelación.

- **Acceptance:**
  - Mensaje de confirmación con resumen del ciclo cancelado
  - Indicación clara de que las claves están bloqueadas
  - Instrucciones para generar factura y pagar

## Non-Functional Requirements

### NFR-1: Precisión de Cálculo

El cálculo del costo al cancelar debe ser idéntico al del cierre normal.

- **Target:** Sin diferencias en el monto calculado
- **Verification:** Tests comparando cálculo de cancelación vs cierre normal

### NFR-2: Tiempo de Respuesta

La operación de cancelación debe completarse en menos de 3 segundos.

- **Target:** < 3s desde confirmación hasta bloqueo de claves
- **Verification:** Benchmarks de la operación completa

### NFR-3: Idempotencia

La cancelación debe ser idempotente (no generar efectos duplicados).

- **Target:** Llamadas múltiples no causan datos inconsistentes
- **Verification:** Tests de idempotencia

## Acceptance Criteria

- [ ] Usuario puede ver botón de cancelar modo consumo cuando tiene ciclo activo
- [ ] Al presionar cancelar, se muestra confirmación con resumen de consumo
- [ ] Al confirmar, el ciclo se cierra anticipadamente
- [ ] Las claves VPN se bloquean tras la cancelación
- [ ] Usuario puede generar factura inmediatamente tras cancelar
- [ ] El pago de la factura desbloquea claves y desactiva modo consumo
- [ ] Usuario puede reactivar modo consumo tras pagar (nuevo ciclo)
- [ ] No se permite cancelar si ya hay deuda pendiente
- [ ] No se permite cancelar si no hay ciclo activo

## Scope

### In Scope

- Nuevo método `cancel_consumption_mode` en `ConsumptionBillingService`
- Nuevo método `can_cancel_consumption` para validaciones
- Nuevo handler `start_cancellation` en `ConsumptionHandler`
- Nuevo handler `confirm_cancellation` en `ConsumptionHandler`
- Nuevos mensajes para flujo de cancelación
- Nuevos teclados para flujo de cancelación
- Tests unitarios para la nueva funcionalidad
- Actualización de mensajes existentes para incluir opción de cancelar

### Out of Scope

- Cambios al sistema de precios o tarifas
- Modificaciones al cron job de cierre automático
- Cambios al flujo de pago existente
- Reembolsos o ajustes parciales
- Notificaciones push externas a Telegram

## Dependencies

### Internal

- `ConsumptionBillingService` - servicio existente a extender
- `ConsumptionVpnIntegrationService` - para bloqueo de claves
- `ConsumptionInvoiceService` - para generación de factura post-cancelación
- `IConsumptionBillingRepository` - repositorio existente
- Entidad `ConsumptionBilling` - ya tiene estado CANCELLED (sin usar)

### External

- Servidor VPN para bloqueo de claves
- Sistema de notificaciones de Telegram

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Usuario cancela accidentalmente | Medio | Confirmación explícita con resumen detallado |
| Inconsistencia en cálculo de costo | Alto | Reutilizar lógica existente de close_cycle |
| Race condition entre cancelación y cron job | Medio | Validar estado antes de operar, manejar errores gracefully |
| Usuario confundido por flujo post-cancelación | Medio | Mensajes claros guiando al siguiente paso (generar factura) |

## Open Questions

- [x] ¿El estado CANCELLED existente en BillingStatus se usa? - No, estaba preparado para futuro
- [x] ¿Se debe permitir cancelar con consumo 0 MB? - Sí, pero mostrar mensaje informativo
- [x] ¿Qué pasa si el usuario no paga tras cancelar? - Mismo comportamiento que cierre normal: claves bloqueadas hasta pago

## Data Model Changes

No se requieren cambios al data model. El estado `CANCELLED` ya existe en `BillingStatus` pero no se usa actualmente. Se usará `CLOSED` para mantener consistencia con el flujo existente.

## API/Interface Changes

### Nuevos métodos en ConsumptionBillingService:

```python
async def can_cancel_consumption(
    self, user_id: int, current_user_id: int
) -> Tuple[bool, Optional[str]]

async def cancel_consumption_mode(
    self, user_id: int, current_user_id: int
) -> CancellationResult
```

### Nuevos handlers:

```python
async def start_cancellation(update, context)
async def confirm_cancellation(update, context)
```

### Nuevos callbacks:

- `consumption_cancel` - iniciar cancelación
- `consumption_confirm_cancel` - confirmar cancelación

## User Flow Diagram

```
[Usuario con modo consumo activo]
           ↓
    [Presiona "Cancelar Modo Consumo"]
           ↓
    [Pantalla de Confirmación]
    • Resumen de consumo
    • Costo calculado
    • Advertencia de bloqueo
           ↓
    ┌──────┴──────┐
    ↓             ↓
[Confirma]    [Cancela]
    ↓             ↓
[Cierre       [Vuelve a
Anticipado]    menú]
    ↓
[Keys Bloqueadas]
    ↓
[Ofrecer Generar Factura]
    ↓
    ┌──────┴──────┐
    ↓             ↓
[Genera]      [No genera]
Factura]      [queda en]
    ↓           [deuda]
[Pago]            ↓
    ↓        [Puede generar
[Desbloqueo]   después]
y Reactivación
```

## Pricing Reference

Sin cambios - se mantiene la misma tarifa:

| Concept | Value |
|---------|-------|
| Precio por GB | $0.45 USD |
| Precio por MB | $0.000439 USD |
| Tiempo límite factura | 30 minutos |

Track ID: `cancel-consumption-mode_20250301`
