# 03 — Módulo de Autenticación

## Objetivo
Permitir que un usuario que ya existe en el ecosistema uSipipo (bot de Telegram) inicie sesión en la APK de forma segura, sin contraseñas, usando su identidad de Telegram como factor de autenticación.

---

## Pantallas del Módulo

### Pantalla 1: Splash / Bienvenida
- Se muestra al iniciar la APK por primera vez o cuando no hay JWT guardado
- Elementos: Logo uSipipo con efecto neon, tagline, botón "Iniciar Sesión con Telegram"
- Fondo: `--bg-void (#0a0a0f)` con grid overlay animado (igual al mini app web)
- Animación: Logo con efecto glitch en el primer render

### Pantalla 2: Ingreso de Identificador Telegram
- Campo de texto para ingresar el `@username` de Telegram O el `telegram_id` numérico
- Nota informativa: "Debes tener cuenta activa en @uSipipoBot"
- Botón "Enviar Código"
- Indicador de carga mientras se hace la petición al backend

### Pantalla 3: Verificación OTP
- 6 campos de un dígito cada uno (estilo bancario) para ingresar el código
- Contador regresivo de 5 minutos
- Enlace "Reenviar código" (habilitado solo cuando el contador llega a 0)
- Nota: "Revisa tu chat con @uSipipoBot"
- Botón "Verificar"

### Pantalla 4: Éxito de Login
- Animación breve de confirmación (ícono check con glow cyan)
- Transición automática al Dashboard después de 1.5 segundos

---

## Flujo de Autenticación Detallado

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO DE LA APK                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────┐
               │  ¿Existe JWT en          │
               │  EncryptedStorage?       │
               └──────────┬───────────────┘
                          │
             ┌────────────┴────────────┐
             │ NO                      │ SÍ
             ▼                         ▼
    [Splash Screen]          ┌─────────────────────┐
         │                   │  ¿JWT válido?        │
         │                   │  (no expirado)       │
         ▼                   └──────┬───────────────┘
[Pantalla Ingreso ID]               │
         │                ┌─────────┴──────────┐
         │                │ SÍ                  │ NO
         │                ▼                     ▼
         │          [Dashboard]        [Renovar JWT]
         │                                      │
         │                             ┌────────▼────────┐
         │                             │ POST /auth/      │
         │                             │ refresh         │
         │                             │ {jwt: old_jwt}  │
         │                             └────────┬────────┘
         │                                      │
         │                           ┌──────────┴──────────┐
         │                           │ OK                   │ FAIL
         │                           ▼                      ▼
         │                    [Nuevo JWT]           [Splash Screen]
         │                    [Dashboard]           (sesión expirada)
         │
         ▼
[POST /auth/request-otp]
{identifier: "@username" | telegram_id}
         │
         ▼
┌────────────────────────────┐
│  Backend:                  │
│  1. Busca usuario en DB    │
│  2. ¿Existe?               │
└──────────┬─────────────────┘
           │
  ┌────────┴────────┐
  │ NO              │ SÍ
  ▼                 ▼
[Error: "Usuario   [Genera OTP]
 no registrado.    [Guarda en Redis]
 Activa bot"]      [TTL: 5 min]
                   [Envía por bot]
                        │
                        ▼
               [Pantalla OTP]
                        │
                        ▼
               [POST /auth/verify-otp]
               {identifier, otp}
                        │
               ┌────────┴────────┐
               │                 │
               ▼                 ▼
          [OTP válido]    [OTP inválido]
               │                 │
               ▼                 ▼
          [Genera JWT]    [Error + intentos]
          [24h expiry]    [Máx 3 intentos]
               │          [Luego: bloqueo 5 min]
               ▼
     [Guarda JWT local]
     [EncryptedStorage]
               │
               ▼
          [Dashboard]
```

---

## Seguridad del Módulo Auth

### Protección contra Brute Force OTP

El backend implementa las siguientes restricciones:

1. **Máximo 3 intentos fallidos de OTP** por telegram_id por ventana de 5 minutos. Al tercer fallo, el OTP se invalida y se requiere solicitar uno nuevo.

2. **Rate limiting por IP en el endpoint OTP:** máximo 5 solicitudes de OTP por IP por hora. Esto previene que un atacante genere OTPs masivamente.

3. **Rate limiting por telegram_id:** máximo 3 solicitudes de OTP por telegram_id por hora. Evita el abuso aunque se cambien de IP.

4. **OTP de un solo uso:** una vez validado correctamente, el OTP se elimina de Redis inmediatamente. No puede reutilizarse.

5. **OTP no predecible:** se genera con `secrets.randbelow(1000000)` con padding a 6 dígitos. No es secuencial ni predecible.

### Almacenamiento Seguro del JWT en la APK

El JWT se almacena usando el sistema de keystore de Android a través de la librería `keyring`. En Android, `keyring` usa `android.security.keystore` internamente, que es el almacén de claves protegido por hardware cuando está disponible. Esto significa que el JWT no puede ser leído por otras apps ni accedido en un backup sin cifrar de Android.

**No se debe usar SharedPreferences ni archivos planos para guardar el JWT.**

### Estructura del JWT de Android

El JWT que el backend emite para la APK tiene una estructura ligeramente diferente al de la mini app web para poder distinguir el origen:

```json
{
  "sub": "telegram_id_del_usuario",
  "client": "android_apk",
  "iat": 1234567890,
  "exp": 1234654290,
  "jti": "uuid-unico-para-revocar"
}
```

El campo `client: "android_apk"` permite al backend aplicar políticas diferentes según el cliente (por ejemplo, endpoints solo accesibles desde la APK).

El campo `jti` (JWT ID) permite revocar tokens individuales si el usuario cierra sesión desde otro dispositivo o si se detecta actividad sospechosa.

### Cierre de Sesión

Al cerrar sesión, la APK realiza dos acciones:

1. Envía `POST /auth/logout` al backend con el JWT actual → el backend agrega el `jti` a una blacklist en Redis (TTL = tiempo restante del JWT)
2. Elimina el JWT del almacenamiento local (`keyring.delete_password(...)`)

---

## Flujo de Renovación de Sesión (Refresh Silencioso)

Cuando el JWT tiene menos de 2 horas de vida restante, la APK automáticamente solicita uno nuevo en segundo plano sin interrumpir al usuario:

```
[APK en uso]
     │
     │ Cada 30 min, en background:
     ▼
[Verifica exp del JWT]
     │
     ├── exp > 2h → No hace nada
     │
     └── exp < 2h → POST /auth/refresh
                    {Authorization: Bearer <old_jwt>}
                         │
                    ┌────┴─────┐
                    │ OK       │ Error
                    ▼          ▼
              [Nuevo JWT]  [Muestra banner:
              [Guarda]      "Sesión expirada,
                             vuelve a iniciar"]
```

---

## Consideraciones de UX

- El código OTP debe mostrarse en el chat de Telegram en un formato que sea fácil de tipear: `🔐 Tu código de verificación: **123 456**` (separado en dos grupos de 3).
- Los 6 campos de la pantalla OTP deben auto-avanzar al siguiente campo al ingresar cada dígito (igual que apps bancarias como Bancolombia o Nequi).
- Si el usuario tiene Telegram instalado en el mismo dispositivo, se puede abrir directamente con un botón "Abrir Telegram" que lo lleve al chat con el bot.
- El contador regresivo debe tener un color que cambie de cyan a ámbar a rojo según se acerca a 0.
