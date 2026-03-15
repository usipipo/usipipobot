# 14 — Estructura del Proyecto APK (Integrada al Repo Existente)

## Principio de Integración

La APK **no es un repositorio separado**. Vive dentro del mismo repositorio `usipipobot` como un módulo hermano de `telegram_bot/`, `miniapp/` e `infrastructure/`. Esto mantiene todo el ecosistema en un solo lugar, facilita el trabajo con Claude Code CLI y permite compartir configuración y CI/CD.

---

## Árbol del Repositorio Completo (Post-Integración)

```
usipipobot/                                  ← Raíz del repo (sin cambios salvo lo marcado NEW)
│
├── .github/
│   └── workflows/
│       ├── ci.yml                           ← Existente (se modifica mínimamente)
│       ├── codeql.yml                       ← Existente (sin cambios)
│       ├── deploy.yml                       ← Existente (sin cambios)
│       ├── docker.yml                       ← Existente (sin cambios)
│       └── build_apk.yml                    ← NEW: Workflow compilación APK
│
├── android_app/                             ← NEW: Todo el código de la APK vive aquí
│   │
│   ├── buildozer.spec                       ← Configuración de compilación Buildozer
│   ├── main.py                              ← Entry point Kivy (≠ al main.py de la raíz)
│   ├── requirements-android.txt            ← Dependencias SOLO para la APK
│   ├── README.md                            ← Instrucciones para desarrollar/compilar
│   │
│   ├── assets/
│   │   ├── fonts/
│   │   │   ├── JetBrainsMono-Regular.ttf
│   │   │   └── JetBrainsMono-Bold.ttf
│   │   └── images/
│   │       ├── logo_usipipo.png
│   │       ├── icon_512.png
│   │       └── presplash.png
│   │
│   ├── src/
│   │   ├── config.py                        ← BASE_URL, versión APK, timeouts, cert hashes
│   │   ├── app.py                           ← Clase principal MDApp + ScreenManager
│   │   │
│   │   ├── screens/
│   │   │   ├── splash_screen.py
│   │   │   ├── login_screen.py
│   │   │   ├── otp_screen.py
│   │   │   ├── dashboard_screen.py
│   │   │   ├── keys_list_screen.py
│   │   │   ├── key_detail_screen.py
│   │   │   ├── create_key_screen.py
│   │   │   ├── shop_screen.py
│   │   │   ├── payment_stars_screen.py
│   │   │   ├── payment_usdt_screen.py
│   │   │   ├── payment_success_screen.py
│   │   │   ├── profile_screen.py
│   │   │   ├── referrals_screen.py
│   │   │   ├── wallet_screen.py
│   │   │   ├── history_screen.py
│   │   │   ├── tickets_screen.py
│   │   │   ├── ticket_detail_screen.py
│   │   │   ├── create_ticket_screen.py
│   │   │   ├── notifications_screen.py
│   │   │   └── about_screen.py
│   │   │
│   │   ├── components/
│   │   │   ├── neon_card.py
│   │   │   ├── data_progress_bar.py
│   │   │   ├── vpn_key_card.py
│   │   │   ├── package_card.py
│   │   │   ├── ticket_item.py
│   │   │   ├── otp_input.py
│   │   │   ├── skeleton_loader.py
│   │   │   ├── neon_button.py
│   │   │   ├── status_badge.py
│   │   │   ├── qr_display.py
│   │   │   ├── countdown_timer.py
│   │   │   └── bottom_nav.py
│   │   │
│   │   ├── services/
│   │   │   ├── api_client.py               ← Cliente HTTP + JWT + certificate pinning
│   │   │   ├── auth_service.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── keys_service.py
│   │   │   ├── payments_service.py
│   │   │   ├── user_service.py
│   │   │   ├── tickets_service.py
│   │   │   ├── notifications_service.py
│   │   │   └── qr_service.py
│   │   │
│   │   ├── storage/
│   │   │   ├── secure_storage.py           ← JWT en Android Keystore (keyring)
│   │   │   ├── cache_storage.py            ← Cache local encriptado
│   │   │   └── preferences_storage.py
│   │   │
│   │   ├── utils/
│   │   │   ├── formatters.py
│   │   │   ├── validators.py
│   │   │   ├── haptics.py
│   │   │   ├── clipboard.py
│   │   │   ├── deep_link.py
│   │   │   ├── share.py
│   │   │   └── logger.py
│   │   │
│   │   └── kv/
│   │       ├── splash.kv
│   │       ├── login.kv
│   │       ├── otp.kv
│   │       ├── dashboard.kv
│   │       ├── keys_list.kv
│   │       ├── key_detail.kv
│   │       ├── create_key.kv
│   │       ├── shop.kv
│   │       ├── payment_stars.kv
│   │       ├── payment_usdt.kv
│   │       ├── profile.kv
│   │       ├── tickets.kv
│   │       └── components.kv
│   │
│   └── tests/
│       ├── test_auth_service.py
│       ├── test_validators.py
│       ├── test_formatters.py
│       └── test_api_client.py
│
├── infrastructure/
│   └── api/
│       ├── server.py                        ← Existente (1 línea nueva: mount /api/v1/)
│       ├── middleware/                      ← Existente (sin cambios)
│       ├── webhooks/                        ← Existente (sin cambios)
│       └── android/                         ← NEW: Rutas REST para la APK
│           ├── __init__.py
│           ├── router.py
│           ├── auth.py
│           ├── dashboard.py
│           ├── keys.py
│           ├── payments.py
│           ├── user.py
│           ├── tickets.py
│           ├── notifications.py
│           └── deps.py
│
├── infrastructure/
│   └── persistence/
│       └── postgresql/
│           └── models/
│               └── android_notification.py  ← NEW: Modelo SQLAlchemy
│
├── migrations/
│   └── versions/
│       └── YYYYMMDD_android_notifications.py ← NEW: Migración Alembic
│
├── docs/
│   ├── ... (existentes sin cambios)
│   └── android/                             ← NEW: Docs de la APK (estos documentos)
│       ├── 00_INDEX.md
│       ├── 01_ARQUITECTURA_GLOBAL.md
│       └── ... (todos los .md del plan)
│
├── requirements.txt                         ← Existente (2 líneas nuevas: redis, python-jose)
├── main.py                                  ← Existente (sin cambios — es el bot)
├── config.py                                ← Existente (sin cambios)
├── AGENTS.md                                ← Existente (se agrega sección Android)
├── QWEN.md                                  ← Existente (se agrega sección Android)
└── .gitignore                               ← Existente (se agrega sección Android)
```

---

## Archivos Existentes que Se Modifican

### `requirements.txt` — Solo estas 2 líneas nuevas al final:
```
# Android API Layer
redis==5.0.8
python-jose[cryptography]==3.3.0
```
Redis es necesario para los OTPs temporales y la blacklist de JWTs revocados.

### `infrastructure/api/server.py` — Una sola adición dentro de `create_app()`:
```python
from infrastructure.api.android.router import android_router
app.include_router(android_router, prefix="/api/v1")
```
No se toca nada más del archivo existente.

### `.gitignore` — Agregar sección al final:
```gitignore
# =============================================================================
# ANDROID APK BUILD
# =============================================================================
android_app/.buildozer/
android_app/bin/
android_app/.gradle/
*.keystore
*.jks
android_app/src/config_local.py
```

### `AGENTS.md` — Agregar sección al final:
Instrucciones para Claude Code CLI sobre el módulo `android_app/`: que no toque
el `main.py` de la raíz cuando trabaje en la APK, que los tests de la APK están
en `android_app/tests/` (no en `tests/` de la raíz), y que el `buildozer.spec`
es solo para compilación Android.

### `ci.yml` — Agregar exclusión de `android_app/` en el job de tests:
```yaml
- name: Run tests with coverage
  run: pytest -v --ignore=android_app/ --cov=. --cov-report=xml
```
Evita que pytest de la raíz intente correr los tests de Kivy (que necesitan el
entorno Android para ejecutarse correctamente).

---

## Separación Crítica: main.py Raíz vs main.py Android

Este punto es el más importante para no confundir a Claude Code CLI:

| Archivo | Qué es | Cuándo corre |
|---|---|---|
| `main.py` (raíz) | Entry point del **bot + FastAPI** | En el VPS con `python main.py` o systemd |
| `android_app/main.py` | Entry point de **Kivy/APK** | Solo en compilación Buildozer |

Son 100% independientes. El `android_app/main.py` **nunca se ejecuta en el VPS**.

---

## Flujo de Trabajo con Claude Code CLI en el VPS

**Trabajar en el backend Android API (rutas REST):**
```bash
# Desde la raíz del repo
claude "implementa el endpoint POST /api/v1/auth/request-otp
        en infrastructure/api/android/auth.py,
        usando Redis para guardar el OTP con TTL de 5 minutos"
```

**Trabajar en la UI de la APK:**
```bash
# Claude Code lee el contexto de android_app/
claude "implementa la pantalla OTP en android_app/src/screens/otp_screen.py
        siguiendo el diseño definido en docs/android/03_MODULO_AUTH.md"
```

**Compilar la APK:**
No se hace en el VPS. El flujo es:
```
1. git add android_app/ infrastructure/api/android/
2. git commit -m "feat: implementa módulo auth Android"
3. git tag v1.0.0
4. git push origin v1.0.0 --tags
5. GitHub Actions compila (ver build_apk.yml)
6. Descargar el .apk desde GitHub Releases
7. Instalar en el móvil: habilitar "Fuentes desconocidas" y abrir el .apk
```
