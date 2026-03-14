#!/bin/bash
# Script de actualización mensual para Outline VPN
# Guarda logs en /var/log/outline-update.log

LOG_FILE="/var/log/outline-update.log"
CONTAINER_NAME="shadowbox"
IMAGE="quay.io/outline/shadowbox:stable"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

log() {
    echo "[$DATE] $1" | tee -a "$LOG_FILE"
}

log "=== Iniciando verificación de actualización Outline ==="

# Verificar si hay nueva imagen
log "Verificando actualizaciones de imagen: $IMAGE"
docker pull "$IMAGE" >> "$LOG_FILE" 2>&1

# Obtener el ID de la imagen local actual
LOCAL_IMAGE_ID=$(docker images --format "{{.ID}}" "$IMAGE" | head -n1)
log "Imagen local ID: $LOCAL_IMAGE_ID"

# Verificar si el contenedor está corriendo con la última imagen
RUNNING_IMAGE_ID=$(docker inspect --format='{{.Image}}' "$CONTAINER_NAME" 2>/dev/null | cut -d: -f2 | cut -c1-12)
log "Contenedor corriendo con imagen ID: $RUNNING_IMAGE_ID"

# Si el contenedor no existe o está usando imagen antigua, actualizar
if [ "$LOCAL_IMAGE_ID" != "$RUNNING_IMAGE_ID" ]; then
    log "Nueva versión disponible. Actualizando contenedor..."

    # Detener y eliminar contenedor actual
    log "Deteniendo contenedor $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME" >> "$LOG_FILE" 2>&1
    docker rm "$CONTAINER_NAME" >> "$LOG_FILE" 2>&1

    # Eliminar imagen antigua para liberar espacio
    if [ -n "$RUNNING_IMAGE_ID" ]; then
        log "Eliminando imagen antigua..."
        docker rmi "$(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep "$RUNNING_IMAGE_ID" | awk '{print $1}')" >> "$LOG_FILE" 2>&1 || true
    fi

    # Crear nuevo contenedor con la misma configuración
    log "Creando nuevo contenedor..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart always \
        --network host \
        -v /opt/outline/persisted-state:/opt/outline/persisted-state \
        "$IMAGE" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "✅ Contenedor actualizado exitosamente"
        log "Nuevo contenedor ID: $(docker ps -q -f name=$CONTAINER_NAME)"
    else
        log "❌ Error al crear el nuevo contenedor"
        exit 1
    fi
else
    log "✅ Outline ya está en la última versión. No se requiere actualización."
fi

# Limpiar imágenes no usadas (opcional)
log "Limpiando imágenes antiguas no usadas..."
docker image prune -f >> "$LOG_FILE" 2>&1

log "=== Proceso completado ==="
echo "" >> "$LOG_FILE"
