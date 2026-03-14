# Product Requirements Document (PRD)

## 1. Visión del Producto

uSipipo Bot es un sistema de gestión VPN que permite a usuarios crear y administrar claves VPN (WireGuard y Outline) directamente desde Telegram. El sistema está diseñado para facilitar el acceso a VPNs de manera sencilla, rápida y segura.

### Propósito
Simplificar la creación y gestión de conexiones VPN para usuarios no técnicos mediante una interfaz conversacional en Telegram.

### Audiencia Objetivo
- Usuarios que necesitan acceso VPN simple y rápido
- Administradores de servidores VPN
- Usuarios de Telegram que buscan privacidad online

---

## 2. Funcionalidades Principales

### 2.1 Gestión de VPN
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Crear claves VPN | Generar nuevas claves WireGuard u Outline | Alta |
| Listar claves | Ver todas las claves activas del usuario | Alta |
| Eliminar claves | Remover claves específicas o todas | Alta |
| Renovar claves | Extender tiempo de expiración | Media |
| Seleccionar servidor | Elegir ubicación del servidor VPN | Media |

### 2.2 Sistema de Usuarios
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Registro automático | Crear cuenta al iniciar `/start` | Alta |
| Perfil de usuario | Ver información y estadísticas | Alta |
| Sistema de referidos | Invitar amigos y ganar créditos | Alta |
| Canje de créditos | Cambiar créditos por GB o slots | Alta |
| Soporte al usuario | Chat directo con administradores | Media |

### 2.3 Sistema de Pagos
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Telegram Stars | Pagar con la moneda nativa de Telegram | Alta |
| Planes Gratis | Cuota mensual de 10GB gratuitos | Alta |
| Paquetes de Datos | 10/25/50/100 GB con Stars | Alta |
| Slots de Claves | Comprar claves adicionales (+1/+3/+5) | Alta |
| Historial de transacciones | Ver movimientos de estrellas | Media |

### 2.4 Panel de Administración
| Funcionalidad | Descripción | Prioridad |
|--------------|-------------|-----------|
| Gestión de usuarios | Ver y administrar usuarios | Alta |
| Gestión de servidores | Monitorear servidores VPN | Alta |
| Eliminación de claves | Remover claves de cualquier usuario | Alta |
| Broadcast masivo | Enviar mensajes a todos los usuarios | Media |
| Sistema de tickets | Gestión de soporte técnico | Media |
| Estadísticas | Métricas de uso y rendimiento | Media |

---

## 3. Flujos de Usuario

### 3.1 Flujo Principal (Nuevo Usuario)
```
/start → Verificar registro → Crear cuenta → Mostrar menú principal
```

### 3.2 Flujo de Creación de Clave VPN
```
Menú Principal → "Crear Nueva" → Seleccionar Protocolo
→ Seleccionar Servidor → Generar Clave → Mostrar Configuración
```

### 3.3 Flujo de Compra de GB
```
Menú Principal → "Comprar GB" → Seleccionar Paquete
→ Confirmar Pago (Stars) → Aplicar GB a cuenta
```

### 3.4 Flujo de Soporte
```
Menú Principal → "Soporte" → Enviar mensaje
→ Esperar respuesta del admin → Notificación
```

### 3.5 Flujo de Referidos
```
Menú Principal → /referir → Ver código y link → Compartir
→ Amigo se registra → Recibir 100 créditos
→ Canjear por GB (100 créditos) o +1 slot (500 créditos)
```

---

## 4. Requisitos Técnicos

### 4.1 Funcionales
- [ ] El bot debe responder a comandos básicos (/start, /help)
- [ ] Los usuarios deben poder crear hasta N claves simultáneas
- [ ] Las claves deben expirar automáticamente después de X días
- [ ] El sistema debe soportar múltiples servidores VPN
- [ ] Los pagos deben procesarse mediante Telegram Stars
- [ ] El sistema de referidos debe trackear invitaciones correctamente

### 4.2 No Funcionales
- **Rendimiento:** Respuesta del bot < 2 segundos
- **Disponibilidad:** 99.5% uptime
- **Escalabilidad:** Soportar 10,000+ usuarios concurrentes
- **Seguridad:** Encriptación de datos sensibles, validación de inputs
- **Usabilidad:** Interfaz intuitiva, sin necesidad de conocimientos técnicos

### 4.3 Restricciones
- Depende de la API de Telegram
- Requiere servidores VPN dedicados
- Limitado a protocolos WireGuard y Outline
- Pagos solo mediante Telegram Stars

---

## 5. Definición de Éxito

### Métricas Clave (KPIs)
- Número de usuarios activos mensuales
- Tasa de conversión de usuarios gratis a VIP
- Tiempo promedio de vida de una clave VPN
- NPS (Net Promoter Score) de usuarios
- Tiempo de respuesta del bot

### Criterios de Aceptación
- [ ] Usuario puede crear una clave VPN en < 3 pasos
- [ ] Sistema de pagos funciona sin errores > 99%
- [ ] Tiempo de respuesta promedio < 2 segundos
- [ ] Documentación completa y actualizada

---

## 6. Roadmap

### Fase 1: Documentación Esencial ✅
- [x] Crear PRD, APPFLOW, TECHNOLOGY
- [x] Actualizar README.md

### Fase 2: Core VPN ✅
- [x] Implementar creación de claves WireGuard
- [x] Implementar creación de claves Outline
- [x] Gestión básica de claves

### Fase 3: Sistema de Pagos ✅
- [x] Integración Telegram Stars
- [x] Paquetes de Datos (10/25/50/100 GB)
- [x] Sistema de créditos por referidos
- [x] Compra de slots de claves

### Fase 4: Admin Avanzado 🔶
- [x] Dashboard básico
- [ ] Estadísticas en tiempo real
- [x] Automatización de tareas (jobs de expiración, sync, cleanup)

---

*Documento versión 2.0 - Fecha: 2026-02-22*
