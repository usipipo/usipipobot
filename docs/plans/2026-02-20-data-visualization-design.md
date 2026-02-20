# Data Visualization Design (Issue #79)

**Goal:** Implementar visualización detallada del consumo de datos del usuario, mostrando paquetes individuales, Plan Free y total disponible.

**Architecture:** Extender el servicio existente `DataPackageService.get_user_data_summary()` para incluir información del Plan Free y detalles de cada paquete. Actualizar mensajes y handler para mostrar el nuevo formato.

**Tech Stack:** Python, asyncio, dataclasses

---

## Cambios Requeridos

### 1. DataPackageService

Extender `get_user_data_summary()` para:
- Obtener datos del Plan Free desde `user_repo`
- Devolver lista detallada de paquetes con nombre, días restantes, usado/disponible
- Calcular totales incluyendo Plan Free

### 2. BuyGbMessages.Data

Nuevo formato de mensaje con:
- Sección de paquetes activos (nombre, días, usado/disponible)
- Sección de Plan Free
- Total disponible
- Nota sobre orden de consumo

### 3. BuyGbHandler.data_handler()

Usar la nueva estructura de datos y formato de mensaje.

---

## Estructura de Datos

```python
{
    "active_packages": 2,
    "packages": [
        {
            "name": "Básico",
            "total_gb": 10.0,
            "used_gb": 3.2,
            "remaining_gb": 6.8,
            "days_remaining": 15
        },
    ],
    "free_plan": {
        "limit_gb": 10.0,
        "used_gb": 1.5,
        "remaining_gb": 8.5
    },
    "total_limit_gb": 20.0,
    "total_used_gb": 4.7,
    "remaining_gb": 15.3
}
```

---

## Formato de Mensaje Final

```
💾 Tu Consumo de Datos

═══════════════════════

📦 Paquetes Activos:
   • Básico 10GB (15 días restantes)
     Usado: 3.2 GB / 10 GB
     Disponible: 6.8 GB

═══════════════════════

🎁 Plan Free:
   Disponible: 8.5 GB

═══════════════════════

📊 TOTAL DISPONIBLE: 15.3 GB

💡 El consumo usa primero los paquetes comprados
```
