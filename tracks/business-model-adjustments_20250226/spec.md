# Ajustes al Modelo de Negocio - Límites, Pagos y Facturación

## Overview

Este track implementa ajustes tácticos al modelo de negocio del bot VPN uSipipo para optimizar la oferta gratuita y mejorar el flujo de pagos con criptomonedas.

## Functional Requirements

### FR-1: Reducir límite de datos por clave a 5GB

**Descripción:** Cambiar el límite de datos por clave del plan gratuito de 10GB a 5GB, manteniendo 10GB totales entre las 2 claves.

**Cambios requeridos:**
- `config.py`: `FREE_PLAN_DATA_LIMIT_GB` de 10 a 5
- `domain/entities/user.py`: `free_data_limit_bytes` default a 5GB (una clave)
- Verificar que el límite se aplica correctamente al crear claves

- **Acceptance:** Al crear una clave nueva, el límite de datos es 5GB en lugar de 10GB

### FR-2: Limitar una clave por servidor

**Descripción:** Restringir la creación de claves para que un usuario solo pueda tener 1 clave Outline y 1 clave WireGuard (máximo 2 en total, una de cada tipo).

**Cambios requeridos:**
- `domain/entities/user.py`: Modificar `can_create_more_keys()` para verificar tipo de clave existente
- `application/services/vpn_service.py`: Modificar `create_key()` para validar que no existe clave del mismo tipo
- `application/services/vpn_service.py`: Modificar `can_user_create_key()` para considerar tipos de claves

- **Acceptance:** Un usuario con 1 clave Outline no puede crear otra Outline, pero sí puede crear WireGuard

### FR-3: Agregar pago con crypto para compra de slots

**Descripción:** Permitir pagar con criptomonedas (USDT) para comprar slots de claves adicionales, similar a como funciona con los paquetes de datos.

**Cambios requeridos:**
- `application/services/data_package_service.py`: Crear método `purchase_key_slots_crypto()`
- `telegram_bot/features/buy_gb/handlers_buy_gb.py`: Agregar handler `pay_slots_with_crypto()`
- `telegram_bot/features/buy_gb/keyboards_buy_gb.py`: Agregar botón para pago con crypto en slots
- Crear flujo similar a `pay_with_crypto()` para slots

- **Acceptance:** Usuario puede seleccionar "Pagar con USDT" al comprar slots y recibe dirección de billetera

### FR-4: Notificación de expiración de orden de pago

**Descripción:** Notificar al usuario cuando pasen 30 minutos y no haya realizado el pago de su orden.

**Cambios requeridos:**
- `infrastructure/jobs/`: Crear job `crypto_order_expiration_job.py`
- Verificar órdenes pending con `expires_at` vencido
- Enviar notificación por Telegram al usuario
- Marcar orden como `EXPIRED`

- **Acceptance:** Usuario recibe mensaje de Telegram cuando su orden expira por falta de pago

### FR-5: Generar factura con código QR

**Descripción:** Generar una factura visual con código QR para pagos con crypto, mostrando monto y dirección.

**Cambios requeridos:**
- `utils/qr_generator.py`: Agregar método `generate_payment_qr()` para datos de pago
- `telegram_bot/features/buy_gb/handlers_buy_gb.py`: Generar y enviar QR en el mensaje de pago
- Incluir: dirección de billetera, monto, red (BSC)

- **Acceptance:** Usuario recibe imagen con código QR escaneable para realizar el pago

### FR-6: Cancelar orden vencida y registrar en historial

**Descripción:** Cuando una orden expira, cancelarla automáticamente y registrar en el historial de transacciones como "vencida".

**Cambios requeridos:**
- `domain/entities/crypto_order.py`: Asegurar que `mark_expired()` funciona correctamente
- `infrastructure/jobs/crypto_order_expiration_job.py`: Al expirar, guardar en historial
- `application/services/crypto_payment_service.py`: Agregar método `get_user_transaction_history()`
- Considerar agregar campo `expired_at` o similar para tracking

- **Acceptance:** Órdenes expiradas aparecen en el historial del usuario con estado "vencida"

## Non-Functional Requirements

### NFR-1: Mantener compatibilidad hacia atrás

- Los usuarios existentes no deben perder sus claves actuales
- Los cambios solo aplican a nuevas claves creadas

### NFR-2: Performance

- El job de expiración debe ejecutarse eficientemente cada minuto
- No debe afectar el rendimiento del bot

### NFR-3: UX

- Mensajes claros cuando se alcanza el límite por tipo de servidor
- QR debe ser fácilmente escaneable

## Acceptance Criteria

- [ ] Usuario con plan gratuito tiene límite de 5GB por clave nueva
- [ ] Usuario solo puede crear 1 clave Outline y 1 WireGuard
- [ ] Usuario puede pagar slots con USDT usando dirección de billetera
- [ ] Usuario recibe notificación cuando orden expira (30 min)
- [ ] Usuario recibe código QR para facilitar el pago
- [ ] Órdenes expiradas aparecen en historial con estado "vencida"

## Scope

### In Scope

- Cambios en configuración de límites
- Validación de tipos de claves
- Pago con crypto para slots
- Sistema de notificación de expiración
- Generación de QR para pagos
- Registro de órdenes expiradas

### Out of Scope

- Cambios a paquetes de datos pagados
- Modificaciones al sistema de referidos
- Cambios en métodos de pago con Stars

## Dependencies

### Internal

- TronDealer API para pagos crypto
- Sistema de jobs existente
- Repositorio de órdenes crypto

### External

- Ninguna dependencia externa nueva

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Usuarios existentes con >2 claves del mismo tipo | Medium | Solo validar para nuevas claves, no afectar existentes |
| Cambio de límite de 10GB a 5GB puede confundir | Low | Comunicar claramente en mensajes del bot |
| Job de expiración puede fallar silenciosamente | Medium | Agregar logging y alertas |

## Open Questions

- [ ] ¿Debe el QR incluir el monto exacto o solo la dirección?
- [ ] ¿Cuál es el formato preferido para el historial de transacciones?
