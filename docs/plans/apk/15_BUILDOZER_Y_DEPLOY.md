# 15 — Buildozer y Deploy de la APK

## Contexto del Flujo de Trabajo

Tú programas en el VPS usando **Claude Code CLI**. La APK **nunca se compila en el VPS** (2GB RAM no es suficiente). El flujo completo es:

```
VPS (Claude Code CLI)           GitHub Actions              Tu Móvil
       │                              │                         │
       │ Escribes y pruebas código    │                         │
       │ del backend y de la APK      │                         │
       │                              │                         │
       │── git push tag v1.0.0 ──────►│                         │
       │                              │ Compila APK             │
       │                              │ (7GB RAM, ~30 min)      │
       │                              │ Firma APK               │
       │                              │ Sube a GitHub Releases  │
       │                              │                         │
       │                              │── Notifica al admin ───►│ (via bot Telegram)
       │                              │                         │
       │                              │                         │ Descarga .apk
       │                              │                         │ Instala manualmente
       │                              │                         │ Prueba funcionalidad
```

---

## Workflow: `.github/workflows/build_apk.yml`

Este archivo se crea nuevo junto a los workflows existentes (`ci.yml`, `deploy.yml`, etc.).

Se dispara **solo** cuando se crea un tag que empieza con `apk-v` (ej: `apk-v1.0.0`). Esto lo separa del deploy del bot que usa tags `v*`.

```
Trigger:    git tag apk-v1.0.0 && git push --tags
Resultado:  bin/usipipo-1.0.0-release.apk en GitHub Releases
Tiempo:     ~25-35 minutos (primera vez ~60 min por caché vacío)
RAM usada:  ~4-5 GB en el runner de GitHub Actions
```

### Estructura del workflow paso a paso:

```
PASO 1: Checkout del código
        └── actions/checkout@v4

PASO 2: Cache del SDK de Android y Buildozer
        └── actions/cache@v4
            ├── Cache key: buildozer-sdk-{hash de buildozer.spec}
            └── Paths: ~/.buildozer/android/platform/
            (Primera compilación: descarga ~2GB. Siguientes: usa cache.)

PASO 3: Instalar dependencias del sistema
        └── apt-get: openjdk-17-jdk, build-essential, git, zip, unzip,
                     libffi-dev, libssl-dev, autoconf, libtool, pkg-config,
                     zlib1g-dev, python3-pip

PASO 4: Setup Python 3.11

PASO 5: Instalar Buildozer y Cython
        └── pip install buildozer cython

PASO 6: Compilar la APK (desde android_app/)
        └── cd android_app && buildozer android release
        └── Genera: android_app/bin/usipipo-*.apk (sin firmar aún)

PASO 7: Firmar la APK
        ├── Restaura el keystore desde GitHub Secret (base64 → archivo .keystore)
        └── apksigner sign --ks usipipo.keystore ...
            Resultado: android_app/bin/usipipo-1.0.0-release-signed.apk

PASO 8: Crear GitHub Release con el APK
        └── softprops/action-gh-release@v2
            ├── Tag: apk-v1.0.0
            ├── Nombre: "uSipipo VPN Android v1.0.0"
            ├── Asset: usipipo-1.0.0-release-signed.apk
            └── Notas: changelog automático del commit

PASO 9: Notificar al admin por Telegram (opcional pero muy útil)
        └── curl a Telegram API con link de descarga directo al APK
```

---

## Secrets de GitHub Necesarios

Estos secrets se configuran en: `GitHub repo → Settings → Secrets and variables → Actions`

| Secret | Descripción | Cómo obtenerlo |
|---|---|---|
| `KEYSTORE_BASE64` | Contenido del .keystore en base64 | `base64 -w 0 usipipo.keystore` |
| `KEYSTORE_PASSWORD` | Contraseña del keystore | La que elegiste al crear el keystore |
| `KEY_ALIAS` | Alias de la clave dentro del keystore | `usipipo_key` (el que definiste) |
| `KEY_PASSWORD` | Contraseña de la clave | Generalmente igual al KEYSTORE_PASSWORD |
| `TELEGRAM_BOT_TOKEN` | Para notificar al admin | El mismo del bot (ya lo tienes) |
| `TELEGRAM_ADMIN_ID` | Tu telegram_id como admin | Ya lo tienes en el .env del VPS |

---

## Generación del Keystore (Una Sola Vez)

Se hace **en tu PC local o en cualquier máquina con Java**, nunca en el VPS y nunca en GitHub Actions:

```bash
keytool -genkey -v \
  -keystore usipipo.keystore \
  -alias usipipo_key \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=uSipipo VPN, OU=Mobile, O=uSipipo, C=CU"
```

Después de crearlo:
```bash
# Convertir a base64 para GitHub Secrets
base64 -w 0 usipipo.keystore > keystore_b64.txt
# Copiar el contenido de keystore_b64.txt al secret KEYSTORE_BASE64
```

Guardar `usipipo.keystore` en un lugar seguro (KeePass, Bitwarden, etc.). Es irremplazable.

---

## Cómo Hacer un Release Completo desde el VPS

```bash
# En el VPS con Claude Code CLI o directamente en la terminal:

# 1. Asegurarse de que el código está en el branch correcto
git status
git checkout develop   # o main según tu flujo

# 2. Actualizar la versión en buildozer.spec y version.py de android si aplica
# (editar android_app/buildozer.spec → version = 1.0.0)

# 3. Commit del código listo
git add android_app/ infrastructure/api/android/
git commit -m "feat: APK v1.0.0 - módulos auth, dashboard, claves, compras"

# 4. Push del branch normal (dispara ci.yml - tests del bot, NO compila APK)
git push origin develop

# 5. Cuando estés listo para el APK, crear el tag especial
git tag apk-v1.0.0
git push origin apk-v1.0.0

# GitHub Actions arranca automáticamente build_apk.yml
# ~30 minutos después recibes una notificación en Telegram
# con el enlace directo para descargar el APK
```

---

## Instalar el APK en tu Móvil

Una vez que GitHub Actions termina y el APK está en Releases:

```
1. En tu Android: Ajustes → Seguridad → "Fuentes desconocidas" → Activar
   (o en Android 8+: Ajustes → Apps → Chrome/Telegram → "Instalar apps desconocidas")

2. Opción A — Desde el móvil directamente:
   - Abre el enlace de descarga en Chrome del móvil
   - Descarga el .apk
   - Toca la notificación de descarga → Instalar

3. Opción B — Desde el PC con ADB (más rápido para pruebas frecuentes):
   adb install -r usipipo-1.0.0-release-signed.apk

4. Verificar la instalación:
   - La app aparece en el launcher con el ícono de uSipipo
   - Al abrirla, debe mostrar la pantalla de splash
```

---

## Actualizar la APK (Versiones Futuras)

El proceso es idéntico. Android reconoce que es una actualización porque:
- El `package.name` en `buildozer.spec` es siempre `org.usipipo`
- La firma del keystore es la misma

```bash
# Solo cambiar la versión en buildozer.spec
# version = 1.1.0
git tag apk-v1.1.0
git push origin apk-v1.1.0
# GitHub Actions compila → APK se instala encima de la anterior sin perder datos
```

---

## Caché de GitHub Actions (Para No Esperar 60 Min Siempre)

La primera compilación descarga el Android SDK + NDK (~2GB) y compila todas las
dependencias de Python nativo (cryptography, Pillow, etc.). Esto toma ~60 minutos.

Las compilaciones siguientes usan el caché de `~/.buildozer/android/platform/` y
toman ~25-30 minutos. El caché se invalida automáticamente cuando cambia el
`buildozer.spec` (o cuando se elimina manualmente desde GitHub → Actions → Caches).

---

## Versioning Tag Convention

Para no confundir los tags del bot con los de la APK:

| Tag | Qué dispara | Resultado |
|---|---|---|
| `v1.2.3` | `deploy.yml` | Deploy del bot al VPS |
| `apk-v1.0.0` | `build_apk.yml` | Compilación y release del APK |

Ambos pueden existir en el mismo commit o en commits diferentes según corresponda.
