# uSipipo VPN - Android APK

Aplicación Android para gestión de VPN uSipipo con autenticación OTP.

## 📋 Descripción

APK Android desarrollada con Kivy + KivyMD que proporciona:

- **Autenticación OTP**: Login seguro con código de verificación
- **Gestión VPN**: Crear y administrar claves WireGuard/Outline
- **Paquetes de Datos**: Comprar y renovar paquetes de datos
- **Soporte**: Sistema de tickets integrado

## 🏗️ Arquitectura

Clean Architecture adaptada a KivyMD:

```
android_app/
├── src/
│   ├── screens/          # Pantallas (Splash, Login, OTP, Dashboard)
│   ├── services/         # Lógica de negocio (API, Auth)
│   ├── storage/          # Almacenamiento (JWT, Preferences)
│   ├── components/       # Widgets reutilizables (OTP, NeonButton)
│   ├── kv/               # Diseños Kivy (.kv files)
│   ├── utils/            # Utilidades (logger)
│   └── config.py         # Configuración global
├── assets/
│   ├── fonts/            # Fuentes (JetBrainsMono)
│   └── images/           # Imágenes (logo, iconos)
├── tests/                # Tests unitarios
├── main.py               # Entry point
└── buildozer.spec        # Configuración Buildozer
```

## 🚀 Instalación

### Requisitos

- Python 3.11+
- Linux (Ubuntu 22.04+ recomendado)
- Android SDK (para compilar APK)

### Desarrollo Desktop

```bash
# Clonar repositorio
cd /path/to/usipipobot/.worktrees/apk-auth

# Crear entorno virtual
cd android_app
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements-android.txt

# Ejecutar en desktop
python main.py
```

### Compilar APK

```bash
# Instalar buildozer
pip install buildozer

# Configurar (primera vez)
buildozer init

# Compilar APK debug
buildozer -v android debug

# Compilar APK release
buildozer -v android release
```

## 🎨 Diseño

Tema **Cyberpunk** con colores neón:

| Color | RGB | Hex |
|-------|-----|-----|
| Neon Cyan | [0, 0.941, 1, 1] | #00f0ff |
| Neon Magenta | [1, 0, 0.667, 1] | #ff00aa |
| Terminal Green | [0, 1, 0.255, 1] | #00ff41 |
| BG Void | [0.039, 0.039, 0.059, 1] | #0a0a0f |

## 🔐 Flujo de Autenticación

1. **Splash Screen**: Verifica sesión activa
2. **Login Screen**: Ingresa @usuario o Telegram ID
3. **OTP Screen**: Ingresa código de 6 dígitos
4. **Dashboard**: Panel principal de gestión

## 📱 Pantallas

### SplashScreen
- Logo animado
- Verificación automática de JWT
- Navegación a login o dashboard

### LoginScreen
- Input de Telegram (@username o ID)
- Validación de formato
- Enlace a bot de signup

### OtpScreen
- 6 campos de input numérico
- Countdown de expiración
- Reenvío de código

### DashboardScreen
- Resumen de usuario
- Accesos rápidos:
  - Mis Claves VPN
  - Paquetes de Datos
  - Soporte
- Cerrar sesión

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=src -v

# Tests asíncronos
pytest tests/ -v --asyncio-mode=auto
```

## 📦 Estructura de Paquetes

| Paquete | Datos | Precio |
|---------|-------|--------|
| Basic | 10GB | $5/mes |
| Standard | 25GB | $10/mes |
| Advanced | 50GB | $18/mes |
| Premium | 100GB | $30/mes |

## 🔧 Configuración

### Variables de Entorno

```bash
# API Backend
USIPIPO_API_URL=https://tu-server.com/api/v1

# Buildozer
ANDROID_API=31
ANDROID_MINAPI=21
```

### buildozer.spec

Configuración principal:

```ini
[app]
title = uSipipo VPN
package.name = usipipo_vpn
package.domain = org.usipipo
source.dir = .
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==2.0.1.dev0,httpx,cryptography,keyring
orientation = portrait
```

## 🔗 Backend API

Endpoints utilizados:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/auth/request-otp` | POST | Solicitar código OTP |
| `/auth/verify-otp` | POST | Verificar código OTP |
| `/auth/logout` | POST | Cerrar sesión |

## 📝 Licencia

Misma licencia que el proyecto principal uSipipo VPN.

## 🤝 Contribución

1. Fork el repositorio
2. Crea rama de feature
3. Implementa cambios
4. Ejecuta tests
5. Crea Pull Request

## 📞 Soporte

- Bot Telegram: @usipipo_bot
- Email: soporte@usipipo.com
