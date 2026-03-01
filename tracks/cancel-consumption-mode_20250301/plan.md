# Implementation Plan: Cancelar Modo de Consumo

Track ID: `cancel-consumption-mode_20250301`
Created: 2025-02-28
Status: completed

## Overview

Implementar la funcionalidad que permite a los usuarios cancelar el modo de tarifa por consumo antes de los 30 días del ciclo.

## Phase 1: Domain Layer Updates

### Tasks

- [x] **Task 1.1**: Agregar método `can_cancel()` a entidad `ConsumptionBilling`
- [x] **Task 1.2**: Agregar estado `CANCELLED` al flujo de estados permitidos
- [x] **Task 1.3**: Verificar compatibilidad con entidad `User`

### Verification

- [x] **Verify 1.1**: Entidad tiene método para validar cancelación
- [x] **Verify 1.2**: Estados son consistentes

## Phase 2: Application Layer - Service Methods

### Tasks

- [x] **Task 2.1**: Crear `can_cancel_consumption()` en `ConsumptionBillingService`
  - Validar que usuario tiene ciclo activo
  - Validar que no tiene deuda previa
  - Validar que ciclo no está ya cerrado/cancelado
- [x] **Task 2.2**: Crear `cancel_consumption_mode()` en `ConsumptionBillingService`
  - Cerrar ciclo anticipadamente con estado CLOSED
  - Bloquear claves VPN del usuario
  - Marcar usuario con deuda pendiente
  - Calcular consumo final
- [x] **Task 2.3**: Crear DTO `CancellationResult` para respuesta

### Verification

- [x] **Verify 2.1**: Tests unitarios para validaciones
- [x] **Verify 2.2**: Tests para flujo exitoso de cancelación
- [x] **Verify 2.3**: Tests para casos edge (sin ciclo, ya cerrado, etc.)

## Phase 3: Telegram Bot - Handlers

### Tasks

- [x] **Task 3.1**: Agregar botón "Cancelar Modo Consumo" al menú principal
- [x] **Task 3.2**: Crear handler `start_cancellation()`
  - Verificar permisos con `can_cancel_consumption()`
  - Mostrar resumen de consumo actual
  - Pedir confirmación
- [x] **Task 3.3**: Crear handler `confirm_cancellation()`
  - Ejecutar `cancel_consumption_mode()`
  - Mostrar resultado
  - Ofrecer generar factura inmediatamente
- [x] **Task 3.4**: Registrar callbacks en `get_consumption_callback_handlers()`
  - `consumption_cancel`
  - `consumption_confirm_cancel`

### Verification

- [x] **Verify 3.1**: Handlers responden correctamente
- [x] **Verify 3.2**: Flujo de cancelación es intuitivo
- [x] **Verify 3.3**: Mensajes de error son claros

## Phase 4: Keyboards Updates

### Tasks

- [x] **Task 4.1**: Agregar botón "Cancelar Modo Consumo" a `consumption_main_menu()`
  - Solo visible cuando hay ciclo activo
- [x] **Task 4.2**: Crear `cancellation_confirmation()` keyboard
  - Botones: Confirmar cancelación / Volver
- [x] **Task 4.3**: Crear `cancel_success_keyboard()` para post-cancelación
  - Botón: Generar Factura / Volver al menú

### Verification

- [x] **Verify 4.1**: Keyboards se renderizan correctamente
- [x] **Verify 4.2**: Flujo de botones es lógico

## Phase 5: Messages Updates

### Tasks

- [x] **Task 5.1**: Verificar mensajes existentes en `Cancellation` class
- [x] **Task 5.2**: Agregar mensajes faltantes si es necesario
- [x] **Task 5.3**: Asegurar que precios son dinámicos

### Verification

- [x] **Verify 5.1**: Mensajes son claros y completos
- [x] **Verify 5.2**: Sin hardcoding de precios

## Phase 6: Testing

### Tasks

- [x] **Task 6.1**: Crear tests para `can_cancel_consumption()`
- [x] **Task 6.2**: Crear tests para `cancel_consumption_mode()`
- [x] **Task 6.3**: Crear tests para handlers (cobertura indirecta)
- [x] **Task 6.4**: Ejecutar test suite completo

### Verification

- [x] **Verify 6.1**: Todos los tests pasan (319 passed)
- [x] **Verify 6.2**: 10 tests nuevos para funcionalidad

## Phase 7: Integration & Documentation

### Tasks

- [x] **Task 7.1**: Verificar integración con servicio de facturación
- [x] **Task 7.2**: Commit y merge a develop
- [x] **Task 7.3**: Actualizar plan.md

### Verification

- [x] **Verify 7.1**: Flujo end-to-end funciona
- [x] **Verify 7.2**: Documentación actualizada

## Checkpoints

| Phase   | Checkpoint SHA | Date       | Status     |
|---------|----------------|------------|------------|
| Phase 1 | d301a91        | 2025-02-28 | completed  |
| Phase 2 | 01b18e7        | 2025-02-28 | completed  |
| Phase 3 | 01b18e7        | 2025-02-28 | completed  |
| Phase 4 | 01b18e7        | 2025-02-28 | completed  |
| Phase 5 | 01b18e7        | 2025-02-28 | completed  |
| Phase 6 | 01b18e7        | 2025-02-28 | completed  |
| Phase 7 | 53d4550        | 2025-02-28 | completed  |

## Summary

**Implementado:**
- ✅ Domain Layer: Validaciones y estados
- ✅ Application Layer: Servicios con cancelación
- ✅ Telegram Handlers: Flujo completo de cancelación
- ✅ Keyboards: UI para cancelación
- ✅ Messages: Mensajes dinámicos
- ✅ Tests: 10 tests unitarios nuevos
- ✅ Merge: Completado a develop

**Flujo de Cancelación:**
1. Usuario ve botón "Cancelar Modo Consumo" en menú
2. Sistema muestra resumen de consumo y confirma
3. Al confirmar: ciclo cerrado, claves bloqueadas, deuda marcada
4. Usuario puede generar factura inmediatamente

**Tests:** 319 passed, 6 warnings
