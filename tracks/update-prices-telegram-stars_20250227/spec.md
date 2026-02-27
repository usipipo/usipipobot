# Actualizar Precios a Estrellas de Telegram

## Overview

Corregir los precios de los productos (paquetes de datos y slots de claves) para reflejar correctamente la tasa de conversión de **100 estrellas = 1 USDT** en lugar de la tasa actual incorrecta de 10 estrellas = 1 USDT.

## Contexto

El usuario ha determinado que los precios actuales en USDT son justos y correctos para el modelo de negocio:
- Paquetes de datos: 5-11 USDT según el tamaño
- Slots de claves: 2.5-9 USDT según la cantidad

Sin embargo, la conversión a estrellas de Telegram está usando una tasa incorrecta (10 stars/USDT en lugar de 100 stars/USDT), resultando en precios 10 veces más baratos de lo que deberían ser.

## Functional Requirements

### FR-1: Actualizar Precios de Paquetes de Datos

Actualizar `PACKAGE_OPTIONS` en `application/services/data_package_service.py` para usar la tasa correcta de 100 stars/USDT:

- **Básico (10 GB)**: 50 stars → 500 stars
- **Estándar (25 GB)**: 65 stars → 650 stars
- **Avanzado (50 GB)**: 85 stars → 850 stars
- **Premium (100 GB)**: 110 stars → 1100 stars

- **Acceptance:** Los precios en estrellas reflejan correctamente 100 stars = 1 USDT

### FR-2: Actualizar Precios de Slots de Claves

Actualizar `SLOT_OPTIONS` en `application/services/data_package_service.py` para usar la tasa correcta de 100 stars/USDT:

- **+1 Clave**: 25 stars → 250 stars
- **+3 Claves**: 60 stars → 600 stars
- **+5 Claves**: 90 stars → 900 stars

- **Acceptance:** Los precios en estrellas reflejan correctamente 100 stars = 1 USDT

### FR-3: Actualizar Tests Relacionados

Actualizar los tests que verifican valores de estrellas para que usen los nuevos precios correctos.

- **Acceptance:** Todos los tests pasan con los nuevos valores de precios

## Non-Functional Requirements

### NFR-1: Consistencia de Precios

- **Target:** Todos los precios mostrados en el bot deben ser consistentes
- **Verification:** Revisar que no haya precios hardcodeados en otros archivos

## Acceptance Criteria

- [ ] Precios de paquetes actualizados a 500, 650, 850, 1100 stars
- [ ] Precios de slots actualizados a 250, 600, 900 stars
- [ ] Tests actualizados y pasando
- [ ] No hay otros lugares con precios hardcodeados incorrectos
- [ ] La conversión USDT en handlers (stars/10 → stars/100) está actualizada si es necesario

## Scope

### In Scope

- Actualización de `PACKAGE_OPTIONS` en `data_package_service.py`
- Actualización de `SLOT_OPTIONS` en `data_package_service.py`
- Actualización de tests relacionados
- Revisión de handlers para verificar consistencia de conversión

### Out of Scope

- Cambios a la lógica de negocio
- Cambios a la estructura de datos
- Modificaciones a la UI/UX del bot

## Dependencies

### Internal

- Ninguna - cambio de configuración simple

### External

- Ninguna

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tests fallando por valores hardcodeados | Medium | Buscar y actualizar todos los tests con valores de estrellas |
| Precios inconsistentes en mensajes | Low | Verificar que los mensajes usen los valores de las configuraciones |

## Open Questions

- [x] ¿La conversión USDT en handlers necesita actualización? - Sí, debe cambiar de `stars/10` a `stars/100`
