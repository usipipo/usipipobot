# Plan: Migración de ngrok a DuckDNS + Caddy

**Fecha:** 2026-02-24
**Issue:** #174
**Branch:** develop

## Resumen

Migrar el sistema de túneles de ngrok a DuckDNS + Caddy para obtener un dominio fijo con HTTPS automático, eliminando la dependencia de ngrok y sus URLs dinámicas.

## Motivación

- ngrok free cambia la URL en cada reinicio
- Requiere actualizar manualmente la URL en BotFather
- DuckDNS proporciona un dominio fijo gratuito (usipipo.duckdns.org)
- Caddy proporciona HTTPS automático con Let's Encrypt

## Componentes a Eliminar

1. **Servicio ngrok** (`infrastructure/tunnel/ngrok_service.py`)
   - Clase NgrokService con métodos start/stop/get_webhook_url

2. **Módulo de túneles** (`infrastructure/tunnel/__init__.py`)
   - Import de NgrokService

3. **Dependencia** (`requirements.txt`)
   - pyngrok==7.2.3

4. **Configuración** (`config.py`)
   - NGROK_AUTH_TOKEN
   - NGROK_SUBDOMAIN

5. **Código en main.py** (líneas 81-93)
   - Inicialización de ngrok tunnel

6. **Documentación afectada**
   - docs/tron_dealer_registration.md
   - docs/plans/2026-02-24-tron-dealer-webhook.md
   - example.env

## Componentes Nuevos

### 1. Servicio DuckDNS (`infrastructure/dns/duckdns_service.py`)

```python
class DuckDNSService:
    def __init__(self, domain: str, token: str):
        self.domain = domain
        self.token = token
    
    async def update_ip(self) -> bool:
        """Actualiza la IP en DuckDNS."""
        pass
    
    def get_public_url(self) -> str:
        """Retorna la URL pública."""
        return f"https://{self.domain}.duckdns.org"
    
    def setup_cron_job(self) -> None:
        """Configura el cron job para actualización automática."""
        pass
```

### 2. Configuración Caddy (`config/Caddyfile`)

```
usipipo.duckdns.org {
    reverse_proxy localhost:8000
    encode gzip
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }
}
```

### 3. Script de Instalación (`scripts/setup-duckdns-caddy.sh`)

- Instalar Caddy
- Crear directorio ~/duckdns
- Crear script duck.sh para actualizar IP
- Configurar cron job (cada 5 minutos)
- Crear Caddyfile
- Iniciar servicios

### 4. Variables de Entorno (`.env`)

```
DUCKDNS_DOMAIN=usipipo
DUCKDNS_TOKEN=tu_duckdns_token_aqui
PUBLIC_URL=https://usipipo.duckdns.org
```

## URLs Finales

| Servicio | URL |
|----------|-----|
| Mini App | https://usipipo.duckdns.org/miniapp/ |
| Webhook Tron Dealer | https://usipipo.duckdns.org/api/v1/webhooks/tron-dealer |
| API | https://usipipo.duckdns.org/api/ |

## Cambios en config.py

```python
# DNS DINÁMICO (DuckDNS)
DUCKDNS_DOMAIN: Optional[str] = Field(
    default=None,
    description="Dominio de DuckDNS (sin .duckdns.org)"
)
DUCKDNS_TOKEN: Optional[str] = Field(
    default=None,
    description="Token de DuckDNS"
)
PUBLIC_URL: Optional[str] = Field(
    default=None,
    description="URL pública del servidor"
)

# Propiedad computada
@property
def webhook_url(self) -> str:
    if self.PUBLIC_URL:
        return f"{self.PUBLIC_URL}/api/v1/webhooks/tron-dealer"
    return f"http://localhost:{self.API_PORT}/api/v1/webhooks/tron-dealer"
```

## Cambios en main.py

Eliminar bloque ngrok (líneas 81-93) y reemplazar con inicialización de DuckDNS si está configurado.

## Testing

1. Verificar que DuckDNS actualiza la IP correctamente
2. Verificar que Caddy sirve HTTPS
3. Verificar que la Mini App es accesible
4. Verificar que los webhooks funcionan

## Rollback

Si algo falla, se puede revertir a ngrok:
1. Restaurar archivos eliminados desde git
2. Restaurar configuración en config.py
3. Restaurar código en main.py

## Próximos Pasos

1. Crear issue en GitHub
2. Eliminar archivos de ngrok
3. Implementar DuckDNSService
4. Actualizar config.py
5. Actualizar main.py
6. Actualizar requirements.txt
7. Actualizar documentación
8. Crear script de instalación
9. Probar en entorno de desarrollo
