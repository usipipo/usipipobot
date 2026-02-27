#!/bin/bash
# =============================================================================
# Script de verificación para limpieza automática de RAM
# =============================================================================

set -e

echo "=========================================="
echo "  Verificación de Limpieza de RAM"
echo "=========================================="
echo ""

# Verificar si es root o tiene sudo
check_permissions() {
    echo "🔍 Verificando permisos..."

    if [ "$EUID" -eq 0 ]; then
        echo "   ✅ Ejecutando como root"
        return 0
    fi

    if sudo -n true 2>/dev/null; then
        echo "   ✅ Tiene acceso sudo sin contraseña"
        return 0
    fi

    echo "   ⚠️  ADVERTENCIA: No es root ni tiene sudo sin contraseña"
    echo "   La limpieza de RAM requiere permisos para escribir en /proc/sys/vm/"
    echo ""
    return 1
}

# Verificar acceso a /proc/sys/vm/drop_caches
check_drop_caches() {
    echo "🔍 Verificando acceso a drop_caches..."

    if [ -w "/proc/sys/vm/drop_caches" ]; then
        echo "   ✅ Puede escribir en /proc/sys/vm/drop_caches"
        return 0
    else
        echo "   ❌ No puede escribir en /proc/sys/vm/drop_caches"
        echo "   Solución: Agregar al usuario a sudoers o ejecutar como root"
        echo ""
        return 1
    fi
}

# Mostrar estado actual de RAM
show_memory_status() {
    echo "🔍 Estado actual de la RAM:"

    if [ -f /proc/meminfo ]; then
        total=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        available=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        used=$((total - available))

        total_gb=$(echo "scale=2; $total / 1024 / 1024" | bc 2>/dev/null || echo "0")
        used_gb=$(echo "scale=2; $used / 1024 / 1024" | bc 2>/dev/null || echo "0")
        avail_gb=$(echo "scale=2; $available / 1024 / 1024" | bc 2>/dev/null || echo "0")

        used_percent=$(echo "scale=1; $used * 100 / $total" | bc 2>/dev/null || echo "0")

        echo "   💾 Total: ${total_gb} GB"
        echo "   📊 Usada: ${used_gb} GB (${used_percent}%)"
        echo "   ✅ Disponible: ${avail_gb} GB"
        echo ""
    else
        echo "   ❌ No se pudo leer /proc/meminfo"
    fi
}

# Mostrar configuración actual
check_config() {
    echo "🔍 Configuración en .env:"

    if [ -f .env ]; then
        enabled=$(grep MEMORY_CLEANUP_ENABLED .env 2>/dev/null | cut -d= -f2 || echo "true")
        threshold=$(grep MEMORY_CLEANUP_THRESHOLD_PERCENT .env 2>/dev/null | cut -d= -f2 || echo "80")
        critical=$(grep MEMORY_CLEANUP_CRITICAL_PERCENT .env 2>/dev/null | cut -d= -f2 || echo "90")
        interval=$(grep MEMORY_CLEANUP_INTERVAL_MINUTES .env 2>/dev/null | cut -d= -f2 || echo "10")
        notify=$(grep MEMORY_NOTIFY_ADMIN .env 2>/dev/null | cut -d= -f2 || echo "true")

        echo "   ENABLED: ${enabled}"
        echo "   THRESHOLD: ${threshold}%"
        echo "   CRITICAL: ${critical}%"
        echo "   INTERVAL: ${interval} minutos"
        echo "   NOTIFY: ${notify}"
        echo ""
    else
        echo "   ⚠️  No se encontró archivo .env (usando valores por defecto)"
        echo ""
    fi
}

# Probar limpieza manual
test_cleanup() {
    echo "🔍 Prueba de limpieza de caché..."

    if [ -w "/proc/sys/vm/drop_caches" ]; then
        sync
        echo 1 > /proc/sys/vm/drop_caches 2>/dev/null && echo "   ✅ Limpieza nivel 1 exitosa" || echo "   ❌ Falló limpieza nivel 1"
    else
        echo "   ⚠️  Sin permisos para probar limpieza"
    fi
    echo ""
}

# Mostrar ayuda para sudoers
show_sudoers_help() {
    echo "🔧 Para permitir limpieza sin contraseña, agregar a /etc/sudoers:"
    echo ""
    echo "   $(whoami) ALL=(ALL) NOPASSWD: /bin/sync"
    echo "   $(whoami) ALL=(ALL) NOPASSWD: /bin/echo * > /proc/sys/vm/drop_caches"
    echo ""
    echo "   O crear un archivo en /etc/sudoers.d/usipipo-ram:"
    echo ""
    cat << 'EOF'
Cmnd_Alias RAM_CLEANUP = /bin/sync, /bin/echo *, /bin/sh -c echo* > /proc/sys/vm/drop_caches
$(whoami) ALL=(ALL) NOPASSWD: RAM_CLEANUP
EOF
    echo ""
}

# Main
main() {
    check_permissions
    check_drop_caches
    show_memory_status
    check_config

    if [ "$1" == "--test" ]; then
        test_cleanup
    fi

    if [ "$1" == "--help-sudoers" ]; then
        show_sudoers_help
    fi

    echo "=========================================="
    echo "  Para ayuda de sudoers: $0 --help-sudoers"
    echo "  Para probar limpieza: $0 --test"
    echo "=========================================="
}

main "$@"
