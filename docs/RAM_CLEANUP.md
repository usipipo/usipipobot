# Limpieza Automática de RAM

Este módulo monitorea el uso de memoria RAM del servidor y limpia automáticamente cachés y buffers cuando se superan los umbrales configurados.

---

## Quick Start (Pasos Rápidos)

### Paso 1: Verificar que el código está actualizado
```bash
cd /home/mowgli/usipipobot
git pull origin main  # o la rama que uses
```

### Paso 2: Verificar configuración en .env
Las variables ya deberían estar en tu `.env`. Si no, añádelas:
```bash
# =============================================================================
# AUTO MEMORY CLEANUP (RAM)
# =============================================================================
MEMORY_CLEANUP_ENABLED=true
MEMORY_CLEANUP_THRESHOLD_PERCENT=80
MEMORY_CLEANUP_CRITICAL_PERCENT=90
MEMORY_CLEANUP_INTERVAL_MINUTES=10
MEMORY_NOTIFY_ADMIN=true
```

### Paso 3: Configurar permisos (IMPORTANTE)
El job necesita permisos para limpiar la caché. Elige una opción:

#### Opción A: Usar sudoers (RECOMENDADA)
```bash
# Crear archivo sudoers para el bot
sudo visudo -f /etc/sudoers.d/usipipo-ram
```

Pega estas líneas (reemplaza `mowgli` con tu usuario):
```
mowgli ALL=(ALL) NOPASSWD: /bin/sync
mowgli ALL=(ALL) NOPASSWD: /bin/sh -c echo* > /proc/sys/vm/drop_caches
```

Guardar y salir (Ctrl+X, Y, Enter).

#### Opción B: Ejecutar como root (NO recomendada)
```bash
sudo systemctl edit usipipo
```
Añadir:
```ini
[Service]
User=root
```

### Paso 4: Probar la configuración
```bash
# Ver estado actual de RAM
./scripts/check_ram_cleanup.sh

# Probar limpieza manual (requiere permisos sudo configurados)
./scripts/check_ram_cleanup.sh --test
```

### Paso 5: Reiniciar el servicio
```bash
sudo systemctl restart usipipo
sudo systemctl status usipipo
```

### Paso 6: Verificar que el job está activo
```bash
# Ver logs en tiempo real
sudo journalctl -u usipipo -f | grep -i "ram\|memoria\|limpieza"
```

Deberías ver:
```
⏰ Job de limpieza de RAM programado cada 10 minutos (umbral: 80%)
```

---

## Características

- **Monitoreo continuo**: Verifica el uso de RAM cada N minutos configurables
- **Limpieza inteligente**:
  - Nivel 1 (pagecache) cuando se supera el umbral estándar
  - Nivel 3 (todo) cuando se alcanza el umbral crítico
- **Compactación de memoria**: Reduce fragmentación de RAM
- **Notificaciones**: Alerta al admin por Telegram cuando se realiza limpieza
- **Limpieza manual**: Comando disponible para forzar limpieza inmediata

---

## Configuración Detallada (.env)

| Variable | Default | Rango | Descripción |
|----------|---------|-------|-------------|
| `MEMORY_CLEANUP_ENABLED` | `true` | `true/false` | Habilitar/deshabilitar limpieza |
| `MEMORY_CLEANUP_THRESHOLD_PERCENT` | `80` | 50-95 | Umbral para limpieza estándar |
| `MEMORY_CLEANUP_CRITICAL_PERCENT` | `90` | 60-99 | Umbral para limpieza agresiva |
| `MEMORY_CLEANUP_INTERVAL_MINUTES` | `10` | 1-60 | Minutos entre verificaciones |
| `MEMORY_NOTIFY_ADMIN` | `true` | `true/false` | Notificar por Telegram |

### Ejemplo de configuración conservadora:
```bash
MEMORY_CLEANUP_ENABLED=true
MEMORY_CLEANUP_THRESHOLD_PERCENT=85
MEMORY_CLEANUP_CRITICAL_PERCENT=95
MEMORY_CLEANUP_INTERVAL_MINUTES=15
MEMORY_NOTIFY_ADMIN=true
```

### Ejemplo de configuración agresiva:
```bash
MEMORY_CLEANUP_ENABLED=true
MEMORY_CLEANUP_THRESHOLD_PERCENT=70
MEMORY_CLEANUP_CRITICAL_PERCENT=85
MEMORY_CLEANUP_INTERVAL_MINUTES=5
MEMORY_NOTIFY_ADMIN=true
```

---

## Permisos Requeridos (Detallado)

El job necesita permisos para escribir en `/proc/sys/vm/drop_caches`.

### Opción 1: Configurar sudoers (RECOMENDADA)

```bash
# Obtener nombre de usuario actual
whoami

# Crear archivo de configuración sudo
sudo visudo -f /etc/sudoers.d/usipipo-ram
```

Agregar estas líneas (reemplaza `usipipo` con tu usuario):
```
usipipo ALL=(ALL) NOPASSWD: /bin/sync
usipipo ALL=(ALL) NOPASSWD: /bin/sh -c echo* > /proc/sys/vm/drop_caches
```

Verificar que funciona:
```bash
sudo -k  # resetear timestamp sudo
sudo /bin/sync  # no debería pedir password
```

### Opción 2: Usar grupo sudo existente

```bash
# Agregar usuario al grupo sudo (si no está)
sudo usermod -aG sudo $USER

# Luego configurar sudo sin password para los comandos específicos
sudo visudo -f /etc/sudoers.d/usipipo-ram
```

Contenido:
```
%sudo ALL=(ALL) NOPASSWD: /bin/sync, /bin/sh -c echo* > /proc/sys/vm/drop_caches
```

### Opción 3: Capability (avanzado, NO recomendado)

```bash
sudo setcap cap_sys_admin+ep /usr/bin/python3
```

⚠️ Precaución: Otorga privilegios especiales al intérprete Python.

### Opción 4: Ejecutar como root (NO recomendado para producción)

Editar el servicio systemd:
```bash
sudo systemctl edit usipipo
```

Agregar:
```ini
[Service]
User=root
```

---

## Verificación y Testing

### Script de verificación
```bash
# Ver estado y configuración
./scripts/check_ram_cleanup.sh

# Ver estado + probar limpieza
./scripts/check_ram_cleanup.sh --test

# Ver ayuda para sudoers
./scripts/check_ram_cleanup.sh --help-sudoers
```

### Ver logs del servicio
```bash
# Ver logs completos
sudo journalctl -u usipipo -n 100

# Ver solo logs de RAM
sudo journalctl -u usipipo -f | grep -i "ram\|memoria\|limpieza\|🧠\|🚨\|✅"

# Ver errores
sudo journalctl -u usipipo | grep -i "error\|❌"
```

### Test manual desde Python
```bash
# Entrar al entorno virtual
source venv/bin/activate

# Ejecutar test
python3 << 'EOF'
import asyncio
from infrastructure.jobs.memory_cleanup_job import get_memory_info, force_memory_cleanup

# Ver estado actual
info = get_memory_info()
print(f"RAM Total: {info['total_gb']} GB")
print(f"RAM Usada: {info['used_gb']} GB ({info['used_percent']}%)")
print(f"RAM Disponible: {info['available_gb']} GB")
EOF
```

---

## Uso Manual (Desde Código)

```python
from infrastructure.jobs.memory_cleanup_job import (
    force_memory_cleanup,
    get_memory_info,
    drop_caches
)

# Ver estado actual
mem_info = get_memory_info()
print(f"RAM usada: {mem_info['used_percent']}%")

# Forzar limpieza inmediata (requiere context de Telegram)
result = await force_memory_cleanup(context)
if result['success']:
    print(f"Liberados: {result['freed_mb']} MB")
    print(f"Antes: {result['before_percent']}%, Después: {result['after_percent']}%")
else:
    print(f"Error: {result['error']}")
```

---

## Logs Esperados

### Inicio del job
```
⏰ Job de limpieza de RAM programado cada 10 minutos (umbral: 80%)
```

### Funcionamiento normal
```
🧠 RAM: 2.15/8.00 GB (26.9%)
```

### Limpieza ejecutada
```
🚨 RAM alta detectada: 85% (umbral: 80%)
✅ Limpieza estándar (nivel 1) completada. RAM liberada: 245.3 MB. Ahora: 72%
```

### Nivel crítico
```
🔥 Nivel CRÍTICO de RAM: 93%
✅ Limpieza agresiva (nivel 3) completada. RAM liberada: 512.8 MB. Ahora: 78%
```

### Error de permisos
```
❌ Permiso denegado para limpiar caché. Ejecutar como root o añadir a sudoers.
```

---

## Troubleshooting

### "Permiso denegado para limpiar caché"

**Causa**: El usuario no tiene permisos para escribir en `/proc/sys/vm/drop_caches`

**Solución**:
1. Configurar sudoers (ver Paso 3 arriba)
2. Reiniciar el servicio: `sudo systemctl restart usipipo`

### No se notifica al admin

**Causa**: `ADMIN_ID` no está configurado o el bot no puede enviar mensajes

**Solución**:
```bash
# Verificar ADMIN_ID en .env
grep ADMIN_ID .env

# Probar envío de mensaje al admin
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<ADMIN_ID>&text=Test"
```

### Limpieza muy frecuente

**Causa**: Umbral muy bajo o intervalo muy corto

**Solución**:
```bash
# Aumentar umbral e intervalo
MEMORY_CLEANUP_THRESHOLD_PERCENT=85
MEMORY_CLEANUP_INTERVAL_MINUTES=15
```

### El job no aparece en los logs

**Causa**: Job no registrado o `MEMORY_CLEANUP_ENABLED=false`

**Solución**:
```bash
# Verificar configuración
grep MEMORY_CLEANUP .env

# Verificar que el job está programado
sudo journalctl -u usipipo | grep "limpieza de RAM programado"

# Reiniciar servicio
sudo systemctl restart usipipo
```

### Error "sync falló"

**Causa**: Problema con permisos de sudo

**Solución**:
```bash
# Verificar que sudo funciona sin password
sudo -k
sudo /bin/sync

# Si pide password, revisar configuración de sudoers
```

---

## Comandos Útiles

```bash
# Ver uso de RAM en tiempo real
watch -n 1 free -h

# Ver procesos que consumen más RAM
ps aux --sort=-%mem | head -10

# Limpiar caché manualmente (como root)
sudo sync && echo 1 | sudo tee /proc/sys/vm/drop_caches

# Ver configuración de memoria del kernel
sysctl -a | grep vm

# Ver estadísticas de memoria
cat /proc/meminfo | head -10
```

---

## Referencias

- [Linux Kernel - drop_caches](https://www.kernel.org/doc/Documentation/sysctl/vm.txt)
- [Linux Memory Management](https://www.kernel.org/doc/gorman/html/understand/understand013.html)
- `/proc/meminfo` documentation
- `sync` command manual: `man sync`

---

## Soporte

Si tienes problemas:

1. Revisar logs: `sudo journalctl -u usipipo -n 200`
2. Verificar permisos: `./scripts/check_ram_cleanup.sh`
3. Probar manualmente el script de verificación
4. Revisar que las variables estén en `.env`
