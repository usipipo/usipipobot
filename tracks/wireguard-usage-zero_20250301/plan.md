# Implementation Plan: Consumo WireGuard siempre muestra 0.0GB

Track ID: `wireguard-usage-zero_20250301`
Created: 2025-03-01
Status: in-progress

## Overview
Corregir el bug donde el consumo de WireGuard siempre muestra 0.0GB debido a que se usa `key_name` en lugar de `external_id` al consultar métricas.

## Phase 1: Corrección del Bug

### Tasks

- [x] **Task 1.1**: Corregir identificador en admin_service.py
  - Cambiar `key.key_name` por `key.external_id` en línea 464
  - Verificar que el cambio es correcto

- [x] **Task 1.2**: Agregar logging de diagnóstico en client_wireguard.py
  - Agregar log debug al buscar cliente en configuración
  - Agregar log debug cuando se encuentra/no encuentra el peer
  - Agregar log info con métricas obtenidas

- [x] **Task 1.3**: Ejecutar tests existentes
  - Verificar que no hay regresiones
  - Corregir tests que usaban `update` en lugar de `save`

### Verification

- [x] **Verify 1.1**: Tests pasan sin errores (33 passed)
- [x] **Verify 1.2**: Flake8 no reporta errores

## Phase 2: Finalización

### Tasks

- [ ] **Task 2.1**: Commit de los cambios
- [ ] **Task 2.2**: Actualizar plan.md con SHAs
- [ ] **Task 2.3**: Cerrar Issue en GitHub

### Verification

- [ ] **Verify 2.1**: Todos los acceptance criteria cumplidos

## Checkpoints

| Phase   | Checkpoint SHA | Date       | Status   |
| ------- | -------------- | ---------- | -------- |
| Phase 1 |                |            | pending  |
| Phase 2 |                |            | pending  |
