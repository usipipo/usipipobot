# Implementation Plan: Actualizar Precios a Estrellas de Telegram

Track ID: `update-prices-telegram-stars_20250227`
Created: 2025-02-27
Status: pending

## Overview

Actualizar los precios de paquetes de datos y slots de claves para usar la tasa correcta de 100 estrellas = 1 USDT.

## Phase 1: Actualizar Precios en Data Package Service

### Tasks

- [ ] **Task 1.1**: Actualizar precios de PACKAGE_OPTIONS
  - Abrir `application/services/data_package_service.py`
  - Cambiar Básico: 50 → 500 stars
  - Cambiar Estándar: 65 → 650 stars
  - Cambiar Avanzado: 85 → 850 stars
  - Cambiar Premium: 110 → 1100 stars

- [ ] **Task 1.2**: Actualizar precios de SLOT_OPTIONS
  - En el mismo archivo
  - Cambiar +1 Clave: 25 → 250 stars
  - Cambiar +3 Claves: 60 → 600 stars
  - Cambiar +5 Claves: 90 → 900 stars

### Verification

- [ ] **Verify 1.1**: Verificar cambios en el archivo
  - Run: `grep -A 5 "PACKAGE_OPTIONS" application/services/data_package_service.py`
  - Expected: Ver precios actualizados (500, 650, 850, 1100)

## Phase 2: Actualizar Tests Relacionados

### Tasks

- [ ] **Task 2.1**: Actualizar test de data_package_service
  - Abrir `tests/application/services/test_data_package_service.py`
  - Buscar valores de estrellas hardcodeados (50, 65, 85, 110)
  - Actualizar a nuevos valores (500, 650, 850, 1100)

### Verification

- [ ] **Verify 2.1**: Ejecutar tests actualizados
  - Run: `pytest tests/application/services/test_data_package_service.py -v`
  - Expected: Todos los tests pasan

## Phase 3: Actualizar Conversión USDT en Handlers

### Tasks

- [ ] **Task 3.1**: Actualizar conversión en handlers_buy_gb.py
  - Abrir `telegram_bot/features/buy_gb/handlers_buy_gb.py`
  - Buscar `stars / 10` y cambiar a `stars / 100`
  - Líneas aproximadas: 169, 389, 521

### Verification

- [ ] **Verify 3.1**: Verificar cambios de conversión
  - Run: `grep -n "stars /" telegram_bot/features/buy_gb/handlers_buy_gb.py`
  - Expected: Todas las conversiones usan `stars / 100`

## Phase 4: Finalización

### Tasks

- [ ] **Task 4.1**: Ejecutar todos los tests
  - Run: `pytest tests/ -v --tb=short`
  - Expected: Todos los tests pasan

- [ ] **Task 4.2**: Verificar linting
  - Run: `flake8 application/services/data_package_service.py telegram_bot/features/buy_gb/handlers_buy_gb.py`
  - Expected: Sin errores

- [ ] **Task 4.3**: Verificar type checking
  - Run: `mypy application/services/data_package_service.py`
  - Expected: Sin errores

### Verification

- [ ] **Verify 4.1**: All tests pass
- [ ] **Verify 4.2**: No linting errors
- [ ] **Verify 4.3**: No type errors

## Checkpoints

| Phase | Checkpoint SHA | Date | Status |
|-------|----------------|------|--------|
| Phase 1 | | | pending |
| Phase 2 | | | pending |
| Phase 3 | | | pending |
| Phase 4 | | | pending |
