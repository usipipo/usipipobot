# Implementation Plan: Cancelar Modo de Consumo

Track ID: `cancel-consumption-mode_20250301`
Created: 2025-02-28
Status: in-progress

## Overview

Implementar la funcionalidad que permite a los usuarios cancelar el modo de tarifa por consumo antes de los 30 días del ciclo.

## Phase 1: Domain Layer Updates

### Tasks

- [ ] **Task 1.1**: Agregar método `can_cancel()` a entidad `ConsumptionBilling`
- [ ] **Task 1.2**: Agregar estado `CANCELLED` al flujo de estados permitidos
- [ ] **Task 1.3**: Verificar compatibilidad con entidad `User`

### Verification

- [ ] **Verify 1.1**: Entidad tiene método para validar cancelación
- [ ] **Verify 1.2**: Estados son consistentes

## Phase 2: Application Layer - Service Methods

### Tasks

- [ ] **Task 2.1**: Crear `can_cancel_consumption()` en `ConsumptionBillingService`
  - Validar que usuario tiene ciclo activo
  - Validar que no tiene deuda previa
  - Validar que ciclo no está ya cerrado/cancelado
- [ ] **Task 2.2**: Crear `cancel_consumption_mode()` en `ConsumptionBillingService`
  - Cerrar ciclo anticipadamente con estado CLOSED
  - Bloquear claves VPN del usuario
  - Marcar usuario con deuda pendiente
  - Calcular consumo final
- [ ] **Task 2.3**: Crear DTO `CancellationResult` para respuesta

### Verification

- [ ] **Verify 2.1**: Tests unitarios para validaciones
- [ ] **Verify 2.2**: Tests para flujo exitoso de cancelación
- [ ] **Verify 2.3**: Tests para casos edge (sin ciclo, ya cerrado, etc.)

## Phase 3: Telegram Bot - Handlers

### Tasks

- [ ] **Task 3.1**: Agregar botón "Cancelar Modo Consumo" al menú principal
- [ ] **Task 3.2**: Crear handler `start_cancellation()`
  - Verificar permisos con `can_cancel_consumption()`
  - Mostrar resumen de consumo actual
  - Pedir confirmación
- [ ] **Task 3.3**: Crear handler `confirm_cancellation()`
  - Ejecutar `cancel_consumption_mode()`
  - Mostrar resultado
  - Ofrecer generar factura inmediatamente
- [ ] **Task 3.4**: Registrar callbacks en `get_consumption_callback_handlers()`
  - `consumption_cancel`
  - `consumption_confirm_cancel`

### Verification

- [ ] **Verify 3.1**: Handlers responden correctamente
- [ ] **Verify 3.2**: Flujo de cancelación es intuitivo
- [ ] **Verify 3.3**: Mensajes de error son claros

## Phase 4: Keyboards Updates

### Tasks

- [ ] **Task 4.1**: Agregar botón "Cancelar Modo Consumo" a `consumption_main_menu()`
  - Solo visible cuando hay ciclo activo
- [ ] **Task 4.2**: Crear `cancellation_confirmation()` keyboard
  - Botones: Confirmar cancelación / Volver
- [ ] **Task 4.3**: Crear `cancel_success_keyboard()` para post-cancelación
  - Botón: Generar Factura / Volver al menú

### Verification

- [ ] **Verify 4.1**: Keyboards se renderizan correctamente
- [ ] **Verify 4.2**: Flujo de botones es lógico

## Phase 5: Messages Updates

### Tasks

- [ ] **Task 5.1**: Verificar mensajes existentes en `Cancellation` class
- [ ] **Task 5.2**: Agregar mensajes faltantes si es necesario
- [ ] **Task 5.3**: Asegurar que precios son dinámicos

### Verification

- [ ] **Verify 5.1**: Mensajes son claros y completos
- [ ] **Verify 5.2**: Sin hardcoding de precios

## Phase 6: Testing

### Tasks

- [ ] **Task 6.1**: Crear tests para `can_cancel_consumption()`
- [ ] **Task 6.2**: Crear tests para `cancel_consumption_mode()`
- [ ] **Task 6.3**: Crear tests para handlers
- [ ] **Task 6.4**: Ejecutar test suite completo

### Verification

- [ ] **Verify 6.1**: Todos los tests pasan
- [ ] **Verify 6.2**: Cobertura >= 80% para nueva funcionalidad

## Phase 7: Integration & Documentation

### Tasks

- [ ] **Task 7.1**: Verificar integración con servicio de facturación
- [ ] **Task 7.2**: Actualizar CHANGELOG.md
- [ ] **Task 7.3**: Actualizar tracks.md

### Verification

- [ ] **Verify 7.1**: Flujo end-to-end funciona
- [ ] **Verify 7.2**: Documentación actualizada

## Checkpoints

| Phase   | Checkpoint SHA | Date       | Status   |
|---------|----------------|------------|----------|
| Phase 1 |                |            | pending  |
| Phase 2 |                |            | pending  |
| Phase 3 |                |            | pending  |
| Phase 4 |                |            | pending  |
| Phase 5 |                |            | pending  |
| Phase 6 |                |            | pending  |
| Phase 7 |                |            | pending  |

## Notes

- El estado `CANCELLED` existe en `BillingStatus` pero no se usa
- Se usará `CLOSED` para mantener consistencia con flujo existente
- La facturación post-cancelación usa el mismo flujo que cierre normal
