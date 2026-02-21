# Design: Script de Setup Modular

**Fecha:** 2026-02-21  
**Estado:** Aprobado  
**Tipo:** Feature

## Resumen

Crear un sistema de instalación modular para uSipipo VPN Bot que permita configurar completamente el sistema (VPN, PostgreSQL, Python, Systemd, Bot) mediante un menú interactivo.

## Requisitos

1. Renombrar `scripts/install.sh` → mantener como módulo VPN
2. Crear `scripts/setup.sh` como menú principal orquestador
3. Crear módulos para cada componente
4. Soportar instalación interactiva con menú
5. Generar credenciales PostgreSQL automáticamente
6. Crear e iniciar servicio systemd automáticamente

## Arquitectura

```
scripts/
├── setup.sh              # Menú principal orquestador
├── install.sh            # VPN (archivo actual, renombrado de scripts/)
├── modules/
│   ├── common.sh         # Funciones compartidas
│   ├── database.sh       # PostgreSQL
│   ├── python.sh         # venv + requirements
│   ├── systemd.sh        # Servicio systemd
│   └── bot.sh            # Validación y lanzamiento
```

## Menú Principal

```
═══════════════════════════════════════════════════════
              🛡️ uSipipo Setup Manager 🛡️
═══════════════════════════════════════════════════════

  1) 🐳 Instalar Docker
  2) ⚙️  Instalar Outline Server
  3) ⚙️  Instalar WireGuard Server
  4) 🗄️  Instalar/Configurar PostgreSQL
  5) 🐍 Instalar dependencias Python (venv)
  6) 🔄 Ejecutar migraciones Alembic
  7) 🚀 Crear servicio systemd
  8) ▶️  Iniciar bot (main.py)
  9) 🔁 Setup completo (1-7 automático)
  10) 📊 Estado del sistema
  0) Salir
```

## Módulos

### common.sh

- Colores y constantes
- Funciones de logging (log, log_ok, log_warn, log_err)
- Helper run_sudo
- Helper confirm
- Detección de IP pública
- Gestión de .env

### database.sh

| Función | Descripción |
|---------|-------------|
| install_postgresql() | Instalar postgresql, postgresql-contrib |
| create_database_and_user() | Crear DB usipipo, usuario con password aleatorio |
| configure_postgresql() | Ajustar pg_hba.conf para conexiones locales |
| save_db_credentials() | Guardar DATABASE_URL en .env |

### python.sh

| Función | Descripción |
|---------|-------------|
| verify_python_version() | Chequear Python >= 3.11 |
| create_venv() | Crear venv en PROJECT_DIR |
| install_requirements() | pip install -r requirements.txt |

### systemd.sh

| Función | Descripción |
|---------|-------------|
| create_service_file() | Crear /etc/systemd/system/usipipo.service |
| enable_service() | systemctl enable usipipo |
| start_service() | systemctl start usipipo |
| show_service_status() | systemctl status usipipo |

### bot.sh

| Función | Descripción |
|---------|-------------|
| validate_env() | Verificar TELEGRAM_TOKEN y otras variables |
| run_migrations() | alembic upgrade head |
| start_bot_interactive() | Ejecutar main.py en foreground |

## Validaciones

1. Permisos root/sudo requeridos
2. Python >= 3.11
3. PostgreSQL no instalado previamente (o actualizar)
4. TELEGRAM_TOKEN presente en .env
5. Puertos disponibles (5432, VPN ports)

## Flujos de Error

- Si PostgreSQL falla: mostrar error y opción de retry
- Si venv falla: verificar Python y reintentar
- Si migraciones fallan: verificar DATABASE_URL y conexión

## Dependencias

- curl, wget, sed, grep, awk (ya verificados)
- python3, python3-venv, python3-pip
- postgresql, postgresql-contrib
- systemd

## Tests

- Verificar sintaxis: `bash -n scripts/setup.sh`
- Verificar imports de módulos
- Test de instalación en VM limpia (manual)
