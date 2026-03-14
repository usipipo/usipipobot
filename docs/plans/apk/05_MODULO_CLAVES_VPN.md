# 05 — Módulo Claves VPN (Listado y Detalle)

## Objetivo
Permitir al usuario ver todas sus claves VPN, su estado de uso, y acceder al detalle de cada una para copiar la configuración, ver el QR, o gestionar la clave.

---

## Pantalla: Lista de Claves

```
┌─────────────────────────────────────┐
│  ← Mis Claves VPN          [+]      │  ← [+] abre flujo Crear Clave
├─────────────────────────────────────┤
│                                     │
│  Tienes 2/2 claves activas          │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔵 Mi iPhone                │    │
│  │ Outline · Servidor: Outline │    │
│  │ ████████░░  1.2 GB / 5 GB  │    │
│  │ ● Activa · Vence: 24 feb   │    │
│  │                    [Ver →] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🟣 Mi PC de trabajo         │    │
│  │ WireGuard · Servidor: WG   │    │
│  │ ███░░░░░░░  450 MB / 5 GB  │    │
│  │ ● Activa · Sin vencimiento │    │
│  │                    [Ver →] │    │
│  └─────────────────────────────┘    │
│                                     │
│  ─── Claves Inactivas ───           │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ⚫ Mi tablet (antigua)      │    │
│  │ Outline · Expirada         │    │
│  │ ○ Inactiva                 │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

### Elementos de cada Card de Clave
- **Ícono de color:** azul para Outline, morado para WireGuard
- **Nombre personalizado** de la clave
- **Tipo y servidor**
- **Barra de progreso de datos:** con colores adaptivos (cyan/ámbar/rojo)
- **Uso exacto:** en MB o GB según el volumen
- **Estado:** punto verde (activa), gris (inactiva), rojo (expirada/sobre límite)
- **Fecha de vencimiento** si aplica
- **Botón "Ver →"** que abre el detalle

---

## Pantalla: Detalle de Clave

```
┌─────────────────────────────────────┐
│  ←  Mi iPhone                [⋮]   │  ← [⋮] menú: Renombrar, Eliminar
├─────────────────────────────────────┤
│                                     │
│  ● ACTIVA                           │
│  Outline VPN · Creada: 15 ene 2026  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │         📊 USO DE DATOS     │    │
│  │                             │    │
│  │    1.2 GB   de   5.0 GB    │    │
│  │  ████████████░░░░░░░░  24% │    │
│  │                             │    │
│  │  Restante: 3.8 GB          │    │
│  │  Reset: 15 feb 2026        │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │    📱 CÓDIGO DE CONEXIÓN    │    │
│  │                             │    │
│  │  [         QR CODE         ]│    │
│  │                             │    │
│  │  ss://eyJ...truncado...    │    │
│  │                             │    │
│  │  [📋 Copiar]  [📤 Compartir]│    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  ℹ️  INFORMACIÓN TÉCNICA   │    │
│  │                             │    │
│  │  Tipo: Outline (Shadowsocks)│    │
│  │  Último uso: hace 2 horas  │    │
│  │  ID externo: 42             │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  📥 CÓMO CONECTARSE        │    │
│  │  1. Descarga Outline o     │    │
│  │     WireGuard app          │    │
│  │  2. Escanea el QR o        │    │
│  │     pega el código         │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

---

## Flujo de Carga del Detalle

```
[Tap en clave del listado]
        │
        ▼
[GET /api/v1/keys/{key_id}]
Respuesta:
{
  "id": "uuid",
  "name": "Mi iPhone",
  "key_type": "outline",
  "key_data": "ss://...",
  "is_active": true,
  "used_bytes": 1288490188,
  "data_limit_bytes": 5368709120,
  "created_at": "2026-01-15T...",
  "expires_at": "2026-02-15T...",
  "last_seen_at": "2026-02-10T...",
  "billing_reset_at": "2026-02-15T..."
}
        │
        ▼
[Genera QR code con librería qrcode]
[key_data → imagen QR → textura Kivy]
        │
        ▼
[Renderiza pantalla]
```

---

## Función: Copiar Código de Conexión

```
[Tap en botón "Copiar"]
        │
        ▼
[Copia key_data al portapapeles del sistema]
(usando Kivy: Clipboard.copy(key_data))
        │
        ▼
[Muestra MDSnackbar]
"✅ Código copiado al portapapeles"
(desaparece en 3 segundos)
        │
        ▼
[Vibración háptica breve]
(50ms, feedback de confirmación)
```

---

## Función: Compartir Clave

```
[Tap en botón "Compartir"]
        │
        ▼
[Muestra MDBottomSheet con opciones]
  ├── "Compartir como texto" → Android Share Intent con key_data
  ├── "Compartir QR como imagen" → Guarda QR y abre Share Intent
  └── "Enviar a Telegram" → Deep link a chat con el texto
        │
        ▼
[Android nativo maneja el compartir]
```

---

## Flujo: Renombrar Clave

```
[Menú ⋮ → Renombrar]
        │
        ▼
[MDDialog con campo de texto]
Placeholder: nombre actual de la clave
Máximo: 30 caracteres
        │
[Tap "Guardar"]
        │
        ▼
[PATCH /api/v1/keys/{key_id}]
{name: "nuevo nombre"}
        │
        ▼
[Actualiza la UI inmediatamente]
[Snackbar: "Nombre actualizado"]
```

---

## Flujo: Eliminar Clave

```
[Menú ⋮ → Eliminar]
        │
        ▼
[MDDialog de confirmación]
"⚠️ ¿Eliminar Mi iPhone?"
"Esta acción es irreversible. 
 La clave dejará de funcionar."
        │
[Tap "Eliminar"]
        │
        ▼
[DELETE /api/v1/keys/{key_id}]
        │
┌───────┴────────┐
│ OK             │ Error (sin créditos)
▼                ▼
[Vuelve a lista] [MDDialog: "Necesitas créditos
[Snackbar:        de referido para eliminar
 "Clave           claves. Invita amigos."]
 eliminada"]
```

**Nota sobre eliminación:** La lógica de negocio existente (`can_delete_keys()`) requiere que el usuario tenga `referral_credits > 0` para eliminar claves, excepto administradores. La APK respeta esta restricción y comunica claramente al usuario por qué no puede eliminar.

---

## Estados de la Barra de Progreso de Datos

| Porcentaje usado | Color barra | Color texto | Acción sugerida |
|---|---|---|---|
| 0% - 60% | Cyan (#00f0ff) | Normal | Ninguna |
| 60% - 85% | Ámbar (#ff9500) | Ámbar | Banner: "Considera comprar más GB" |
| 85% - 99% | Rojo (#ff4444) | Rojo | Snackbar: "¡Quedan pocos GB!" + botón Comprar |
| 100% | Rojo parpadeante | Rojo | Overlay: "Límite alcanzado. Compra más GB." |
