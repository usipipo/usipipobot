# Plan de Implementación: Telegram Mini App Web

**Fecha:** 2026-02-24
**Issue:** #172
**Branch:** feature/telegram-miniapp-web

## Resumen

Implementación de una Mini App Web de Telegram para uSipipo VPN Bot que permite a los usuarios gestionar sus claves VPN desde una interfaz web integrada en Telegram con diseño cyberpunk.

## Componentes Implementados

### Backend

1. **Servicio de Autenticación** (`miniapp/services/miniapp_auth.py`)
   - Validación de `initData` de Telegram
   - Verificación de hash HMAC
   - Control de frescura de sesión (24h max)
   - Clase `TelegramUser` para datos del usuario

2. **Router FastAPI** (`miniapp/router.py`)
   - Endpoints HTML: `/miniapp/`, `/miniapp/keys`, `/miniapp/keys/create`, `/miniapp/purchase`
   - Endpoints API: `/miniapp/api/user`, `/miniapp/api/keys`, `/miniapp/api/keys/delete`
   - Dependencia `get_current_user` para autenticación
   - Integración con VpnService existente

3. **Integración con Servidor** (`infrastructure/api/server.py`)
   - Import del router de Mini App
   - Mount de archivos estáticos

### Frontend

1. **Templates Jinja2** (`miniapp/templates/`)
   - `base.html`: Layout base con estilos cyberpunk inline
   - `dashboard.html`: Dashboard con métricas y claves
   - `keys.html`: Gestión de claves VPN
   - `create_key.html`: Formulario de creación
   - `purchase.html`: Tienda de paquetes

2. **Estilos** (`miniapp/static/css/cyberpunk.css`)
   - Paleta cyberpunk (neon cyan, magenta, terminal green)
   - Efectos glitch
   - Animaciones scan-line
   - Soporte para dark mode

3. **JavaScript** (`miniapp/static/js/app.js`)
   - Integración con Telegram WebApp SDK
   - Manejo de initData
   - Haptic feedback
   - Utilidades de formateo

### Configuración

- Nuevas variables en `config.py`:
  - `MINIAPP_URL`: URL base de la Mini App
  - `MINIAPP_ENABLED`: Habilitar/deshabilitar

## Funcionalidades

1. **Autenticación Automática**
   - Validación de datos de Telegram
   - Sin login tradicional

2. **Dashboard**
   - Métricas de consumo
   - Claves activas
   - Acciones rápidas

3. **Gestión de Claves**
   - Ver lista de claves
   - Crear nuevas claves
   - Eliminar claves existentes

4. **Tienda**
   - Paquetes de datos (Básico, Estándar, Premium)
   - Integración con Telegram Stars (redirección al bot)

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /miniapp/ | Dashboard principal |
| GET | /miniapp/keys | Lista de claves |
| GET | /miniapp/keys/create | Formulario crear clave |
| POST | /miniapp/keys/create | Crear clave |
| GET | /miniapp/purchase | Tienda de paquetes |
| GET | /miniapp/api/user | API datos usuario |
| GET | /miniapp/api/keys | API lista claves |
| POST | /miniapp/api/keys/delete | API eliminar clave |

## Seguridad

- Validación HMAC de initData con token del bot
- Control de expiración de sesión (24 horas)
- Sin exposición de datos sensibles
- Rate limiting heredado del servidor

## Diseño Visual

- Tema oscuro cyberpunk
- Paleta de colores neón
- Efectos glitch en títulos
- Bordes con glow
- Animaciones sutiles
- Responsive para móvil

## Testing

- Verificar importaciones
- Probar endpoints
- Validar templates

## Próximos Pasos

1. Configurar URL de la Mini App en BotFather
2. Probar autenticación con initData real
3. Implementar pagos Stars desde la Mini App
4. Añadir más animaciones y efectos
