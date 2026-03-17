# Mini App Web - Migración de Rutas API

**Created:** 2026-03-17
**Status:** Pending
**Priority:** High
**Estimated Effort:** 2-3 horas

---

## Overview

Migrar la Mini App Web desde el prefijo `/miniapp/` hacia `/api/v1/miniapp/` para unificar la estructura de APIs del proyecto y separar claramente las plataformas (Flutter App vs Mini App Web).

---

## Motivación

1. **Consistencia arquitectónica**: Todas las APIs bajo `/api/v1/`
2. **Separación por plataforma**: `/api/v1/app/` (móvil) vs `/api/v1/miniapp/` (web)
3. **Rate limiting diferenciado**: Políticas distintas por plataforma
4. **Documentación clara**: Swagger/OpenAPI organizado por tags
5. **Escalabilidad**: Fácil agregar nuevas plataformas (ej: `/api/v1/admin/`)

---

## Cambios Requeridos

### 1. Rutas a Migrar

| Archivo Actual | Ruta Actual | Nueva Ruta | Método |
|----------------|-------------|------------|--------|
| `miniapp/routes_user.py` | `/miniapp/` | `/api/v1/miniapp/dashboard` | GET |
| `miniapp/routes_user.py` | `/miniapp/profile` | `/api/v1/miniapp/profile` | GET |
| `miniapp/routes_user.py` | `/miniapp/settings` | `/api/v1/miniapp/settings` | GET |
| `miniapp/routes_user.py` | `/miniapp/api/user` | `/api/v1/miniapp/api/user` | GET |
| `miniapp/routes_keys.py` | `/miniapp/keys` | `/api/v1/miniapp/keys` | GET |
| `miniapp/routes_keys.py` | `/miniapp/keys/create` | `/api/v1/miniapp/keys/create` | GET/POST |
| `miniapp/routes_keys.py` | `/miniapp/api/keys` | `/api/v1/miniapp/api/keys` | GET |
| `miniapp/routes_keys.py` | `/miniapp/api/keys/delete` | `/api/v1/miniapp/api/keys/delete` | POST |
| `miniapp/routes_payments.py` | `/miniapp/purchase` | `/api/v1/miniapp/purchase` | GET |
| `miniapp/routes_payments.py` | `/miniapp/api/create-stars-invoice` | `/api/v1/miniapp/api/create-stars-invoice` | POST |
| `miniapp/routes_payments.py` | `/miniapp/api/create-crypto-order` | `/api/v1/miniapp/api/create-crypto-order` | POST |
| `miniapp/routes_payments.py` | `/miniapp/api/confirm-payment` | `/api/v1/miniapp/api/confirm-payment` | POST |
| `miniapp/routes_subscriptions.py` | `/api/v1/subscriptions/plans` | `/api/v1/miniapp/api/subscriptions/plans` | GET |
| `miniapp/routes_subscriptions.py` | `/api/v1/subscriptions/status` | `/api/v1/miniapp/api/subscriptions/status` | GET |
| `miniapp/routes_subscriptions.py` | `/api/v1/subscriptions/activate` | `/api/v1/miniapp/api/subscriptions/activate` | POST |
| `miniapp/routes_subscriptions.py` | `/api/v1/subscriptions/check/{user_id}` | `/api/v1/miniapp/api/subscriptions/check/{user_id}` | GET |
| `miniapp/routes_admin.py` | `/miniapp/logs` | `/api/v1/miniapp/admin/logs` | GET |
| `miniapp/routes_admin.py` | `/miniapp/api/logs` | `/api/v1/miniapp/admin/api/logs` | GET |
| `miniapp/routes_public.py` | `/miniapp/entry` | `/api/v1/miniapp/public/entry` | GET |
| `miniapp/routes_public.py` | `/miniapp/privacy` | `/api/v1/miniapp/public/privacy` | GET |

---

### 2. Cambios en Archivos

#### 2.1 `miniapp/__init__.py`

**Antes:**
```python
from miniapp.router import router

__all__ = ["router"]
```

**Después:**
```python
# Este archivo se mantendrá para compatibilidad temporal
# Las rutas ahora se registran desde infrastructure/api/server.py
from miniapp.router import router as legacy_router

__all__ = ["legacy_router"]
```

#### 2.2 `miniapp/router.py`

**Antes:**
```python
router = APIRouter(prefix="/miniapp", tags=["Mini App"])
```

**Después:**
```python
# Este router ya no se usa directamente
# Las rutas se mueven a infrastructure/api/routes/miniapp_*.py
```

#### 2.3 `infrastructure/api/server.py`

**Antes:**
```python
from miniapp import router as miniapp_router

app.include_router(miniapp_router)
```

**Después:**
```python
from infrastructure.api.routes import (
    miniapp_auth_router,
    miniapp_user_router,
    miniapp_keys_router,
    miniapp_payments_router,
    miniapp_subscriptions_router,
    miniapp_admin_router,
    miniapp_public_router,
)

# Registrar rutas de Mini App con nuevo prefijo
app.include_router(miniapp_user_router, prefix="/api/v1/miniapp")
app.include_router(miniapp_keys_router, prefix="/api/v1/miniapp")
app.include_router(miniapp_payments_router, prefix="/api/v1/miniapp")
app.include_router(miniapp_subscriptions_router, prefix="/api/v1/miniapp")
app.include_router(miniapp_admin_router, prefix="/api/v1/miniapp")
app.include_router(miniapp_public_router, prefix="/api/v1/miniapp")
```

#### 2.4 Templates HTML

Actualizar todas las referencias a rutas en los templates:

**`miniapp/templates/dashboard.html`**
```html
<!-- Antes -->
<script src="/miniapp/static/js/dashboard.js"></script>
<link rel="stylesheet" href="/miniapp/static/css/dashboard.css">

<!-- Después -->
<script src="/api/v1/miniapp/static/js/dashboard.js"></script>
<link rel="stylesheet" href="/api/v1/miniapp/static/css/dashboard.css">
```

**Actualizar en todos los templates:**
- `dashboard.html`
- `profile.html`
- `settings.html`
- `keys.html`
- `create_key.html`
- `purchase.html`
- `entry.html`
- `privacy.html`

---

### 3. Archivos Nuevos a Crear

```
infrastructure/api/routes/
├── __init__.py
├── miniapp_user.py           # Migrado desde miniapp/routes_user.py
├── miniapp_keys.py           # Migrado desde miniapp/routes_keys.py
├── miniapp_payments.py       # Migrado desde miniapp/routes_payments.py
├── miniapp_subscriptions.py  # Migrado desde miniapp/routes_subscriptions.py
├── miniapp_admin.py          # Migrado desde miniapp/routes_admin.py
└── miniapp_public.py         # Migrado desde miniapp/routes_public.py
```

---

## Plan de Migración

### Paso 1: Crear Nueva Estructura (30 min)

```bash
# Crear directorio de rutas
mkdir -p infrastructure/api/routes

# Copiar archivos existentes
cp miniapp/routes_user.py infrastructure/api/routes/miniapp_user.py
cp miniapp/routes_keys.py infrastructure/api/routes/miniapp_keys.py
cp miniapp/routes_payments.py infrastructure/api/routes/miniapp_payments.py
cp miniapp/routes_subscriptions.py infrastructure/api/routes/miniapp_subscriptions.py
cp miniapp/routes_admin.py infrastructure/api/routes/miniapp_admin.py
cp miniapp/routes_public.py infrastructure/api/routes/miniapp_public.py
```

### Paso 2: Actualizar Rutas en Archivos Copiados (45 min)

En cada archivo, actualizar el router:

**`infrastructure/api/routes/miniapp_user.py`**
```python
# Antes
router = APIRouter(tags=["Mini App - User"])

# Después
router = APIRouter(tags=["Mini App Web - User"])
# Las rutas individuales ya no necesitan el prefijo /miniapp
# porque se añade en server.py al incluir el router
```

### Paso 3: Actualizar server.py (15 min)

Actualizar `infrastructure/api/server.py` para incluir los nuevos routers con el prefijo `/api/v1/miniapp`.

### Paso 4: Actualizar Templates (30 min)

Buscar y reemplazar en todos los templates:
- `/miniapp/static/` → `/api/v1/miniapp/static/`
- `href="/miniapp/` → `href="/api/v1/miniapp/`
- `src="/miniapp/` → `src="/api/v1/miniapp/`

### Paso 5: Actualizar Imports en Mini App Services (15 min)

Los servicios en `miniapp/services/` pueden importar rutas que necesitan actualización.

### Paso 6: Testing Local (30 min)

```bash
# Iniciar servidor
uv run python main.py

# Testear endpoints
curl http://localhost:8000/api/v1/miniapp/dashboard
curl http://localhost:8000/api/v1/miniapp/profile
curl http://localhost:8000/api/v1/miniapp/keys
curl http://localhost:8000/api/v1/miniapp/api/user

# Verificar que static files cargan
curl http://localhost:8000/api/v1/miniapp/static/js/dashboard.js
```

### Paso 7: Actualizar Frontend Mini App (15 min)

Si la Mini App tiene código JavaScript que hace fetch a rutas, actualizar:

```javascript
// Antes
const response = await fetch('/miniapp/api/user');

// Después
const response = await fetch('/api/v1/miniapp/api/user');
```

### Paso 8: Deploy y Verificación (15 min)

1. Deploy a producción
2. Verificar logs
3. Testear en Telegram Mini App
4. Monitorear errores

---

## Rollback Plan

Si algo sale mal:

1. **Revertir server.py**: Comentar nuevos routers, restaurar import antiguo
2. **Reiniciar servicio**: `sudo systemctl restart usipipo`
3. **Verificar**: La Mini App debería funcionar con rutas antiguas

---

## Checklist de Migración

- [ ] Crear directorio `infrastructure/api/routes/`
- [ ] Copiar 6 archivos de rutas desde `miniapp/`
- [ ] Actualizar routers en archivos copiados
- [ ] Actualizar `infrastructure/api/server.py`
- [ ] Actualizar templates HTML (8 archivos)
- [ ] Actualizar imports en `miniapp/services/`
- [ ] Actualizar JavaScript en templates
- [ ] Testing local de todos los endpoints
- [ ] Testing de static files
- [ ] Testing en Telegram Mini App
- [ ] Deploy a producción
- [ ] Verificación post-deploy
- [ ] Eliminar código legacy (después de 1 semana sin errores)

---

## Riesgos y Mitigación

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Static files no cargan | Alto | Verificar mount en server.py |
| Templates con rutas hardcodeadas | Medio | Búsqueda global en templates |
| JavaScript con fetch a rutas viejas | Medio | Revisar todos los .js y .html |
| CORS issues | Alto | Actualizar allow_origins si es necesario |
| Telegram Mini App cachea rutas | Medio | Forzar recarga con version en URLs |

---

## Métricas de Éxito

- ✅ Todos los endpoints responden 200 OK
- ✅ Static files cargan correctamente
- ✅ Mini App funciona en Telegram sin errores
- ✅ No hay errores 404 en logs
- ✅ No hay errores de CORS

---

## Post-Migración

Después de 1 semana sin errores:

1. Eliminar `miniapp/router.py` (ya no se usa)
2. Eliminar `miniapp/__init__.py` (limpieza)
3. Actualizar documentación QWEN.md y AGENTS.md
4. Actualizar tests si existen

---

## Notas Adicionales

- **No breaking change para usuarios**: La URL de la Mini App en Telegram no cambia
- **Solo cambia el path interno**: Los usuarios no notan la migración
- **Mismo dominio**: `https://usipipo.duckdns.org/api/v1/miniapp/...`
- **FCM y notificaciones**: No se ven afectados

---

**Document Owner:** uSipipo Team
**Last Updated:** 2026-03-17
**Next Review:** After migration completion
