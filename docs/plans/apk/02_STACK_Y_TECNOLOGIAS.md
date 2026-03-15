# 02 — Stack Técnico y Tecnologías

## Decisión Final de Framework

### Kivy 2.3.x + KivyMD 2.0.x + Buildozer 1.5.x

Esta combinación es la única opción madura en el ecosistema Python para Android en 2026. A continuación el análisis completo.

---

## Comparativa de Opciones Python para Android

| Criterio | Kivy + KivyMD | BeeWare (Toga) | PyDroid (solo dev) |
|---|---|---|---|
| Madurez | Alta (2011) | Media (2014, inestable) | No aplica |
| Componentes UI | Ricos (KivyMD) | Limitados | No aplica |
| Buildozer support | Nativo | Parcial (Briefcase) | No |
| Material Design 3 | Sí (KivyMD) | No | No |
| Animaciones | Nativas OpenGL | Básicas | No |
| VPS compile | Sí (Docker) | Problemas frecuentes | No |
| Costo | 100% gratuito | 100% gratuito | No aplica |
| Comunidad | Muy activa | Creciendo | No |

**Veredicto:** Kivy + KivyMD es la elección correcta para este proyecto.

---

## Stack Completo de la APK

### Capa de UI y Presentación
- **Kivy 2.3.x** — Motor de renderizado OpenGL ES, sistema de widgets, eventos
- **KivyMD 2.0.x** — Componentes Material Design 3: MDCard, MDBottomNavigation, MDDialog, MDProgressBar, MDTextField, MDRaisedButton, MDSnackbar
- **Kivy Garden** — Widgets adicionales: graph (para gráficas de uso), qrcode (para mostrar QR de claves)

### Capa de Datos y Red
- **httpx 0.27.x** — Cliente HTTP asíncrono para llamadas al backend (mejor que requests para async)
- **asyncio** — Manejo de operaciones asíncronas (peticiones en background sin bloquear UI)
- **pydantic 2.x** — Validación y parsing de respuestas JSON del backend

### Capa de Seguridad Local
- **cryptography 42.x** — Encriptación del almacenamiento local (JWT, configuración)
- **keyring** — Integración con el keystore de Android para guardar el JWT de forma segura
- **certifi** — Bundle de certificados CA actualizado (certificate pinning)

### Capa de Utilidades
- **qrcode 7.x** — Generación de imágenes QR para las claves VPN
- **Pillow 10.x** — Procesamiento de imágenes (conversión de QR a textura Kivy)
- **python-dotenv** — Variables de entorno del build

### Herramienta de Compilación
- **Buildozer 1.5.x** — Empaquetado automático de Python a APK Android
- **python-for-android (p4a)** — Motor interno de Buildozer, maneja NDK/SDK

---

## Archivo buildozer.spec (Configuración Clave)

El archivo `buildozer.spec` es el corazón de la compilación. Los campos críticos son:

### Permisos Android necesarios
```
android.permissions = INTERNET, ACCESS_NETWORK_STATE, VIBRATE, RECEIVE_BOOT_COMPLETED
```

- `INTERNET` — Para peticiones al backend
- `ACCESS_NETWORK_STATE` — Para detectar si hay conexión antes de hacer peticiones
- `VIBRATE` — Para feedback háptico en acciones importantes (conexión VPN, pago exitoso)
- `RECEIVE_BOOT_COMPLETED` — Para reiniciar polling de notificaciones al iniciar el dispositivo

### Librerías a incluir en el APK
```
requirements = python3,kivy,kivymd,httpx,cryptography,qrcode,Pillow,pydantic,certifi,keyring
```

### Versión mínima de Android
```
android.minapi = 26
android.targetapi = 34
```

- `minapi 26` — Android 8.0 Oreo (2017). Cubre el 98% de dispositivos activos en LATAM.
- `targetapi 34` — Android 14. Requerimiento de Google Play si se distribuye ahí.

### Orientación y pantalla completa
```
orientation = portrait
fullscreen = 0
```

---

## Estructura de Compilación con Buildozer

```
Flujo de compilación en el VPS:

1. buildozer android debug
   ↓
   Descarga Android SDK + NDK (primera vez: ~2GB)
   ↓
   python-for-android compila las dependencias nativas
   (httpx, cryptography, Pillow requieren compilación C)
   ↓
   Empaqueta todo el código Python + assets
   ↓
   Genera: bin/usipipo-1.0.0-debug.apk

2. buildozer android release
   ↓
   Mismo proceso pero sin modo debug
   ↓
   Firma con keystore (jarsigner / apksigner)
   ↓
   Genera: bin/usipipo-1.0.0-release.apk
```

### Consideraciones de RAM para el VPS (2GB)
La compilación de Buildozer consume entre 1.2 y 1.8 GB de RAM. Las opciones son:

**Opción A (Recomendada): Compilar en GitHub Actions (gratis)**
- Se configura un workflow `.github/workflows/build_apk.yml`
- GitHub Actions provee 7GB RAM — suficiente sin problemas
- El APK compilado se sube como Release artifact automáticamente

**Opción B: Compilar en el VPS con swap**
- Agregar 2GB de swap al VPS antes de compilar
- `sudo fallocate -l 2G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`
- Compilación lenta (~30 min) pero funcional

---

## Versiones del Backend que Necesitan Actualizarse

El backend existente (FastAPI) requiere estos nuevos módulos para soportar la APK:

### Nuevo módulo: `/api/v1/` (rutas Android)
- Archivo: `infrastructure/api/routes_android.py`
- Se monta en el FastAPI existente sin modificar rutas actuales

### Nuevo módulo: OTP Authentication
- Archivo: `infrastructure/api/android_auth.py`
- Requiere: Redis para almacenar OTPs temporales (TTL 5 minutos)

### Dependencias nuevas en requirements.txt del backend
```
redis==5.0.x          # Para OTPs temporales
python-jose[cryptography]==3.3.x  # Para JWT Android (puede compartir con mini app)
```

---

## Entorno de Desarrollo Recomendado

Para desarrollar la APK en el VPS sin compilar en cada cambio, el flujo recomendado es:

### Desarrollo con Kivy en Desktop (Linux/Mac)
1. Instalar Kivy en el entorno virtual del PC local
2. Desarrollar y probar en desktop (Kivy corre en Linux/Mac/Windows)
3. La UI se ve igual en desktop que en Android
4. Solo compilar con Buildozer para pruebas en dispositivo real

### Estructura del entorno virtual APK
```
usipipo-apk/
├── venv/               ← Kivy + dependencias para desarrollo desktop
├── buildozer.spec      ← Configuración de compilación
├── main.py             ← Entry point de Kivy
├── assets/             ← Imágenes, fuentes, íconos
└── src/                ← Código fuente de la APK
```

---

## Fuentes Tipográficas

Para mantener consistencia con el mini app web (que usa JetBrains Mono), la APK incluirá:

- **JetBrains Mono** — Para datos técnicos: claves VPN, direcciones wallet, estadísticas
- **Roboto** — Font por defecto de Android/KivyMD para textos generales

Ambas fuentes se incluyen como archivos `.ttf` en el directorio `assets/fonts/` del proyecto APK y se declaran en `buildozer.spec` bajo `source.include_exts`.
