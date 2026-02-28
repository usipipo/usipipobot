# Pay-as-You-Go Consumption Billing System

## Overview

Sistema de tarifa por consumo (postpago) que permite a los usuarios navegar sin límites de datos durante 30 días, pagando únicamente por los MB/GB consumidos al final del ciclo.

### Estrategia de Negocio

- **Precio competitivo**: $0.45 USD/GB (10% menos que el plan estándar de $0.50/GB)
- **Precisión**: Cobro exacto por MB consumido (no por GB completos)
- **Postpago**: El usuario consume primero, paga después
- **Auto-desactivación**: Por seguridad, se desactiva tras cada pago

### Flujo Principal

1. Usuario activa modo consumo (opt-in con advertencia explícita)
2. Se pausan los 5GB gratuitos mensuales
3. Usuario navega sin límites por 30 días
4. Al día 30: se genera factura, se bloquean las claves VPN
5. Usuario tiene 30 minutos para pagar desde que genera la factura
6. Al pagar: se limpia deuda, se reactivan claves, se desactiva modo consumo

## Functional Requirements

### FR-1: Activación del Modo Consumo

El usuario debe poder activar el modo consumo desde el menú de configuración.

- **Acceptance:**
  - Comando/botón disponible solo si el usuario no tiene deuda pendiente
  - Mensaje de advertencia explícito con términos y condiciones
  - Confirmación requerida (checkbox de aceptación de riesgo)
  - Al activar: se registra timestamp de activación

### FR-2: Seguimiento de Consumo

El sistema debe registrar cada byte consumido durante el modo consumo.

- **Acceptance:**
  - Registro acumulativo de MB consumidos
  - Cálculo en tiempo real del costo acumulado
  - Comando `/mi_consumo` disponible para consultar deuda actual
  - Precisión de conteo: a nivel de MB

### FR-3: Cierre de Ciclo (Día 30)

Al cumplirse 30 días desde la activación, el sistema debe cerrar el ciclo.

- **Acceptance:**
  - Cron job diario que verifica ciclos vencidos
  - Al detectar vencimiento:
    - Se bloquean todas las claves VPN del usuario
    - Se marca flag `has_pending_debt = true`
    - Se envía notificación al usuario con resumen de consumo
    - Se genera monto a pagar: `(MB_consumidos / 1024) * $0.45`

### FR-4: Generación y Pago de Factura

El usuario debe poder generar y pagar su factura.

- **Acceptance:**
  - Botón "Generar Factura" disponible solo cuando hay deuda
  - Al generar:
    - Se crea invoice con tiempo límite de 30 minutos
    - Se proporciona dirección de wallet para pago crypto
    - Se muestra QR de pago
  - Al pagar:
    - Se verifica transacción en blockchain
    - Se marca factura como pagada
    - Se limpia deuda del usuario
    - Se desactiva modo consumo automáticamente
    - Se reactivan claves VPN
    - Se reactivan los 5GB gratuitos mensuales

### FR-5: Desactivación Automática Post-Pago

Tras pagar la factura, el modo consumo debe desactivarse automáticamente.

- **Acceptance:**
  - Flag `consumption_mode_enabled` se establece a `false`
  - Contador de MB consumidos se resetea a 0
  - Usuario recibe notificación de desactivación
  - Usuario debe reactivar manualmente si desea otro ciclo

### FR-6: Bloqueo por Falta de Pago

Si el usuario no paga, todas sus claves deben permanecer bloqueadas.

- **Acceptance:**
  - Mientras `has_pending_debt = true`, las claves no funcionan
  - Usuario puede seguir generando nuevas facturas si expira una
  - Al pagar cualquier factura pendiente, se desbloquea todo

## Non-Functional Requirements

### NFR-1: Seguridad de Datos Financieros

Los datos de facturación deben almacenarse de forma segura.

- **Target:** Cifrado de datos sensibles en reposo
- **Verification:** Revisión de esquema de base de datos

### NFR-2: Precisión de Cálculo

Los cálculos de costo deben ser precisos hasta 6 decimales.

- **Target:** Sin errores de redondeo mayores a $0.000001
- **Verification:** Tests unitarios de cálculo

### NFR-3: Disponibilidad del Cron Job

El job de cierre de ciclo debe ejecutarse con 99.9% de disponibilidad.

- **Target:** Máximo 1 fallo por año
- **Verification:** Logs de ejecución

### NFR-4: Tiempo de Respuesta

La consulta de consumo debe responder en menos de 2 segundos.

- **Target:** < 2s para consulta de deuda
- **Verification:** Benchmarks de API

## Acceptance Criteria

- [ ] Usuario puede activar modo consumo desde menú
- [ ] Al activar, se muestra advertencia clara con términos
- [ ] Durante modo consumo, los 5GB free están pausados
- [ ] Usuario puede consultar consumo acumulado con `/mi_consumo`
- [ ] A los 30 días, las claves se bloquean automáticamente
- [ ] Usuario recibe notificación de cierre de ciclo
- [ ] Usuario puede generar factura con botón
- [ ] Factura tiene tiempo límite de 30 minutos
- [ ] Pago exitoso desbloquea claves y desactiva modo consumo
- [ ] Si no paga, las claves permanecen bloqueadas
- [ ] Modo consumo debe reactivarse manualmente tras cada ciclo

## Scope

### In Scope

- Entidad `ConsumptionBilling` para seguimiento de consumo
- Entidad `ConsumptionInvoice` para facturación
- Modificaciones a entidad `User` (nuevos flags)
- Servicio `ConsumptionBillingService` con lógica de negocio
- Servicio `ConsumptionInvoiceService` para facturación
- Handlers de Telegram para activación y consulta
- Cron job para cierre de ciclos
- Integración con sistema de pagos crypto existente
- Tests unitarios y de integración

### Out of Scope

- Soporte para múltiples monedas fiat
- Sistema de "promesas de pago" o prórrogas
- Notificaciones push (solo Telegram)
- Panel de administración para ver consumos
- Exportación de facturas a PDF

## Dependencies

### Internal

- Sistema de pagos crypto existente (`CryptoPaymentService`)
- Sistema de wallets (`WalletManagementService`)
- Repositorio de usuarios (`IUserRepository`)
- Sistema de VPN keys (`VpnKey` management)

### External

- API de TronDealer para pagos
- Servidor VPN para habilitar/deshabilitar keys
- Blockchain BSC para verificación de pagos

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Usuario activa sin leer advertencia | Alto | Checkbox obligatorio + mensaje extenso + confirmación doble |
| Usuario no entiende concepto postpago | Medio | Mensaje con ejemplo: "Si usas 2GB pagas $0.90" |
| Fallo en cron job de cierre | Alto | Logging extensivo + alerta manual + job idempotente |
| Usuario protesta por cobro inesperado | Alto | Sistema de desactivación automática post-pago |
| Bug en cálculo de consumo | Alto | Tests unitarios exhaustivos + auditoría de logs |
| Pago no detectado | Medio | Webhook + polling doble verificación |

## Open Questions

- [x] ¿Qué pasa si el usuario tiene paquetes prepago activos? - Se mantienen pero el consumo se cuenta para el modo consumo primero
- [x] ¿Se puede desactivar manualmente antes de los 30 días? - No, el ciclo es fijo de 30 días una vez activado
- [x] ¿Qué moneda de pago se acepta? - USDT en BSC (mismo sistema actual)
- [x] ¿Hay mínimo de consumo? - No, si usa 1MB paga por 1MB

## Data Model Overview

### ConsumptionBilling
- `id`: UUID
- `user_id`: int (FK)
- `started_at`: datetime
- `ended_at`: datetime (nullable)
- `mb_consumed`: decimal
- `total_cost_usd`: decimal
- `status`: enum (active, closed, paid)
- `created_at`: datetime

### ConsumptionInvoice
- `id`: UUID
- `billing_id`: UUID (FK)
- `user_id`: int (FK)
- `amount_usd`: decimal
- `wallet_address`: string
- `status`: enum (pending, paid, expired)
- `expires_at`: datetime
- `paid_at`: datetime (nullable)
- `transaction_hash`: string (nullable)

### User (new fields)
- `consumption_mode_enabled`: bool (default false)
- `has_pending_debt`: bool (default false)
- `current_billing_id`: UUID (nullable)
- `consumption_mode_activated_at`: datetime (nullable)

## Pricing Reference

| Concept | Valor |
|---------|-------|
| Precio por GB | $0.45 USD |
| Precio por MB | $0.000439 USD |
| Ciclo de facturación | 30 días |
| Tiempo límite factura | 30 minutos |
| Comparación plan estándar | 10% más barato por GB |

## User Flow Diagram

```
[Usuario] → Activa Modo Consumo → [Sistema]
                ↓
         [Advertencia + Confirmación]
                ↓
         [Modo Activo 30 días]
                ↓
    [Consumo libre - Sin límites]
                ↓
         [Día 30 - Cierre]
                ↓
    [Bloqueo de Keys + Notificación]
                ↓
    [Usuario Genera Factura]
                ↓
         ┌──────┴──────┐
         ↓             ↓
    [Paga]        [No Paga]
         ↓             ↓
   [Desbloqueo]   [Keys Bloqueadas]
   [Desactivación] [Espera pago]
   [5GB Reactivados]
```
