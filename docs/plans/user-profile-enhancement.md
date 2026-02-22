# Plan: Mejora del Perfil e Información de Usuario

**Issue:** #128  
**Fecha:** 2026-02-22  
**Prioridad:** Alta

---

## 📊 Análisis del Estado Actual

### Implementado
| Componente | Archivo | Estado |
|------------|---------|--------|
| Entidad User | `domain/entities/user.py` | ✅ Completo |
| Repositorio User | `infrastructure/persistence/postgresql/user_repository.py` | ✅ Completo |
| Handler /info | `telegram_bot/features/user_management/handlers_user_management.py:283` | 🔶 Parcial |
| Handler /status | `telegram_bot/features/user_management/handlers_user_management.py:195` | 🔶 Parcial |
| Mensajes de perfil | `telegram_bot/features/user_management/messages_user_management.py` | 🔶 Parcial |
| Servicio VPN status | `application/services/vpn_service.py:127` | 🔶 Parcial |
| Modelo Transaction | `infrastructure/persistence/postgresql/models/base.py:141` | ✅ Completo |
| Repositorio Transaction | `infrastructure/persistence/postgresql/transaction_repository.py` | ✅ Existe |

### No Implementado / Pendiente
| Funcionalidad | Descripción |
|---------------|-------------|
| Historial de transacciones visible | Usuario no puede ver sus transacciones |
| Resumen de paquetes de datos | No se muestran paquetes activos |
| Datos gratuitos restantes | Información parcial |
| Estadísticas de uso por período | No existe |

---

## 🎯 Objetivos

1. Mostrar información completa y precisa del usuario en `/info`
2. Mostrar historial de transacciones del usuario
3. Mostrar resumen de paquetes de datos activos
4. Mejorar el comando `/status` con datos completos

---

## 📝 Tareas

### Fase 1: Mejorar comando `/info`

#### 1.1 Actualizar mensajes de información
- **Archivo:** `telegram_bot/features/user_management/messages_user_management.py`
- **Cambios:**
  - Eliminar campos `level` y `achievements` (no se usarán)
  - Agregar campo `free_data_remaining`
  - Agregar campo `active_packages`
  - Agregar campo `total_referrals`

#### 1.2 Actualizar handler `/info`
- **Archivo:** `telegram_bot/features/user_management/handlers_user_management.py`
- **Cambios:**
  - Obtener paquetes de datos activos del usuario
  - Calcular datos gratuitos restantes
  - Obtener conteo de referidos
  - Eliminar valores hardcodeados

#### 1.3 Crear/actualizar servicio de perfil
- **Archivo:** `application/services/user_profile_service.py` (nuevo)
- **Funcionalidad:**
  - `get_user_profile_summary(user_id)` - Resumen completo
  - `get_user_transactions(user_id, limit)` - Historial
  - `get_user_packages_summary(user_id)` - Paquetes activos

### Fase 2: Implementar historial de transacciones

#### 2.1 Agregar método al repositorio de transacciones
- **Archivo:** `infrastructure/persistence/postgresql/transaction_repository.py`
- **Método:** `get_by_user_id(user_id, limit)`

#### 2.2 Crear comando `/history` o agregar al perfil
- **Opción A:** Nuevo comando `/history` para ver transacciones
- **Opción B:** Agregar botón en `/info` para ver historial

#### 2.3 Crear mensajes y keyboards
- **Archivo:** `telegram_bot/features/user_management/messages_user_management.py`
- Agregar clase `History` con mensajes de historial

### Fase 3: Mostrar paquetes de datos

#### 3.1 Agregar método al servicio de paquetes
- **Archivo:** `application/services/data_package_service.py`
- **Método:** `get_active_packages(user_id)` - Ya existe `get_user_packages()`

#### 3.2 Mostrar en el perfil
- Agregar sección de paquetes activos en `/info`
- Mostrar: nombre, datos restantes, fecha expiración

### Fase 4: Mejorar comando `/status`

#### 4.1 Actualizar `get_user_status()`
- **Archivo:** `application/services/vpn_service.py:127`
- Agregar:
  - `free_data_remaining_gb`
  - `active_packages_count`
  - `referrals_count`

#### 4.2 Actualizar mensajes de status
- **Archivo:** `telegram_bot/features/user_management/messages_user_management.py`
- Agregar campos adicionales

---

## 🗂️ Archivos a Modificar/Crear

### Modificar
1. `domain/entities/user.py` - Sin cambios necesarios
2. `telegram_bot/features/user_management/handlers_user_management.py`
3. `telegram_bot/features/user_management/messages_user_management.py`
4. `application/services/vpn_service.py`
5. `infrastructure/persistence/postgresql/transaction_repository.py`

### Crear
1. `application/services/user_profile_service.py` (opcional, puede integrarse en vpn_service)
2. `tests/application/services/test_user_profile_service.py`

---

## 📐 Especificaciones de UI

### Comando `/info` - Nueva estructura
```
ℹ️ **Información de tu Cuenta**

👤 **Usuario:** Juan Pérez
🆔 **ID:** 123456789
👥 **Username:** @juanperez
📅 **Registro:** 2025-01-15
🟢 **Estado:** Activo ✅

📊 **Datos:**
├─ Usados: 5.23 GB
├─ Gratuitos restantes: 4.77 GB
└─ Paquetes activos: 2 (50 GB)

🔑 **Claves VPN:**
├─ Usadas: 2/3
└─ Protocolos: WireGuard (1), Outline (1)

🎁 **Referidos:**
├─ Código: ABC123
├─ Invitados: 5
└─ Créditos: 500
```

### Comando `/history` - Nueva estructura
```
📜 **Historial de Transacciones**

*Últimos 5 movimientos:*

1️⃣ `2026-02-20` - Paquete 50GB
   ⭐ 200 Stars | ✅ Completado

2️⃣ `2026-02-15` - Bonus referido
   🎁 +100 créditos | Usuario 987654

3️⃣ `2026-02-10` - +1 Slot de clave
   ⭐ 50 Stars | ✅ Completado

📄 Ver más | 🏠 Menú principal
```

---

## ✅ Criterios de Aceptación

- [ ] `/info` muestra información completa sin valores hardcodeados
- [ ] `/info` muestra datos gratuitos restantes
- [ ] `/info` muestra número de paquetes activos
- [ ] `/info` muestra conteo de referidos
- [ ] Existe forma de ver historial de transacciones
- [ ] `/status` muestra resumen de datos y claves
- [ ] Tests unitarios para nuevos métodos
- [ ] Tests de integración para handlers

---

## 📅 Estimación

| Fase | Tiempo |
|------|--------|
| Fase 1: Mejorar `/info` | 2-3 horas |
| Fase 2: Historial transacciones | 2-3 horas |
| Fase 3: Paquetes de datos | 1-2 horas |
| Fase 4: Mejorar `/status` | 1 hora |
| Testing | 2 horas |
| **Total** | **8-11 horas** |

---

## 🔄 Dependencias

- Ninguna nueva dependencia externa
- Usa infraestructura existente (PostgreSQL, repositorios)

---

## 📌 Notas

- No implementar sistema de gamificación/niveles/achievements (fuera de scope)
- Mantener consistencia con el estilo de mensajes actual
- Seguir patrones de Clean Architecture existentes
