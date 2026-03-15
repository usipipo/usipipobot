# 12 — Seguridad Integral del Ecosistema

## Filosofía de Seguridad

> **"Defense in Depth"** — La seguridad no es una capa, es una mentalidad que impregna cada decisión de diseño. Si una capa falla, la siguiente detiene el ataque.

El ecosistema uSipipo es un objetivo atractivo para atacantes porque maneja dinero (Stars, USDT), claves VPN activas, y datos personales de usuarios. Este documento define las medidas de seguridad en cada capa.

---

## CAPA 1: Seguridad de la APK Android

### 1.1 Almacenamiento Seguro de Credenciales

El JWT nunca se guarda en texto plano. Se usa el Android Keystore System:

```
Android Keystore (respaldado por hardware en dispositivos modernos)
└── Entrada "usipipo_jwt"
    └── Clave AES-256-GCM
        └── Encrypta el JWT
            └── El texto cifrado se guarda en un archivo interno de la app
```

Nadie fuera de la APK puede leer este valor, ni siquiera con root en muchos dispositivos modernos (si el hardware tiene Trusted Execution Environment).

**Qué NO hacer (prácticas prohibidas):**
- No usar `SharedPreferences` sin cifrar
- No guardar el JWT en un archivo en `/sdcard/` o almacenamiento externo
- No logear el JWT en logs de Android (`Logcat`) ni en archivos de log

### 1.2 Certificate Pinning

La APK no confía ciegamente en cualquier certificado HTTPS. Se configura certificate pinning contra el dominio del backend (`usipipo.duckdns.org`):

```
Proceso de Certificate Pinning:
1. Antes del release, se extrae el hash SHA-256 del certificado del servidor
2. Ese hash se embebe en el código de la APK (en la configuración de httpx)
3. Cada petición verifica que el certificado del servidor coincida con el hash embebido
4. Si no coincide (ataque MITM), la petición se rechaza con error y se notifica al usuario
```

**Consideración:** Cuando el certificado del servidor se renueve (cada 90 días con Let's Encrypt / Caddy), el hash del pin también debe actualizarse en la APK. Por esto, siempre se incluyen 2 pines en la APK: el certificado actual y el de respaldo (backup pin).

### 1.3 Ofuscación de Código Python

Python no tiene un compilador nativo que ofusque el código como Java/Kotlin con ProGuard. Sin embargo, se aplican estas medidas:

- **Compilación a bytecode .pyc:** python-for-android compila el código a `.pyc`, eliminando los archivos `.py` del APK. Un atacante que descompile el APK tendrá `.pyc`, no código legible directamente.
- **No hardcodear secrets:** ninguna URL, token, o clave secreta va en el código fuente. Todo se configura via variables en `buildozer.spec` o se obtiene del servidor.
- **No incluir credenciales de prueba** en la build de release.

### 1.4 Validación de Integridad de la APK

Para detectar APKs modificadas (repackaged APKs con malware):

- La APK se firma con un keystore privado único (`usipipo.keystore`)
- El backend puede verificar la firma del APK en peticiones críticas (opcional, para implementar en v2)
- Se publica solo en canales oficiales (enlace directo desde el bot de Telegram)

---

## CAPA 2: Seguridad de la Capa de Transporte

### 2.1 HTTPS Obligatorio

**La APK rechaza cualquier petición HTTP (sin S).** Si el backend responde en HTTP por error de configuración, la APK no continúa.

Esto se configura en httpx:
```
Nunca usar verify=False en producción.
Siempre usar HTTPS + certificate pinning.
```

### 2.2 JWT: Diseño Seguro

El JWT emitido para Android tiene estas características de seguridad:

- **Algoritmo:** HS256 con `SECRET_KEY` de 256 bits mínimo (ya en config.py)
- **Expiración:** 24 horas (`exp`)
- **Issued at:** incluido (`iat`) para detectar tokens muy viejos
- **JWT ID:** UUID único (`jti`) para poder revocar tokens individuales
- **Claim `client`:** `"android_apk"` para que el backend rechace tokens del miniapp web en endpoints Android y viceversa
- **Claim `sub`:** el `telegram_id` del usuario (identificador primario)

**Revocación:** cuando el usuario hace logout, el `jti` se guarda en Redis con TTL = tiempo restante del JWT. En cada request, el backend verifica que el `jti` no esté en la blacklist. Esto garantiza que un JWT robado sea inútil tras el logout.

### 2.3 Headers de Seguridad en Respuestas

El backend ya tiene `SecurityHeadersMiddleware`. Para las rutas Android, se asegura que incluyan:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Cache-Control: no-store
```

---

## CAPA 3: Seguridad del Backend API

### 3.1 Autenticación OTP: Protección Anti-Abuso

**Flujo de protección del OTP:**

```
NIVEL 1 - Rate limit por IP:
  5 solicitudes de OTP por IP por hora
  → Si se supera: 429 Too Many Requests

NIVEL 2 - Rate limit por identifier:
  3 solicitudes de OTP por telegram_id por hora
  → Si se supera: 429 + "Espera X minutos"

NIVEL 3 - Bloqueo por intentos fallidos:
  3 intentos incorrectos de OTP
  → El OTP se invalida en Redis
  → El usuario debe solicitar un nuevo OTP

NIVEL 4 - Bloqueo progresivo:
  Si en 1 hora hay más de 5 intentos fallidos
  → Bloqueo de 30 minutos para ese telegram_id
  → Alerta enviada al admin por Telegram
```

El almacenamiento de intentos fallidos se hace en Redis con TTL, sin tocar la base de datos PostgreSQL.

### 3.2 Rate Limiting por Endpoint

Se extiende el `RateLimitMiddleware` existente para cubrir las rutas Android:

| Endpoint | IPs Anónimas | Usuarios Autenticados |
|---|---|---|
| `POST /auth/request-otp` | 5/hora | N/A |
| `POST /auth/verify-otp` | 10/hora | N/A |
| `POST /keys/create` | N/A | 5/hora |
| `POST /payments/*/create` | N/A | 10/hora |
| `GET /dashboard/summary` | N/A | 60/min |
| `GET /notifications/pending` | N/A | 120/min |
| `POST /tickets/create` | N/A | 3/hora |

### 3.3 Validación Estricta de Inputs

Todos los inputs de la APK pasan por validación Pydantic en el backend:

- **Nombres de claves:** solo caracteres alfanuméricos, espacios y guiones. Máx 30 chars.
- **Comentarios de tickets:** máx 500 chars. Strip de HTML/scripts.
- **Direcciones wallet:** regex que valida formato TRC-20 antes de procesarla.
- **Tipos de paquete:** enum estricto, no acepta valores arbitrarios.
- **telegram_id en OTP:** debe ser un entero positivo, validado contra la DB.

### 3.4 Protección contra Inyección SQL

El backend ya usa SQLAlchemy con consultas parametrizadas. **Nunca se construyen queries SQL con concatenación de strings.** Esta protección ya existe y solo se extiende a las nuevas tablas.

### 3.5 Protección de Endpoints de Webhook

Los webhooks de TronDealer ya tienen validación de firma HMAC (`webhook_security_service.py`). Se mantiene esta protección. Los nuevos endpoints Android no son webhooks, son REST autenticados con JWT.

---

## CAPA 4: Protección contra DDoS

### 4.1 Primera Línea: Caddy (ya en producción)

Caddy actúa como reverse proxy y puede limitar conexiones. Se configura:

```caddyfile
# En el Caddyfile existente, agregar para rutas Android:
rate_limit {
    zone android_api {
        match path /api/v1/*
        key {remote_host}
        events 100
        window 1m
    }
}
```

Esto limita a 100 peticiones por minuto por IP antes de llegar al FastAPI.

### 4.2 Segunda Línea: Middleware FastAPI

El `RateLimitMiddleware` existente agrega una segunda capa de rate limiting en la aplicación.

### 4.3 Tercera Línea: Redis para Contadores

Los contadores de rate limiting se almacenan en Redis (no en memoria del proceso), lo que permite que los límites funcionen correctamente aunque haya múltiples workers de Gunicorn/uvicorn.

### 4.4 Protección del Endpoint de Polling

Los endpoints que la APK consulta frecuentemente (`/notifications/pending`, `/dashboard/summary`) tienen estas protecciones adicionales:

- **Cache de respuesta:** las respuestas se cachean en Redis por 15 segundos. Si múltiples dispositivos del mismo usuario consultan simultáneamente, la segunda petición no golpea la DB.
- **Respuesta vacía rápida:** si no hay notificaciones, la respuesta es inmediata sin consultas pesadas a la DB.

### 4.5 Respuesta a Ataques Detectados

Si el sistema detecta patrones de ataque (más de 500 peticiones en 1 minuto desde una IP):

1. La IP se bloquea automáticamente en Caddy por 1 hora
2. Se envía alerta al admin por Telegram: "🚨 Posible DDoS desde IP X.X.X.X"
3. El bloqueo se registra en la DB para análisis posterior

---

## CAPA 5: Seguridad de Datos de Usuarios

### 5.1 Datos Mínimos Necesarios

La APK solo solicita y almacena lo que necesita:
- **Del servidor:** se cachea el nombre/username para mostrar en UI. Nunca se cachea el `key_data` (strings de conexión VPN) en disco.
- **Localmente:** solo el JWT en el keystore. Nada más en disco.

### 5.2 Logs Sin Datos Sensibles

Los logs del backend no deben incluir:
- Strings de claves VPN (`ss://...` o configs WireGuard)
- Direcciones de billetera completas
- OTPs
- JWT completos (solo el `jti` si se necesita para debugging)

Se revisa el `logger.py` existente para asegurar que ningún endpoint nuevo loguee estos datos.

### 5.3 Comunicación entre Usuarios

La APK no tiene funcionalidad P2P ni comunicación entre usuarios. Esto elimina vectores de ataque como XSS, inyección de contenido malicioso en mensajes, etc.

---

## CAPA 6: Seguridad Operacional

### 6.1 Gestión del Keystore de Firma

El archivo `usipipo.keystore` para firmar el APK:
- **Nunca** va en el repositorio Git (`.gitignore` estricto)
- Se guarda en un gestor de secretos (KeePass local, Bitwarden, o variable en GitHub Secrets)
- Se hace backup en al menos 2 lugares seguros
- La contraseña del keystore debe ser diferente a todas las demás contraseñas del proyecto

### 6.2 Gestión del SECRET_KEY del Backend

La `SECRET_KEY` que firma los JWTs:
- Longitud mínima: 64 caracteres hexadecimales (generada con `openssl rand -hex 32`)
- **Rotación:** si se sospecha que está comprometida, se cambia y todos los JWTs existentes quedan inválidos automáticamente (usuarios deben re-login)
- No se comparte con el keystore de la APK

### 6.3 Plan de Respuesta a Incidentes

Si se detecta que el JWT secret fue comprometido:
1. Cambiar `SECRET_KEY` en el `.env` del servidor inmediatamente
2. Reiniciar el servidor → todos los JWTs existentes quedan inválidos
3. Limpiar la blacklist de Redis (ya no es necesaria con el nuevo secret)
4. Notificar a usuarios por Telegram: "Por seguridad, debes volver a iniciar sesión en la APK"
5. Investigar el vector de compromiso

Si se detecta que un `telegram_id` fue usado maliciosamente:
1. `PUT /admin/users/{telegram_id}/status` → `"blocked"`
2. El usuario bloqueado recibe 403 en todos los endpoints
3. Sus claves VPN se desactivan automáticamente
