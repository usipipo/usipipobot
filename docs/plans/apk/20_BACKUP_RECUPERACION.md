# Plan de Backup y Recuperación de Desastres

> **Versión:** 1.0.0
> **Fecha:** Marzo 2026
> **Contexto:** Single VPS con todos los servicios
> **Objetivo:** RTO < 4 horas, RPO < 24 horas

---

## 🎯 Objetivos de Recuperación

### RTO (Recovery Time Objective)
**Tiempo máximo para recuperar el servicio:** 4 horas

| Escenario | RTO Objetivo |
|-----------|--------------|
| Caída de servicio individual | < 30 minutos |
| Corrupción de base de datos | < 2 horas |
| Fallo completo del VPS | < 4 horas |
| Desastre total (pérdida de VPS) | < 24 horas |

### RPO (Recovery Point Objective)
**Pérdida máxima de datos aceptable:** 24 horas

| Tipo de Dato | RPO Objetivo | Frecuencia de Backup |
|--------------|--------------|---------------------|
| Base de datos PostgreSQL | 24 horas | Diario |
| Archivos de configuración | 7 días | Semanal |
| Logs del sistema | 30 días | Mensual (archive) |
| Secrets/Keys | 0 (crítico) | Backup inmediato al cambiar |

---

## 📦 Estrategia de Backup 3-2-1

### Regla 3-2-1
- **3** copias de los datos (producción + 2 backups)
- **2** medios diferentes (disco local + cloud)
- **1** copia off-site (otro servidor/cloud)

### Implementación para uSipipo

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCCIÓN (VPS)                         │
│  /var/lib/postgresql/15/main (datos en vivo)                │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────────┐ ┌──────────┐ ┌──────────────────┐
│ BACKUP LOCAL    │ │ BACKUP   │ │ BACKUP OFF-SITE  │
│ (mismo VPS)     │ │ REMOTO   │ │ (Cloud)          │
│                 │ │ (SFTP)   │ │                  │
│ /backups/       │ │          │ │ Backblaze B2     │
│ - PostgreSQL    │ │ VPS      │ │ o AWS S3         │
│ - Configs       │ │ secundario│ │                  │
│ - Secrets       │ │          │ │                  │
└─────────────────┘ └──────────┘ └──────────────────┘
```

---

## 🗄️ Fase 1: Backup de PostgreSQL

### Script de Backup Diario

**Archivo: `/opt/usipipobot/scripts/backup_postgresql.sh`**

```bash
#!/bin/bash
# Backup completo de PostgreSQL con retención y verificación

set -e

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

BACKUP_DIR="/backups/postgresql"
RETENTION_DAYS=7                    # Retener backups diarios por 7 días
RETENTION_WEEKS=4                   # Retener backups semanales por 4 semanas
RETENTION_MONTHS=6                  # Retener backups mensuales por 6 meses

DB_NAME="usipipodb"
DB_USER="usipipo_app"
PG_HOST="localhost"

# Notificaciones
ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"

# Logging
LOG_FILE="/var/log/usipipo/backup_postgresql.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/usipipo_${DB_NAME}_${TIMESTAMP}.sql.gz"

# =============================================================================
# FUNCIONES
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"💾 BACKUP PostgreSQL:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
    log "ALERT: $message"
}

cleanup_old_backups() {
    log "Limpiando backups antiguos..."
    
    # Eliminar backups diarios más antiguos que RETENTION_DAYS
    find "$BACKUP_DIR" -name "usipipo_${DB_NAME}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    # Mantener al menos 1 backup semanal (el más reciente de cada semana)
    # Mantener al menos 1 backup mensual (el más reciente de cada mes)
    # Esto requiere lógica más compleja, simplificado por ahora
    
    log "Limpieza completada"
}

verify_backup() {
    local backup_file="$1"
    
    log "Verificando backup: $backup_file"
    
    # Verificar que el archivo existe y no está vacío
    if [ ! -f "$backup_file" ]; then
        alert "❌ Backup NO existe: $backup_file"
        return 1
    fi
    
    if [ ! -s "$backup_file" ]; then
        alert "❌ Backup está VACÍO: $backup_file"
        return 1
    fi
    
    # Verificar integridad del gzip
    if ! gzip -t "$backup_file" 2>/dev/null; then
        alert "❌ Backup CORRUPTO (gzip test falló): $backup_file"
        return 1
    fi
    
    # Verificar que contiene SQL válido (buscar CREATE TABLE o INSERT)
    if ! zcat "$backup_file" | head -100 | grep -qE "(CREATE TABLE|INSERT INTO|pg_dump)"; then
        alert "❌ Backup parece inválido (no contiene SQL): $backup_file"
        return 1
    fi
    
    # Obtener tamaño
    local size=$(du -h "$backup_file" | cut -f1)
    log "✅ Backup verificado: $size"
    
    return 0
}

# =============================================================================
# BACKUP PRINCIPAL
# =============================================================================

log "=== Iniciando backup de PostgreSQL ==="
log "Base de datos: $DB_NAME"
log "Archivo de backup: $BACKUP_FILE"

# Crear directorio de backups si no existe
mkdir -p "$BACKUP_DIR"

# Obtener tamaño actual de la DB
DB_SIZE=$(psql -h "$PG_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
log "Tamaño actual de la DB: $DB_SIZE"

# Ejecutar pg_dump
log "Ejecutando pg_dump..."
if PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "$PG_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    2>> "$LOG_FILE" | gzip -9 > "$BACKUP_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Backup completado: $BACKUP_SIZE"
    
    # Verificar backup
    if verify_backup "$BACKUP_FILE"; then
        # Calcular checksum
        CHECKSUM=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
        echo "$CHECKSUM  $BACKUP_FILE" >> "${BACKUP_DIR}/checksums.txt"
        
        log "Checksum MD5: $CHECKSUM"
        
        # Notificar éxito
        alert "✅ Backup completado exitosamente\\n\\n📊 Base de datos: ${DB_NAME}\\n📦 Tamaño: ${BACKUP_SIZE}\\n📁 Archivo: $(basename $BACKUP_FILE)\\n🔐 Checksum: \`${CHECKSUM:0:16}...\`"
    else
        alert "❌ Backup falló la verificación\\n\\n📁 Archivo: $(basename $BACKUP_FILE)"
        exit 1
    fi
    
else
    alert "❌❌ Backup FALLÓ\\n\\n📊 Base de datos: ${DB_NAME}\\n\\n⚠️ Revisar logs para más detalles."
    exit 1
fi

# =============================================================================
# LIMPIEZA
# =============================================================================

cleanup_old_backups

# =============================================================================
# BACKUP REMOTO (opcional, si hay SFTP configurado)
# =============================================================================

if [ -n "${REMOTE_BACKUP_HOST:-}" ] && [ -n "${REMOTE_BACKUP_USER:-}" ]; then
    log "Copiando backup a servidor remoto..."
    
    if scp "$BACKUP_FILE" "${REMOTE_BACKUP_USER}@${REMOTE_BACKUP_HOST}:/backups/postgresql/" 2>> "$LOG_FILE"; then
        log "✅ Backup remoto completado"
    else
        alert "⚠️ Backup remoto FALLÓ\\n\\nEl backup local está bien, pero no se pudo copiar al servidor remoto."
    fi
fi

log "=== Backup completado ==="
```

**Permisos y seguridad:**
```bash
sudo chmod 700 /opt/usipipobot/scripts/backup_postgresql.sh
sudo chown root:usipipo /opt/usipipobot/scripts/backup_postgresql.sh

# Crear archivo de credenciales seguro
sudo mkdir -p /root/.postgresql
sudo cat > /root/.postgresql/backup_credentials <<EOF
DB_PASSWORD=tu_contraseña_segura
REMOTE_BACKUP_HOST=backup.usipipo.com
REMOTE_BACKUP_USER=backup_user
EOF
sudo chmod 600 /root/.postgresql/backup_credentials
```

**Cron (diario a las 3 AM):**
```bash
sudo crontab -e

# Agregar:
0 3 * * * /opt/usipipobot/scripts/backup_postgresql.sh
```

---

### Backup de Configuración de PostgreSQL

**Archivo: `/opt/usipipobot/scripts/backup_pg_config.sh`**

```bash
#!/bin/bash
# Backup de configuración de PostgreSQL

set -e

BACKUP_DIR="/backups/postgresql/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Archivos de configuración
CONFIG_FILES=(
    "/etc/postgresql/15/main/postgresql.conf"
    "/etc/postgresql/15/main/pg_hba.conf"
    "/etc/postgresql/15/main/pg_ident.conf"
)

log "Backup de configuración de PostgreSQL..."

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -f "$config_file" ]; then
        cp "$config_file" "${BACKUP_DIR}/$(basename $config_file).${TIMESTAMP}"
        log "✅ Copiado: $config_file"
    fi
done

# Limpieza (mantener últimos 10 backups)
ls -t "${BACKUP_DIR}"/*.conf.* | tail -n +11 | xargs -r rm

log "=== Backup de configuración completado ==="
```

---

## 📁 Fase 2: Backup de Archivos Críticos

### Script de Backup de Configuraciones

**Archivo: `/opt/usipipobot/scripts/backup_configs.sh`**

```bash
#!/bin/bash
# Backup de todas las configuraciones críticas del sistema

set -e

BACKUP_DIR="/backups/configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/usipipo_configs_${TIMESTAMP}.tar.gz"

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
LOG_FILE="/var/log/usipipo/backup_configs.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"💾 BACKUP Configs:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
}

log "=== Iniciando backup de configuraciones ==="

mkdir -p "$BACKUP_DIR"

# Lista de archivos y directorios críticos
CRITICAL_FILES=(
    # Application configs
    "/opt/usipipobot/.env"
    "/opt/usipipobot/config.py"
    
    # System configs
    "/etc/caddy/Caddyfile"
    "/etc/postgresql/15/main/postgresql.conf"
    "/etc/postgresql/15/main/pg_hba.conf"
    "/etc/redis/redis.conf"
    
    # Systemd services
    "/etc/systemd/system/usipipo-backend.service"
    "/etc/systemd/system/usipipo-bot.service"
    "/etc/systemd/system/usipipo-jobs.service"
    
    # VPN configs
    "/etc/wireguard/wg0.conf"
    
    # Scripts personalizados
    "/opt/usipipobot/scripts"
    
    # SSH config (solo configuración, no keys)
    "/etc/ssh/sshd_config"
)

# Crear lista de archivos existentes
EXISTING_FILES=()
for file in "${CRITICAL_FILES[@]}"; do
    if [ -e "$file" ]; then
        EXISTING_FILES+=("$file")
        log "Incluyendo: $file"
    else
        log "⚠️ No existe: $file"
    fi
done

# Crear tarball
log "Creando backup..."
if tar -czf "$BACKUP_FILE" "${EXISTING_FILES[@]}" 2>> "$LOG_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Backup completado: $BACKUP_SIZE"
    
    # Calcular checksum
    CHECKSUM=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
    echo "$CHECKSUM  $BACKUP_FILE" >> "${BACKUP_DIR}/checksums.txt"
    
    # Notificar
    alert "✅ Backup de configuraciones completado\\n\\n📦 Tamaño: ${BACKUP_SIZE}\\n📁 Archivo: $(basename $BACKUP_FILE)"
    
else
    alert "❌ Backup de configuraciones FALLÓ"
    exit 1
fi

# Limpieza (mantener últimos 30 backups)
ls -t "${BACKUP_DIR}"/usipipo_configs_*.tar.gz | tail -n +31 | xargs -r rm

log "=== Backup completado ==="
```

**Cron (semanal, domingos a las 4 AM):**
```bash
0 4 * * 0 /opt/usipipobot/scripts/backup_configs.sh
```

---

## 🔐 Fase 3: Backup de Secrets

### Script de Backup Seguro de Secrets

**Archivo: `/opt/usipipobot/scripts/backup_secrets.sh`**

```bash
#!/bin/bash
# Backup ENCRYPTADO de secrets críticos

set -e

BACKUP_DIR="/backups/secrets"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/usipipo_secrets_${TIMESTAMP}.gpg"

# Clave GPG para encriptación (debe estar configurada previamente)
GPG_RECIPIENT="admin@usipipo.com"

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"
LOG_FILE="/var/log/usipipo/backup_secrets.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"🔐 BACKUP Secrets:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
}

log "=== Iniciando backup SEGURO de secrets ==="

mkdir -p "$BACKUP_DIR"

# Archivos de secrets críticos
SECRET_FILES=(
    "/opt/usipipobot/.env"
    "/root/.postgresql/backup_credentials"
    "/root/.ssh/authorized_keys"
    "/etc/ssh/sshd_config"
)

# Crear tarball temporal
TEMP_TAR=$(mktemp)
trap "rm -f $TEMP_TAR" EXIT

log "Creando tarball temporal..."
tar -cf "$TEMP_TAR" "${SECRET_FILES[@]}" 2>/dev/null || true

# Encriptar con GPG
log "Encriptando backup..."
if gpg --yes --batch --recipient "$GPG_RECIPIENT" \
    --encrypt --output "$BACKUP_FILE" "$TEMP_TAR" 2>> "$LOG_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "✅ Backup encriptado completado: $BACKUP_SIZE"
    
    # Calcular checksum
    CHECKSUM=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
    echo "$CHECKSUM  $BACKUP_FILE" >> "${BACKUP_DIR}/checksums.txt"
    
    # Notificar
    alert "🔐 Backup de secrets encriptado completado\\n\\n📦 Tamaño: ${BACKUP_SIZE}\\n🔒 Encriptado para: ${GPG_RECIPIENT}"
    
    # Limpieza (mantener últimos 5 backups ENCRYPTADOS)
    ls -t "${BACKUP_DIR}"/usipipo_secrets_*.gpg | tail -n +6 | xargs -r rm
    
else
    alert "❌ Backup de secrets FALLÓ (encriptación)"
    exit 1
fi

log "=== Backup seguro completado ==="
```

**Configurar GPG primero:**
```bash
# Generar par de claves GPG (si no existe)
gpg --gen-key

# Exportar clave pública (para importar en otro servidor)
gpg --export --armor admin@usipipo.com > backup_public_key.asc

# Importar clave pública en otro servidor (para restaurar)
gpg --import backup_public_key.asc
```

**Cron (mensual, día 1 a las 5 AM):**
```bash
0 5 1 * * /opt/usipipobot/scripts/backup_secrets.sh
```

---

## ☁️ Fase 4: Backup Off-Site (Cloud)

### Script de Sync a Backblaze B2

**Archivo: `/opt/usipipobot/scripts/sync_backup_cloud.sh`**

```bash
#!/bin/bash
# Sincronizar backups locales a Backblaze B2 (S3-compatible)

set -e

# Configuración de Backblaze B2
B2_BUCKET="usipipo-backups"
B2_ACCOUNT_ID="${B2_ACCOUNT_ID:-}"
B2_APPLICATION_KEY="${B2_APPLICATION_KEY:-}"

BACKUP_LOCAL_DIR="/backups"
LOG_FILE="/var/log/usipipo/sync_cloud.log"

ALERT_WEBHOOK="https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage"
CHAT_ID="${ADMIN_ID}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

alert() {
    local message="$1"
    curl -s -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{
            \"chat_id\": ${CHAT_ID},
            \"text\": \"☁️ SYNC Cloud:\\n${message}\",
            \"parse_mode\": \"HTML\"
        }"
}

log "=== Iniciando sync a Backblaze B2 ==="

# Verificar credenciales
if [ -z "$B2_ACCOUNT_ID" ] || [ -z "$B2_APPLICATION_KEY" ]; then
    alert "❌ Credenciales de B2 no configuradas\\n\\nB2_ACCOUNT_ID y B2_APPLICATION_KEY deben estar en el .env"
    exit 1
fi

# Instalar b2cli si no existe
if ! command -v b2 &> /dev/null; then
    log "Instalando b2cli..."
    pip3 install b2cli
fi

# Autenticar con B2
log "Autenticando con Backblaze B2..."
if ! b2 authorize-account "$B2_ACCOUNT_ID" "$B2_APPLICATION_KEY" 2>> "$LOG_FILE"; then
    alert "❌ Falló autenticación con Backblaze B2"
    exit 1
fi

# Crear bucket si no existe
b2 create-bucket "$B2_BUCKET" allPrivate 2>/dev/null || log "Bucket ya existe"

# Sincronizar backups
log "Sincronizando backups..."
if b2 sync "$BACKUP_LOCAL_DIR" "b2://${B2_BUCKET}/backups" 2>> "$LOG_FILE"; then
    
    # Listar archivos en B2
    FILE_COUNT=$(b2 ls "b2://${B2_BUCKET}/backups" | wc -l)
    
    log "✅ Sync completado: $FILE_COUNT archivos en B2"
    alert "☁️ Sync a Backblaze B2 completado\\n\\n📦 Archivos en cloud: ${FILE_COUNT}"
    
else
    alert "❌ Sync a Backblaze B2 FALLÓ"
    exit 1
fi

log "=== Sync completado ==="
```

**Alternativa con AWS S3:**

**Archivo: `/opt/usipipobot/scripts/sync_backup_s3.sh`**

```bash
#!/bin/bash
# Sincronizar backups a AWS S3

set -e

AWS_BUCKET="usipipo-backups"
AWS_REGION="us-east-1"

BACKUP_LOCAL_DIR="/backups"
LOG_FILE="/var/log/usipipo/sync_s3.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Iniciando sync a AWS S3 ==="

# Sincronizar con S3
if aws s3 sync "$BACKUP_LOCAL_DIR" "s3://${AWS_BUCKET}/backups" \
    --region "$AWS_REGION" \
    --storage-class STANDARD_IA \
    >> "$LOG_FILE" 2>&1; then
    
    log "✅ Sync a S3 completado"
else
    log "❌ Sync a S3 FALLÓ"
    exit 1
fi

log "=== Sync completado ==="
```

**Cron (diario a las 6 AM, después del backup de PostgreSQL):**
```bash
0 6 * * * /opt/usipipobot/scripts/sync_backup_cloud.sh
```

---

## 🔄 Fase 5: Recuperación de Desastres

### Plan de Recuperación Documentado

**Archivo: `/opt/usipipobot/docs/DISASTER_RECOVERY.md`**

```markdown
# Plan de Recuperación de Desastres

## Escenario 1: Caída de Servicio Individual

### PostgreSQL caído
```bash
# 1. Verificar estado
sudo systemctl status postgresql

# 2. Intentar restart
sudo systemctl restart postgresql

# 3. Verificar logs
sudo tail -100 /var/log/postgresql/postgresql-15-main.log

# 4. Si no funciona, restaurar desde backup
sudo systemctl stop postgresql
sudo rm -rf /var/lib/postgresql/15/main
sudo -u postgres /usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/15/main
sudo systemctl start postgresql

# 5. Restaurar backup más reciente
gunzip -c /backups/postgresql/usipipo_*.sql.gz | sudo -u postgres psql usipipodb
```

### Backend caído
```bash
# 1. Verificar proceso
ps aux | grep uvicorn

# 2. Verificar logs
sudo journalctl -u usipipo-backend -n 100

# 3. Intentar restart
sudo systemctl restart usipipo-backend

# 4. Verificar health
curl http://localhost:8000/health
```

## Escenario 2: Corrupción de Base de Datos

### Síntomas
- Errores de SQL en logs
- Queries fallando aleatoriamente
- Datos inconsistentes

### Recuperación
```bash
# 1. Detener aplicación
sudo systemctl stop usipipo-backend
sudo systemctl stop usipipo-bot

# 2. Identificar corrupción
sudo -u postgres psql usipipodb -c "SELECT pg_check_tables();"

# 3. Si hay corrupción, restaurar backup
sudo systemctl stop postgresql

# Backup de datos corruptos (por si acaso)
sudo mv /var/lib/postgresql/15/main /var/lib/postgresql/15/main.corrupt

# Restaurar
sudo -u postgres /usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/15/main
sudo systemctl start postgresql

# Crear DB
sudo -u postgres createdb usipipodb

# Restaurar datos
gunzip -c /backups/postgresql/usipipo_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql usipipodb

# 4. Reiniciar aplicación
sudo systemctl start usipipo-backend
sudo systemctl start usipipo-bot

# 5. Verificar
curl http://localhost:8000/health
```

## Escenario 3: Fallo Completo del VPS

### Recuperación en Nuevo VPS

```bash
# 1. Provisionar nuevo VPS (mismo SO preferiblemente)

# 2. Instalar dependencias
sudo apt update
sudo apt install -y postgresql postgresql-contrib redis-server \
    python3 python3-pip python3-venv nginx curl git

# 3. Instalar Caddy
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# 4. Clonar repositorio
git clone https://github.com/usipipo/usipipobot.git /opt/usipipobot
cd /opt/usipipobot

# 5. Restaurar secrets desde backup seguro
# (Descargar de Backblaze B2 o desde backup encriptado)
b2 download-file b2://usipipo-backups/secrets/usipipo_secrets_*.gpg /tmp/secrets.gpg
gpg --decrypt /tmp/secrets.gpg > /opt/usipipobot/.env

# 6. Configurar permisos
sudo chown -R usipipo:usipipo /opt/usipipobot
sudo chmod 640 /opt/usipipobot/.env

# 7. Instalar dependencias de Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 8. Restaurar PostgreSQL
sudo systemctl start postgresql
sudo -u postgres createdb usipipodb

# Descargar backup más reciente
b2 download-file b2://usipipo-backups/backups/postgresql/usipipo_*.sql.gz /tmp/backup.sql.gz
gunzip -c /tmp/backup.sql.gz | sudo -u postgres psql usipipodb

# 9. Configurar servicios
sudo cp /opt/usipipobot/systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable usipipo-backend usipipo-bot caddy

# 10. Iniciar servicios
sudo systemctl start usipipo-backend
sudo systemctl start usipipo-bot
sudo systemctl start caddy

# 11. Verificar
curl http://localhost:8000/health

# 12. Actualizar DNS si cambió la IP del VPS
# (Editar en DuckDNS o proveedor de dominio)
```

## Escenario 4: Pérdida Total de Datos (Desastre Natural)

### Recuperación desde Backup Off-Site

```bash
# 1. Provisionar nuevo VPS desde cero

# 2. Seguir pasos del Escenario 3

# 3. Descargar backups desde Backblaze B2
b2 authorize-account $B2_ACCOUNT_ID $B2_APPLICATION_KEY
b2 sync b2://usipipo-backups/backups /backups

# 4. Restaurar backup más reciente de PostgreSQL
# (ver pasos arriba)

# 5. Restaurar configuraciones
tar -xzf /backups/configs/usipipo_configs_*.tar.gz -C /

# 6. Restaurar secrets
gpg --decrypt /backups/secrets/usipipo_secrets_*.gpg | tar -xz -C /

# 7. Verificar integridad de datos restaurados
sudo -u postgres psql usipipodb -c "SELECT COUNT(*) FROM users;"
# Comparar con expected count

# 8. Notificar a usuarios si hay pérdida de datos significativa
```

## Contactos de Emergencia

| Rol | Nombre | Contacto |
|-----|--------|----------|
| Admin Principal | [Nombre] | @telegram, email |
| Backup Admin | [Nombre] | @telegram, email |
| Soporte VPS | [Provider] | Ticket, email |

## Checklist Post-Recuperación

- [ ] Verificar que todos los servicios están activos
- [ ] Verificar health del backend
- [ ] Probar creación de clave VPN
- [ ] Probar pago con Stars
- [ ] Probar pago con USDT
- [ ] Verificar datos de usuarios (count)
- [ ] Notificar a usuarios si aplica
- [ ] Documentar incidente y lecciones aprendidas
```

---

## 🧪 Fase 6: Testing de Recuperación

### Script de Test de Restauración

**Archivo: `/opt/usipipobot/scripts/test_restore.sh`**

```bash
#!/bin/bash
# Test de restauración de backup (en ambiente aislado)

set -e

BACKUP_FILE="$1"
TEST_DB="usipipodb_test_restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Uso: test_restore.sh <backup_file.sql.gz>"
    exit 1
fi

echo "=== Test de Restauración de Backup ==="
echo "Backup: $BACKUP_FILE"

# Verificar que el backup existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup no existe: $BACKUP_FILE"
    exit 1
fi

# Verificar integridad
echo "Verificando integridad..."
if ! gzip -t "$BACKUP_FILE"; then
    echo "❌ Backup corrupto (gzip test falló)"
    exit 1
fi
echo "✅ Integridad OK"

# Crear DB de test
echo "Creando base de datos de test..."
sudo -u postgres dropdb --if-exists "$TEST_DB"
sudo -u postgres createdb "$TEST_DB"

# Restaurar backup
echo "Restaurando backup..."
START_TIME=$(date +%s)
gunzip -c "$BACKUP_FILE" | sudo -u postgres psql "$TEST_DB" > /dev/null
END_TIME=$(date +%s)
RESTORE_TIME=$((END_TIME - START_TIME))

echo "✅ Restauración completada en ${RESTORE_TIME}s"

# Verificar datos
echo "Verificando datos..."
USER_COUNT=$(sudo -u postgres psql "$TEST_DB" -t -c "SELECT COUNT(*) FROM users;")
KEY_COUNT=$(sudo -u postgres psql "$TEST_DB" -t -c "SELECT COUNT(*) FROM vpn_keys;")
PACKAGE_COUNT=$(sudo -u postgres psql "$TEST_DB" -t -c "SELECT COUNT(*) FROM data_packages;")

echo ""
echo "=== Resultados ==="
echo "Usuarios: $USER_COUNT"
echo "Claves VPN: $KEY_COUNT"
echo "Paquetes: $PACKAGE_COUNT"
echo "Tiempo de restauración: ${RESTORE_TIME}s"

# Limpieza
echo ""
echo "Limpiando..."
sudo -u postgres dropdb "$TEST_DB"
echo "✅ Test completado exitosamente"
```

**Ejecutar test mensualmente:**
```bash
# Buscar el backup más reciente
LATEST_BACKUP=$(ls -t /backups/postgresql/usipipo_*.sql.gz | head -1)

# Ejecutar test
/opt/usipipobot/scripts/test_restore.sh "$LATEST_BACKUP"
```

---

## ✅ Checklist de Implementación

### Semana 1: Backup de PostgreSQL
- [ ] Implementar script de backup diario
- [ ] Configurar cron a las 3 AM
- [ ] Configurar retención (7 días)
- [ ] Probar restauración manual
- [ ] Configurar alertas de backup fallido

### Semana 2: Backup de Configuraciones
- [ ] Implementar script de backup de configs
- [ ] Configurar cron semanal
- [ ] Incluir todos los archivos críticos
- [ ] Verificar backups creados

### Semana 3: Backup Off-Site
- [ ] Configurar cuenta en Backblaze B2 o AWS S3
- [ ] Implementar script de sync
- [ ] Configurar cron diario
- [ ] Verificar sync completado

### Semana 4: Documentación y Testing
- [ ] Documentar plan de recuperación
- [ ] Crear script de test de restauración
- [ ] Ejecutar test de restauración completo
- [ ] Medir tiempo de recuperación (RTO)

---

## 🎯 Métricas de Éxito

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Backup diario exitoso | >99% | Logs de backup |
| Tiempo de backup PostgreSQL | <30 min | Timestamp en logs |
| Tamaño de backup comprimido | <500MB | du -h backup file |
| Test de restauración | Mensual | Script test_restore.sh |
| RTO (recuperación total) | <4 horas | Timing de drill |
| RPO (pérdida de datos) | <24 horas | Timestamp último backup |

---

## 📊 Resumen de Backup Schedule

| Tipo | Frecuencia | Horario | Retención | Destino |
|------|------------|---------|-----------|---------|
| PostgreSQL | Diario | 3:00 AM | 7 días | Local + Cloud |
| Configuraciones | Semanal | Domingo 4:00 AM | 30 backups | Local + Cloud |
| Secrets | Mensual | Día 1, 5:00 AM | 5 backups | Local + Cloud |
| Sync a Cloud | Diario | 6:00 AM | Indefinido | Backblaze/AWS |
| Test Restore | Mensual | Día 15 | N/A | Local (test DB) |

---

*Documento versión 1.0 - Fecha: Marzo 2026*
