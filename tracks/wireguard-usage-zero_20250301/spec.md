# Bug: Consumo WireGuard siempre muestra 0.0GB

## Overview
Las claves WireGuard siempre muestran 0.0GB de consumo independientemente del tráfico real generado por el usuario. El mensaje muestra "Consumo: 0.0/5.0GB (0%)" aunque el usuario haya utilizado datos.

## Functional Requirements

### FR-1: Corregir identificador en admin_service
El método `get_key_usage_stats` en `admin_service.py` usa `key.key_name` en lugar de `key.external_id` al consultar métricas de WireGuard.

- Acceptance: El método debe usar `key.external_id` para obtener métricas correctas

### FR-2: Agregar logging de diagnóstico
Agregar logs detallados en `get_peer_metrics` para facilitar debugging de problemas de sincronización.

- Acceptance: Los logs deben mostrar el client_name buscado y si fue encontrado en la configuración

## Acceptance Criteria

- [ ] Las claves WireGuard muestran el consumo real de datos
- [ ] El admin_service usa `external_id` correctamente
- [ ] Hay logs de debug para diagnóstico de métricas
- [ ] Los tests existentes continúan pasando

## Scope

### In Scope
- Corregir bug en `admin_service.py` línea 464
- Agregar logging en `client_wireguard.py`
- Verificar flujo de sincronización de uso

### Out of Scope
- Cambios en la lógica de sincronización periódica (usage_sync.py)
- Modificaciones al esquema de base de datos
- Cambios en la UI de Telegram

## Dependencies

### Internal
- `application/services/admin_service.py`
- `infrastructure/api_clients/client_wireguard.py`

## Root Cause Analysis

El bug está en `application/services/admin_service.py:464`:
```python
metrics = await self.wireguard_client.get_peer_metrics(key.key_name)  # BUG
```

Debería ser:
```python
metrics = await self.wireguard_client.get_peer_metrics(key.external_id)
```

Esto causa que se busque el nombre descriptivo de la clave (ej: "mowgliwg") en lugar del identificador técnico (ej: "tg_123456_abc1") que está guardado en el archivo de configuración de WireGuard.

## Notes

- El flujo principal de sincronización en `vpn_service.py` usa correctamente `key.external_id`
- Este bug solo afecta la visualización en el panel de administración y mensajes de detalle
- El consumo real se sincroniza correctamente por el job de sincronización
