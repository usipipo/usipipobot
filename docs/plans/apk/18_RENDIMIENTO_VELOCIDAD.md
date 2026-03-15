# Plan de Rendimiento y Velocidad de Respuesta

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Single VPS con todos los servicios (Bot + Mini App + VPN + Backend + APK)
> **Objetivo:** Respuestas en <100ms para el 95% de las peticiones

---

## 🎯 Objetivos de Rendimiento

### Metas de Latencia (SLOs)

| Endpoint/Operación | p50 | p95 | p99 |
|-------------------|-----|-----|-----|
| GET /api/v1/dashboard/summary | 50ms | 100ms | 200ms |
| GET /api/v1/keys | 30ms | 80ms | 150ms |
| POST /api/v1/keys/create | 200ms | 500ms | 1000ms |
| POST /api/v1/auth/request-otp | 100ms | 200ms | 400ms |
| POST /api/v1/auth/verify-otp | 50ms | 100ms | 200ms |
| GET /api/v1/notifications/pending | 20ms | 50ms | 100ms |
| Bot Telegram (comando /start) | 500ms | 1000ms | 2000ms |
| Bot Telegram (callback query) | 300ms | 600ms | 1200ms |

### Metas de Throughput

| Métrica | Objetivo |
|---------|----------|
| Requests/segundo (backend) | 100-200 |
| Conexiones simultáneas (backend) | 50-100 |
| Conexiones activas (PostgreSQL) | 10-20 |
| Operaciones/segundo (Redis) | 1000+ |
| Ancho de banda VPN (WireGuard) | 100+ Mbps |
| Ancho de banda VPN (Outline) | 50+ Mbps |

---

## ⚡ Estrategia de Optimización

### Principios Rectores

1. **"Cache Everything"**: Si se puede cachear, se cachea
2. **"Async Everywhere"**: Todo asíncrono, nada de blocking I/O
3. **"Connection Pooling"**: Reutilizar conexiones, no crear nuevas
4. **"Query Optimization"**: Cada query debe usar índices
5. **"Minimal Payload"**: Responses lo más pequeñas posible

---

## 🔥 Fase 1: Optimización de PostgreSQL

### 1.1 Índices Estratégicos

**Script: `/opt/usipipobot/scripts/create_indexes.sql`**

```sql
-- =============================================================================
-- ÍNDICES ESTRATÉGICOS PARA OPTIMIZAR QUERIES CRÍTICOS
-- =============================================================================

-- Usuario por telegram_id (ya debería existir como PK, pero verificar)
CREATE INDEX IF NOT EXISTS idx_users_telegram_id
ON users(telegram_id);

-- Usuario por referral_code (para flujo de referidos)
CREATE INDEX IF NOT EXISTS idx_users_referral_code
ON users(referral_code);

-- Usuario por status (para filtrar usuarios activos)
CREATE INDEX IF NOT EXISTS idx_users_status
ON users(status);

-- Composite index para login (telegram_id + status)
CREATE INDEX IF NOT EXISTS idx_users_telegram_status
ON users(telegram_id, status);

-- Claves VPN por usuario
CREATE INDEX IF NOT EXISTS idx_vpn_keys_user_id
ON vpn_keys(user_id);

-- Claves VPN por usuario + activas (query más común)
CREATE INDEX IF NOT EXISTS idx_vpn_keys_user_active
ON vpn_keys(user_id, is_active);

-- Claves VPN por external_id (para sync con servidores VPN)
CREATE INDEX IF NOT EXISTS idx_vpn_keys_external_id
ON vpn_keys(external_id);

-- Paquetes de datos por usuario + activos
CREATE INDEX IF NOT EXISTS idx_data_packages_user_active
ON data_packages(user_id, is_active);

-- Paquetes de datos por expires_at (para job de expiración)
CREATE INDEX IF NOT EXISTS idx_data_packages_expires_at
ON data_packages(expires_at)
WHERE is_active = true;

-- Crypto orders por status + created_at (para job de expiración)
CREATE INDEX IF NOT EXISTS idx_crypto_orders_status_created
ON crypto_orders(status, created_at);

-- Tickets por usuario + status
CREATE INDEX IF NOT EXISTS idx_tickets_user_status
ON tickets(user_id, status);

-- Tickets por status + created_at (para admins)
CREATE INDEX IF NOT EXISTS idx_tickets_status_created
ON tickets(status, created_at);

-- Notificaciones Android por telegram_id + no leídas
CREATE INDEX IF NOT EXISTS idx_android_notif_user_unread
ON android_notifications(telegram_id, is_read)
WHERE is_read = false;

-- Índice parcial para notificaciones pendientes (< 24 horas)
CREATE INDEX IF NOT EXISTS idx_android_notif_recent_unread
ON android_notifications(telegram_id, created_at)
WHERE is_read = false
  AND created_at > NOW() - INTERVAL '24 hours';

-- =============================================================================
-- ÍNDICES DE ALTO RENDIMIENTO (BRIN)
-- =============================================================================
-- Los índices BRIN son más pequeños y eficientes para columnas correlacionadas

-- Índice BRIN para created_at en users (los nuevos usuarios se insertan al final)
CREATE INDEX IF NOT EXISTS idx_users_created_at_brin
ON users USING BRIN(created_at);

-- Índice BRIN para created_at en vpn_keys
CREATE INDEX IF NOT EXISTS idx_vpn_keys_created_at_brin
ON vpn_keys USING BRIN(created_at);

-- Índice BRIN para created_at en data_packages
CREATE INDEX IF NOT EXISTS idx_data_packages_created_at_brin
ON data_packages USING BRIN(created_at);

-- =============================================================================
-- ESTADÍSTICAS ACTUALIZADAS
-- =============================================================================
-- Analizar tablas para que el query planner tenga estadísticas frescas

ANALYZE users;
ANALYZE vpn_keys;
ANALYZE data_packages;
ANALYZE crypto_orders;
ANALYZE tickets;
ANALYZE android_notifications;

-- =============================================================================
-- VERIFICACIÓN DE ÍNDICES
-- =============================================================================
-- Query para verificar que todos los índices existen

SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

**Ejecutar:**
```bash
sudo -u postgres psql -d usipipodb -f /opt/usipipobot/scripts/create_indexes.sql
```

---

### 1.2 Query Optimization

**Queries críticas optimizadas:**

#### Query 1: Obtener dashboard de usuario (CRÍTICO)

**Antes (lento, 200-300ms):**
```python
# Múltiples queries separadas
user = await get_user(telegram_id)
keys = await get_user_keys(telegram_id)
packages = await get_user_packages(telegram_id)
# ... más queries
```

**Después (rápido, <50ms):**
```python
# Single query con JOINs y aggregations
async def get_dashboard_summary(session: AsyncSession, telegram_id: int):
    """
    Obtener todo el dashboard en una sola query.
    """
    query = text("""
        WITH user_data AS (
            SELECT
                telegram_id,
                username,
                full_name,
                status,
                role,
                referral_credits,
                free_data_limit_bytes,
                free_data_used_bytes,
                created_at as joined_at
            FROM users
            WHERE telegram_id = :telegram_id
        ),
        keys_summary AS (
            SELECT
                COUNT(*) FILTER (WHERE is_active = true) as active_keys,
                COUNT(*) as total_keys,
                SUM(used_bytes) FILTER (WHERE is_active = true) as total_used_bytes,
                MAX(created_at) as last_key_created
            FROM vpn_keys
            WHERE user_id = :telegram_id
        ),
        active_package AS (
            SELECT
                package_type,
                data_limit_bytes,
                data_used_bytes,
                expires_at,
                purchased_at
            FROM data_packages
            WHERE user_id = :telegram_id
              AND is_active = true
            ORDER BY expires_at DESC
            LIMIT 1
        ),
        referral_stats AS (
            SELECT
                COUNT(*) as total_referrals,
                SUM(CASE WHEN u.status = 'active' THEN 1 ELSE 0 END) as active_referrals
            FROM users u
            WHERE u.referred_by = :telegram_id
        )
        SELECT
            ud.*,
            ks.active_keys,
            ks.total_keys,
            ks.total_used_bytes,
            ks.last_key_created,
            ap.package_type,
            ap.data_limit_bytes as package_limit,
            ap.data_used_bytes as package_used,
            ap.expires_at as package_expires,
            ap.purchased_at,
            rs.total_referrals,
            rs.active_referrals
        FROM user_data ud
        CROSS JOIN keys_summary ks
        CROSS JOIN active_package ap
        CROSS JOIN referral_stats rs;
    """)

    result = await session.execute(query, {"telegram_id": telegram_id})
    return result.first()
```

#### Query 2: Listar claves VPN con uso de datos

**Antes:**
```python
# N+1 queries: una para claves, luego una por cada clave para uso
keys = await session.execute(select(VpnKey).where(...))
for key in keys:
    usage = await get_key_usage(key.id)  # Query adicional por cada clave
```

**Después:**
```python
# Single query con todo incluido
query = text("""
    SELECT
        vk.id,
        vk.name,
        vk.key_type,
        vk.is_active,
        vk.used_bytes,
        vk.created_at,
        vk.last_used_at,
        COALESCE(
            dp.data_limit_bytes - dp.data_used_bytes,
            u.free_data_limit_bytes - u.free_data_used_bytes
        ) as remaining_bytes
    FROM vpn_keys vk
    LEFT JOIN LATERAL (
        SELECT data_limit_bytes, data_used_bytes
        FROM data_packages
        WHERE user_id = vk.user_id
          AND is_active = true
        ORDER BY expires_at DESC
        LIMIT 1
    ) dp ON true
    JOIN users u ON u.telegram_id = vk.user_id
    WHERE vk.user_id = :telegram_id
    ORDER BY vk.created_at DESC;
""")
```

---

### 1.3 Connection Pooling Optimizado

**Archivo: `infrastructure/persistence/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from config import settings

# =============================================================================
# CONFIGURACIÓN OPTIMIZADA PARA VPS DE 2GB
# =============================================================================

engine = create_async_engine(
    settings.database_url,
    poolclass=AsyncAdaptedQueuePool,

    # Pool sizing - crítico para rendimiento
    pool_size=10,                   # Máximo de conexiones permanentes
    max_overflow=5,                 # Conexiones extra temporales (burst)
    pool_timeout=30,                # Timeout esperando conexión disponible
    pool_recycle=1800,              # Reciclar conexiones cada 30min (evita stale connections)
    pool_pre_ping=True,             # Verificar conexión antes de usar (evita errors)

    # Parámetros de conexión
    connect_args={
        "server_settings": {
            "application_name": "usipipo_backend",
            "statement_timeout": "30000",       # 30s timeout por query
            "idle_in_transaction_session_timeout": "60000",  # 60s para transacciones
        }
    },

    # No loggear SQL en producción (ahorra I/O)
    echo=False,

    # Usar asyncpg (más rápido que psycopg2)
    echo_pool=False,
)

session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,       # No expirar objetos después de commit (mejor cache)
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)


# =============================================================================
# CONTEXTO DE SESIÓN REUTILIZABLE
# =============================================================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session():
    """
    Obtener sesión de base de datos del pool.
    Usar como context manager para asegurar cleanup correcto.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# =============================================================================
# MONITOREO DEL POOL
# =============================================================================

def get_pool_stats() -> dict:
    """
    Obtener estadísticas del pool de conexiones.
    Útil para debugging y monitoreo.
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0,
    }
```

---

## 🚀 Fase 2: Optimización de Redis

### 2.1 Estrategia de Caché Multi-Nivel

**Archivo: `infrastructure/cache/layered_cache.py`**

```python
"""
Caché en múltiples niveles para máximo rendimiento.

Nivel 1: Caché en memoria (asyncio LRU cache) - <1ms
Nivel 2: Redis local - 1-5ms
Nivel 3: Base de datos - 10-50ms

La mayoría de las requests deberían ser servidas desde Nivel 1 o 2.
"""
import asyncio
from functools import wraps
from typing import Any, Callable, Optional
from datetime import timedelta
import redis.asyncio as redis
from loguru import logger


class LayeredCache:
    """Caché multi-nivel optimizado."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

        # Nivel 1: Caché en memoria (por proceso worker)
        # Cada worker de Uvicorn tiene su propio caché en memoria
        self._memory_cache: dict[str, Any] = {}
        self._memory_cache_ttl: dict[str, float] = {}

        # Límite de caché en memoria (evitar memory leak)
        self._memory_cache_max_size = 1000

    async def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché multi-nivel.
        """
        import time
        current_time = time.time()

        # Nivel 1: Memoria
        if key in self._memory_cache:
            # Verificar TTL
            if key in self._memory_cache_ttl and current_time < self._memory_cache_ttl[key]:
                logger.debug(f"Caché HIT memoria: {key}")
                return self._memory_cache[key]
            else:
                # Expirado, limpiar
                del self._memory_cache[key]
                if key in self._memory_cache_ttl:
                    del self._memory_cache_ttl[key]

        # Nivel 2: Redis
        try:
            value = await self.redis.get(key)
            if value:
                import json
                result = json.loads(value)

                # Promover a memoria
                self._set_memory(key, result)

                logger.debug(f"Caché HIT Redis: {key}")
                return result
        except Exception as e:
            logger.error(f"Error leyendo Redis: {e}")

        # Caché miss
        logger.debug(f"Caché MISS: {key}")
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Guardar valor en caché multi-nivel.
        """
        import json

        # Nivel 1: Memoria
        self._set_memory(key, value)

        # Nivel 2: Redis
        try:
            await self.redis.setex(
                key,
                ttl_seconds,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Error escribiendo Redis: {e}")

    def _set_memory(self, key: str, value: Any):
        """Guardar en caché de memoria con LRU."""
        import time

        # LRU: si está lleno, eliminar el más viejo
        if len(self._memory_cache) >= self._memory_cache_max_size:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
            if oldest_key in self._memory_cache_ttl:
                del self._memory_cache_ttl[oldest_key]

        self._memory_cache[key] = value
        self._memory_cache_ttl[key] = time.time() + 300  # 5 min TTL por defecto

    async def delete(self, key: str):
        """Eliminar valor del caché en todos los niveles."""
        # Nivel 1: Memoria
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._memory_cache_ttl:
            del self._memory_cache_ttl[key]

        # Nivel 2: Redis
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error eliminando de Redis: {e}")

    async def clear_memory(self):
        """Limpiar caché de memoria (útil para debugging)."""
        self._memory_cache.clear()
        self._memory_cache_ttl.clear()


# =============================================================================
# DECORADOR PARA CACHEAR FUNCIONES ASÍNCRONAS
# =============================================================================

def cached(
    prefix: str = "",
    ttl_seconds: int = 300,
    key_builder: Optional[Callable] = None
):
    """
    Decorador para cachear resultados de funciones asíncronas.

    Usage:
        @cached(prefix="user_profile", ttl_seconds=600)
        async def get_user_profile(telegram_id: int):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Construir cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Key por defecto: prefix:func_name:args_hash
                import hashlib
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                key = f"{prefix}:{func.__name__}:{args_hash}"

            # Intentar caché
            cache = LayeredCache(settings.redis_url)
            cached_value = await cache.get(key)
            if cached_value is not None:
                return cached_value

            # Ejecutar función
            result = await func(*args, **kwargs)

            # Guardar en caché
            await cache.set(key, result, ttl_seconds)

            return result
        return wrapper
    return decorator
```

---

### 2.2 Caché de Dashboard (Ejemplo Práctico)

**Archivo: `infrastructure/cache/dashboard_cache.py`**

```python
"""
Caché específico para el dashboard de usuario.
"""
from infrastructure.cache.layered_cache import LayeredCache, cached
from config import settings

dashboard_cache = LayeredCache(settings.redis_url)


async def get_cached_dashboard(telegram_id: int) -> dict | None:
    """
    Obtener dashboard del caché.
    """
    key = f"dashboard:{telegram_id}"
    return await dashboard_cache.get(key)


async def set_cached_dashboard(telegram_id: int, data: dict, ttl_seconds: int = 900):
    """
    Guardar dashboard en caché.

    TTL por defecto: 15 minutos (900 segundos)
    """
    key = f"dashboard:{telegram_id}"
    await dashboard_cache.set(key, data, ttl_seconds)


async def invalidate_dashboard(telegram_id: int):
    """
    Invalidar caché del dashboard cuando hay cambios.
    """
    key = f"dashboard:{telegram_id}"
    await dashboard_cache.delete(key)


# =============================================================================
# INVALIDACIÓN AUTOMÁTICA
# =============================================================================
# Llamar a invalidate_dashboard() cuando:
# - Usuario compra un paquete de datos
# - Usuario crea/elimina una clave VPN
# - Usuario actualiza su perfil
# - Sync de uso de datos VPN

async def on_package_purchased(telegram_id: int):
    """Callback cuando un usuario compra un paquete."""
    await invalidate_dashboard(telegram_id)
    # Notificar a otros servicios si es necesario


async def on_key_created(telegram_id: int):
    """Callback cuando se crea una clave VPN."""
    await invalidate_dashboard(telegram_id)


async def on_key_deleted(telegram_id: int):
    """Callback cuando se elimina una clave VPN."""
    await invalidate_dashboard(telegram_id)


async def on_data_sync(telegram_id: int):
    """Callback cuando se sincroniza el uso de datos VPN."""
    await invalidate_dashboard(telegram_id)
```

---

## ⚡ Fase 3: Optimización del Backend FastAPI

### 3.1 Uvicorn con HttpTools y UVLoop

**Instalación:**
```bash
pip install httptools uvloop
```

**Configuración en `infrastructure/api/server.py`:**

```python
import uvloop
from fastapi import FastAPI
from loguru import logger

# Instalar uvloop antes de cualquier código async
uvloop.install()
logger.info("UVLoop instalado - event loop más rápido")


def create_app() -> FastAPI:
    """Crear aplicación FastAPI optimizada."""

    app = FastAPI(
        title="uSipipo VPN API",
        description="API para gestión de VPN uSipipo",
        version="3.4.0",
        docs_url=None,              # Deshabilitar Swagger en producción (ahorra recursos)
        redoc_url=None,             # Deshabilitar ReDoc en producción
        openapi_url=None,           # Deshabilitar OpenAPI JSON en producción
    )

    # Configurar middlewares
    # ... (security headers, rate limiting, etc.)

    # Configurar rutas
    # ... (android routes, webhooks, etc.)

    # Startup event
    @app.on_event("startup")
    async def startup():
        logger.info("Backend iniciando con optimizaciones de rendimiento")
        logger.info(f"Workers: {settings.workers}")
        logger.info(f"HttpTools: instalado")
        logger.info(f"UVLoop: instalado")

    return app
```

**Beneficios:**
- **HttpTools:** Parser HTTP en C, 2-3x más rápido que el parser de Python
- **UVLoop:** Event loop en C, 2-4x más rápido que asyncio default

---

### 3.2 Response Compression con Gzip

**Middleware: `infrastructure/api/middleware/compression.py`**

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import gzip
import json

class GZipMiddleware(BaseHTTPMiddleware):
    """
    Comprimir respuestas con gzip para reducir ancho de banda.
    Solo comprime respuestas > 1KB y < 1MB.
    """

    def __init__(self, app, minimum_size: int = 1024, maximum_size: int = 1048576):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.maximum_size = maximum_size

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Solo comprimir JSON responses
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            return response

        # Obtener body de la respuesta
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Solo comprimir si está dentro del rango de tamaño
        if self.minimum_size <= len(body) <= self.maximum_size:
            compressed = gzip.compress(body, compresslevel=6)

            # Solo usar compressed si es más pequeño
            if len(compressed) < len(body):
                response = Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers={
                        **response.headers,
                        "Content-Encoding": "gzip",
                        "Content-Length": str(len(compressed)),
                        "Vary": "Accept-Encoding",
                    },
                    media_type=response.media_type,
                )
                return response

        return response
```

**Registrar en `server.py`:**
```python
from infrastructure.api.middleware.compression import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1024)
```

**Beneficio:** Reduce el tamaño de respuestas JSON en 60-80%, especialmente útil para listas grandes.

---

### 3.3 Parallel Query Execution

**Ejemplo: Ejecutar queries en paralelo**

```python
"""
Ejecutar múltiples queries independientes en paralelo para reducir latencia.
"""
import asyncio
from sqlalchemy import text
from infrastructure.persistence.database import get_session


async def get_user_dashboard_parallel(telegram_id: int):
    """
    Obtener dashboard ejecutando queries independientes en paralelo.
    """
    async with get_session() as session:
        # Ejecutar todas las queries independientes en paralelo
        results = await asyncio.gather(
            session.execute(
                text("SELECT * FROM users WHERE telegram_id = :id"),
                {"id": telegram_id}
            ),
            session.execute(
                text("""
                    SELECT COUNT(*) as active_keys, SUM(used_bytes) as total_used
                    FROM vpn_keys
                    WHERE user_id = :id AND is_active = true
                """),
                {"id": telegram_id}
            ),
            session.execute(
                text("""
                    SELECT package_type, data_limit_bytes, expires_at
                    FROM data_packages
                    WHERE user_id = :id AND is_active = true
                    ORDER BY expires_at DESC LIMIT 1
                """),
                {"id": telegram_id}
            ),
            session.execute(
                text("""
                    SELECT COUNT(*) as referrals
                    FROM users
                    WHERE referred_by = :id
                """),
                {"id": telegram_id}
            ),
        )

        user_result, keys_result, package_result, referrals_result = results

        # Construir respuesta
        return {
            "user": user_result.first(),
            "keys": keys_result.first(),
            "package": package_result.first(),
            "referrals": referrals_result.first(),
        }
```

**Beneficio:** Reduce latencia de 4 queries secuenciales (4x tiempo de query) a paralelo (1x tiempo de query).

---

## 📊 Fase 4: Optimización de la Mini App Web

### 4.1 Static File Caching con Caddy

**Archivo: `Caddyfile`**

```caddyfile
usipipo.duckdns.org {
    # HTTPS automático con Let's Encrypt
    tls admin@usipipo.com

    # Reverse proxy para el backend
    reverse_proxy /api/* localhost:8000

    # Reverse proxy para webhooks
    reverse_proxy /webhooks/* localhost:8000

    # Servir archivos estáticos de la Mini App
    root * /opt/usipipobot/static
    file_server

    # Cache agresivo para archivos estáticos
    @static {
        path /static/*
        path /css/*
        path /js/*
        path /images/*
        path *.css
        path *.js
        path *.png
        path *.jpg
        path *.svg
        path *.ico
    }

    header @static {
        Cache-Control "public, max-age=31536000, immutable"
    }

    # Cache moderado para HTML (puede cambiar)
    @html {
        path *.html
        path /miniapp/*
    }

    header @html {
        Cache-Control "public, max-age=3600, must-revalidate"
    }

    # Gzip compression
    encode gzip

    # Security headers
    header {
        X-Frame-Options "DENY"
        X-Content-Type-Options "nosniff"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }
}
```

---

### 4.2 Lazy Loading de Imágenes

**En los templates HTML de la Mini App:**

```html
<!-- Imágenes con lazy loading nativo -->
<img src="placeholder.jpg" data-src="imagen-real.jpg" loading="lazy" alt="Descripción">

<!-- O con Intersection Observer para más control -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
});
</script>
```

---

## 📱 Fase 5: Optimización de la APK Android

### 5.1 HTTP Client Optimizado

**Archivo: `android_app/src/services/api_client.py`**

```python
"""
Cliente HTTP optimizado para la APK Android.
"""
import httpx
from typing import Optional
from android_app.src.config import BACKEND_URL, CERT_PINS


class OptimizedAPIClient:
    """
    Cliente HTTP con optimizaciones:
    - Connection pooling
    - Keep-alive
    - Retry automático
    - Timeout configurado
    - Certificate pinning
    """

    _instance: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """
        Obtener cliente HTTP singleton (reutilizar conexiones).
        """
        if cls._instance is None:
            # Configurar límites del pool
            limits = httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=30.0,
            )

            # Configurar timeouts
            timeout = httpx.Timeout(
                timeout=30.0,
                connect=10.0,
                read=15.0,
                write=10.0,
                pool=5.0,
            )

            # Configurar transporte con retries
            transport = httpx.AsyncHTTPTransport(
                retries=3,                    # Reintentar 3 veces antes de fallar
                limits=limits,
            )

            cls._instance = httpx.AsyncClient(
                base_url=BACKEND_URL,
                transport=transport,
                timeout=timeout,
                headers={
                    "User-Agent": "uSipipo-Android/1.0.0",
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                }
            )

        return cls._instance

    @classmethod
    async def close(cls):
        """Cerrar el cliente (al salir de la app)."""
        if cls._instance:
            await cls._instance.aclose()
            cls._instance = None


# =============================================================================
# DECORADOR PARA RETRIES AUTOMÁTICOS
# =============================================================================

from functools import wraps
import asyncio

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 0.5):
    """
    Decorador para reintentar requests fallidas con backoff exponencial.

    Usage:
        @retry_on_failure(max_retries=3)
        async def fetch_dashboard():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        # Backoff exponencial: 0.5s, 1s, 2s, ...
                        wait_time = backoff_factor * (2 ** attempt)
                        await asyncio.sleep(wait_time)

            # Todos los retries fallaron
            raise last_exception

        return wrapper
    return decorator
```

---

### 5.2 Caché Local en la APK

**Archivo: `android_app/src/storage/cache_storage.py`**

```python
"""
Caché local en la APK para reducir peticiones al backend.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional
from loguru import logger


class CacheStorage:
    """
    Caché en disco para la APK.
    Los datos se guardan en archivos JSON con TTL.
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Obtener path del archivo de caché."""
        # Sanitizar key para nombre de archivo
        safe_key = key.replace(":", "_").replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché.
        Retorna None si no existe o está expirado.
        """
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)

            # Verificar TTL
            expires_at = datetime.fromisoformat(data['expires_at'])
            if datetime.now() > expires_at:
                # Expirado, eliminar
                os.remove(cache_path)
                return None

            return data['value']

        except Exception as e:
            logger.error(f"Error leyendo caché {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_minutes: int = 15):
        """
        Guardar valor en caché con TTL.
        """
        cache_path = self._get_cache_path(key)
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)

        try:
            data = {
                'value': value,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.now().isoformat(),
            }

            with open(cache_path, 'w') as f:
                json.dump(data, f)

            logger.debug(f"Caché guardado: {key} (TTL: {ttl_minutes} min)")

        except Exception as e:
            logger.error(f"Error guardando caché {key}: {e}")

    def delete(self, key: str):
        """Eliminar valor del caché."""
        cache_path = self._get_cache_path(key)

        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.debug(f"Caché eliminado: {key}")

    def clear(self):
        """Limpiar todo el caché."""
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)

            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error eliminando {file_path}: {e}")

        logger.info("Caché limpiado completamente")


# =============================================================================
# CACHE ESPECÍFICO PARA DASHBOARD
# =============================================================================

dashboard_cache = CacheStorage(cache_dir="/data/data/org.usipipo/cache/dashboard")


def get_cached_dashboard() -> Optional[dict]:
    """Obtener dashboard del caché local."""
    return dashboard_cache.get("dashboard_summary")


def set_cached_dashboard(data: dict):
    """Guardar dashboard en caché local (15 min TTL)."""
    dashboard_cache.set("dashboard_summary", data, ttl_minutes=15)


def invalidate_dashboard():
    """Invalidar caché del dashboard."""
    dashboard_cache.delete("dashboard_summary")
```

---

## 📊 Fase 6: Monitoreo de Rendimiento

### 6.1 Endpoint de Métricas de Rendimiento

**Archivo: `infrastructure/api/routes_metrics.py`**

```python
from fastapi import APIRouter
from sqlalchemy import text
import time
from infrastructure.persistence.database import get_session, get_pool_stats

router = APIRouter()


@router.get("/metrics/performance")
async def performance_metrics():
    """
    Métricas de rendimiento del backend.
    """
    import psutil
    import os

    process = psutil.Process(os.getpid())

    # Uso de CPU y RAM del proceso
    cpu_percent = process.cpu_percent(interval=0.1)
    memory_info = process.memory_info()

    # Estadísticas del pool de DB
    pool_stats = get_pool_stats()

    # Latencia de PostgreSQL
    async with get_session() as session:
        start = time.time()
        await session.execute(text("SELECT 1"))
        db_latency_ms = (time.time() - start) * 1000

    # Estadísticas de Redis
    import redis.asyncio as redis
    r = redis.from_url(settings.redis_url)

    start = time.time()
    await r.ping()
    redis_latency_ms = (time.time() - start) * 1000

    # Info del sistema
    system_memory = psutil.virtual_memory()

    return {
        "process": {
            "cpu_percent": cpu_percent,
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "threads": process.num_threads(),
        },
        "database": {
            "pool_size": pool_stats["pool_size"],
            "checked_out": pool_stats["checked_out"],
            "overflow": pool_stats["overflow"],
            "latency_ms": db_latency_ms,
        },
        "redis": {
            "latency_ms": redis_latency_ms,
        },
        "system": {
            "memory_total_mb": system_memory.total / 1024 / 1024,
            "memory_available_mb": system_memory.available / 1024 / 1024,
            "memory_percent": system_memory.percent,
        },
    }


@router.get("/metrics/slow-queries")
async def slow_queries():
    """
    Queries lentas de PostgreSQL (últimos 10 minutos).
    Requiere pg_stat_statements extension.
    """
    async with get_session() as session:
        result = await session.execute(text("""
            SELECT
                query,
                calls,
                mean_exec_time,
                max_exec_time,
                rows
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY mean_exec_time DESC
            LIMIT 10
        """))

        return {
            "slow_queries": [
                {
                    "query": row[0][:100] + "..." if len(row[0]) > 100 else row[0],
                    "calls": row[1],
                    "mean_time_ms": row[2],
                    "max_time_ms": row[3],
                    "rows": row[4],
                }
                for row in result.all()
            ]
        }
```

---

## ✅ Checklist de Implementación

### Semana 1: Índices y Query Optimization
- [ ] Crear todos los índices estratégicos
- [ ] Optimizar query del dashboard (single query con JOINs)
- [ ] Optimizar query de listado de claves
- [ ] Ejecutar ANALYZE en todas las tablas
- [ ] Medir mejora de latencia

### Semana 2: Caché Multi-Nivel
- [ ] Implementar LayeredCache (memoria + Redis)
- [ ] Cachear dashboard con TTL de 15 minutos
- [ ] Invalidar caché cuando hay cambios
- [ ] Medir hit rate del caché

### Semana 3: Backend Optimizations
- [ ] Instalar httptools y uvloop
- [ ] Configurar Uvicorn con múltiples workers
- [ ] Implementar GZip middleware
- [ ] Habilitar parallel query execution
- [ ] Medir throughput del backend

### Semana 4: Frontend Optimizations
- [ ] Configurar Caddy para static file caching
- [ ] Implementar lazy loading de imágenes
- [ ] Optimizar HTTP client de la APK
- [ ] Implementar caché local en la APK
- [ ] Medir tiempo de carga de la Mini App

### Semana 5: Monitoreo
- [ ] Implementar endpoint de performance metrics
- [ ] Configurar alertas de latencia alta
- [ ] Monitorear slow queries
- [ ] Dashboard de métricas en tiempo real

---

## 🎯 Métricas de Éxito

| Métrica | Antes | Después (Objetivo) |
|---------|-------|-------------------|
| Latencia dashboard (p95) | 300ms | <100ms |
| Latencia listado claves (p95) | 200ms | <80ms |
| Throughput backend | 50 req/s | 150 req/s |
| Cache hit rate | 0% | >80% |
| Tiempo de carga Mini App | 3s | <1s |
| RAM backend | 500MB | 350MB |

---

*Documento versión 1.0 - Fecha: Marzo 2026*
