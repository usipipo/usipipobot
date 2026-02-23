# Plan: Rediseño Visual de Mensajes /info y /data

**Issue:** #151
**Fecha:** 2026-02-23
**Estilo:** Cyberpunk/Neón

## Objetivo

Mejorar la experiencia visual de los mensajes del botón "Mis Datos" (/data) y el comando /info con un diseño Cyberpunk/Neón que incluye barras de progreso visuales, estructura jerárquica con ASCII art, y métricas detalladas.

## Archivos a Modificar

1. `telegram_bot/features/user_management/messages_user_management.py`
   - Clase `Info` - rediseño completo del mensaje `/info`
   - Clase `Status` - mejoras visuales menores

2. `telegram_bot/features/buy_gb/messages_buy_gb.py`
   - Clase `Data` - rediseño completo del mensaje `/data`
   - Clase `Info` - mejoras visuales menores

3. `telegram_bot/features/user_management/handlers_user_management.py`
   - `info_handler` - pasar datos adicionales necesarios

4. `telegram_bot/features/buy_gb/handlers_buy_gb.py`
   - `data_handler` - pasar datos adicionales necesarios

## Implementación

### Fase 1: Funciones Auxiliares

Crear funciones helper en cada archivo de mensajes:

```python
def _progress_bar(percentage: int, width: int = 20) -> str:
    """Genera barra de progreso ASCII."""
    filled = int(width * percentage / 100)
    return "▓" * filled + "░" * (width - filled)
```

### Fase 2: Rediseño `/info`

Nueva estructura:
- Header con ASCII art box
- Sección PROFILE con datos básicos
- Sección DATA METRICS con barra de progreso
- Sección KEY MATRIX con slots visuales
- Sección REFERRAL NETWORK

### Fase 3: Rediseño `/data`

Nueva estructura:
- Header con ASCII art box
- Sección por cada paquete activo con barra de progreso
- Sección FREE TIER con barra de progreso
- Footer con total disponible y eficiencia

### Fase 4: Handlers

Actualizar handlers para pasar:
- `days_remaining` y `hours_remaining` para paquetes
- `efficiency` calculada
- `total_limit_gb` para barras de progreso

## Criterios de Aceptación

- [ ] Mensajes se muestran correctamente en Telegram
- [ ] Barras de progreso reflejan porcentajes reales
- [ ] Información es legible y bien organizada
- [ ] No hay regresiones en funcionalidad existente

## Testing

- Verificar renderizado en Telegram Desktop
- Verificar renderizado en Telegram Mobile
- Verificar casos edge (sin datos, sin paquetes, etc.)
