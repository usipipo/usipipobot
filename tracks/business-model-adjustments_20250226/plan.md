# Implementation Plan: Ajustes al Modelo de Negocio

Track ID: `business-model-adjustments_20250226`
Created: 2025-02-26
Status: pending

## Overview

Plan de implementación para ajustes tácticos al modelo de negocio: reducción de límites de datos, restricción por tipo de servidor, pagos crypto para slots, y sistema de facturación con notificaciones.

## Phase 1: Configuración y Límites

### Tasks

- [ ] **Task 1.1**: Cambiar límite de datos por clave a 5GB
  - Modificar `config.py`: `FREE_PLAN_DATA_LIMIT_GB = 5`
  - Actualizar `domain/entities/user.py`: default `free_data_limit_bytes = 5 * 1024**3`
  - Actualizar tests relacionados

- [ ] **Task 1.2**: Implementar validación de una clave por servidor
  - Modificar `domain/entities/user.py`: Agregar método `get_key_count_by_type()`
  - Modificar `domain/entities/user.py`: Actualizar `can_create_more_keys()` para validar por tipo
  - Modificar `application/services/vpn_service.py`: Validar tipo en `create_key()`
  - Actualizar mensajes de error para ser claros sobre el límite por tipo

### Verification

- [ ] **Verify 1.1**: Tests pasan con nuevo límite de 5GB
- [ ] **Verify 1.2**: Usuario no puede crear 2 claves del mismo tipo

## Phase 2: Pago con Crypto para Slots

### Tasks

- [ ] **Task 2.1**: Crear método de compra de slots con crypto
  - Agregar `purchase_key_slots_crypto()` en `application/services/data_package_service.py`
  - Crear orden crypto con tipo "slots" para diferenciar de paquetes

- [ ] **Task 2.2**: Agregar handler para pago de slots con crypto
  - Crear `pay_slots_with_crypto()` en `telegram_bot/features/buy_gb/handlers_buy_gb.py`
  - Agregar callback handler `pay_slots_crypto_`
  - Mostrar dirección de billetera y monto en USDT

- [ ] **Task 2.3**: Actualizar teclados para slots
  - Modificar `telegram_bot/features/buy_gb/keyboards_buy_gb.py`
  - Agregar botón "💰 Pagar con USDT" en menú de slots
  - Actualizar `slots_menu()` para incluir opción de pago crypto

- [ ] **Task 2.4**: Procesar pago de slots vía webhook
  - Modificar `crypto_payment_service.py` para detectar órdenes de tipo slot
  - Llamar `purchase_key_slots()` al confirmar pago

### Verification

- [ ] **Verify 2.1**: Usuario puede iniciar pago de slots con crypto
- [ ] **Verify 2.2**: Al confirmar pago crypto, se incrementan los slots correctamente

## Phase 3: Sistema de Notificaciones y Expiración

### Tasks

- [ ] **Task 3.1**: Crear job de expiración de órdenes
  - Crear `infrastructure/jobs/crypto_order_expiration_job.py`
  - Verificar órdenes pending con `expires_at < now()`
  - Marcar como `EXPIRED` en base de datos

- [ ] **Task 3.2**: Enviar notificación de expiración
  - Integrar con bot de Telegram para enviar mensaje
  - Usar `application/services/common/container.py` para obtener bot
  - Mensaje informativo sobre orden vencida

- [ ] **Task 3.3**: Registrar órdenes expiradas en historial
  - Asegurar que `mark_expired()` guarda timestamp
  - Agregar método `get_user_transaction_history()` en crypto_payment_service
  - Incluir órdenes expiradas en historial

### Verification

- [ ] **Verify 3.1**: Job marca órdenes vencidas correctamente
- [ ] **Verify 3.2**: Usuario recibe notificación cuando orden expira

## Phase 4: Generación de QR para Pagos

### Tasks

- [ ] **Task 4.1**: Agregar generador de QR de pago
  - Extender `utils/qr_generator.py` con `generate_payment_qr()`
  - Formato: dirección + monto (formato EIP-681 o similar)
  - Guardar imagen temporal

- [ ] **Task 4.2**: Integrar QR en mensajes de pago
  - Modificar `pay_with_crypto()` para generar y enviar QR
  - Modificar `pay_slots_with_crypto()` para generar y enviar QR
  - Enviar QR como imagen adjunta

- [ ] **Task 4.3**: Limpiar archivos QR temporales
  - Agregar cleanup de archivos QR antiguos
  - Ejecutar periódicamente o al iniciar

### Verification

- [ ] **Verify 4.1**: QR generado contiene dirección y monto correctos
- [ ] **Verify 4.2**: QR es escaneable por wallets móviles

## Phase 5: Finalización y Testing

### Tasks

- [ ] **Task 5.1**: Ejecutar tests existentes
  - `pytest -v` - todos los tests deben pasar
  - Corregir tests afectados por cambios de límite

- [ ] **Task 5.2**: Ejecutar linting y type checking
  - `flake8 .` - sin errores
  - `black .` - código formateado
  - `mypy .` - sin errores de tipo

- [ ] **Task 5.3**: Verificar manualmente flujos críticos
  - Crear clave Outline (debe permitir 1)
  - Intentar crear segunda Outline (debe bloquear)
  - Crear clave WireGuard (debe permitir)
  - Verificar límite de 5GB en nueva clave

- [ ] **Task 5.4**: Documentar cambios
  - Actualizar CHANGELOG.md
  - Agregar notas sobre cambios de modelo de negocio

### Verification

- [ ] **Verify 5.1**: Todos los tests pasan
- [ ] **Verify 5.2**: Linting y type checking sin errores
- [ ] **Verify 5.3**: Flujos manuales funcionan correctamente

## Checkpoints

| Phase | Checkpoint SHA | Date | Status |
|-------|---------------|------|--------|
| Phase 1 | | | pending |
| Phase 2 | | | pending |
| Phase 3 | | | pending |
| Phase 4 | | | pending |
| Phase 5 | | | pending |
