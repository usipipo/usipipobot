# 06 — Módulo Crear Clave VPN

## Objetivo
Guiar al usuario paso a paso para crear una nueva clave VPN, eligiendo el tipo de protocolo y servidor, con validaciones claras antes de confirmar la creación.

---

## Flujo Completo de Creación

```
[Usuario toca [+] en lista de claves]
        │
        ▼
┌─────────────────────────────┐
│  ¿Puede crear más claves?   │
│  GET /api/v1/keys/can-create│
└──────────┬──────────────────┘
           │
  ┌────────┴────────┐
  │ SÍ              │ NO
  ▼                 ▼
[Paso 1]     [Dialog: "Límite alcanzado
              Tienes 2/2 claves activas.
              Elimina una para crear otra."
              [Ir a Claves] [Cancelar]]

──────────────────────────────────────────

PASO 1: Elige el tipo de protocolo

┌─────────────────────────────────────┐
│  Nueva Clave · Paso 1 de 3          │
│                                     │
│  ¿Qué protocolo quieres usar?       │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🔵 OUTLINE (Shadowsocks)    │    │
│  │                             │    │
│  │ ✅ Más compatible           │    │
│  │ ✅ Fácil de configurar      │    │
│  │ ✅ Funciona en la mayoría   │    │
│  │    de países con censura    │    │
│  │                             │    │
│  │ 📱 App: Outline Client      │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 🟣 WIREGUARD                │    │
│  │                             │    │
│  │ ✅ Más rápido               │    │
│  │ ✅ Mejor para gaming/video  │    │
│  │ ⚠️ Puede ser bloqueado en   │    │
│  │    algunos países           │    │
│  │                             │    │
│  │ 📱 App: WireGuard           │    │
│  └─────────────────────────────┘    │
│                                     │
│  [Cancelar]                         │
└─────────────────────────────────────┘

──────────────────────────────────────────

PASO 2: Nombra tu clave

┌─────────────────────────────────────┐
│  Nueva Clave · Paso 2 de 3          │
│                                     │
│  Protocolo: 🔵 Outline              │
│                                     │
│  Dale un nombre a esta clave        │
│  para identificarla fácilmente:     │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Mi iPhone                   │    │  ← MDTextField
│  └─────────────────────────────┘    │
│                                     │
│  Sugerencias:                       │
│  [Mi iPhone]  [Mi PC]  [Mi tablet]  │  ← Chips tocables
│  [Trabajo]    [Casa]   [Viajes]     │
│                                     │
│  Máximo 30 caracteres (12/30)       │
│                                     │
│  [Atrás]              [Siguiente →] │
└─────────────────────────────────────┘

──────────────────────────────────────────

PASO 3: Confirmación

┌─────────────────────────────────────┐
│  Nueva Clave · Paso 3 de 3          │
│                                     │
│  Resumen de tu nueva clave:         │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  Nombre:    Mi iPhone       │    │
│  │  Protocolo: Outline         │    │
│  │  Límite:    5 GB incluidos  │    │
│  │  Servidor:  Outline Server  │    │
│  └─────────────────────────────┘    │
│                                     │
│  ℹ️ Esta clave usará tus datos      │
│  disponibles. Si no tienes          │
│  paquete activo, tienes 5 GB        │
│  gratuitos.                         │
│                                     │
│  [Atrás]          [✅ Crear Clave] │
└─────────────────────────────────────┘
```

---

## Flujo de Creación Backend

```
[Tap "Crear Clave"]
        │
        ▼
[Muestra indicador de carga]
"Creando tu clave VPN..."
        │
        ▼
[POST /api/v1/keys/create]
{
  "key_type": "outline",
  "name": "Mi iPhone"
}
        │
┌───────┴────────────────────────────┐
│ 201 Created                        │ Error
▼                                    ▼
{                             [MDDialog con
  "id": "uuid",                error específico:
  "key_data": "ss://...",      - "Ya tienes una
  "name": "Mi iPhone",           clave Outline"
  "key_type": "outline",       - "Sin datos
  "qr_url": "/keys/.../qr"       disponibles"
}                              - "Error del servidor"
        │
        ▼
[PANTALLA DE ÉXITO]
```

---

## Pantalla de Éxito Post-Creación

```
┌─────────────────────────────────────┐
│                                     │
│         ✅                          │
│   ¡Clave creada exitosamente!       │
│                                     │
│   Mi iPhone · Outline               │
│                                     │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │       [QR CODE AQUÍ]        │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
│  ss://eyJ...                        │
│  (texto truncado con "...")         │
│                                     │
│  [📋 Copiar código]                 │
│                                     │
│  ─── Cómo conectarte ───           │
│                                     │
│  1. Descarga Outline Client        │
│     en tu iPhone                   │
│  2. Toca el QR o pega el código    │
│  3. ¡Listo! Ya tienes VPN          │
│                                     │
│  [Ver mis claves]  [Ir al inicio]  │
└─────────────────────────────────────┘
```

---

## Validaciones del Lado APK (Previas al Request)

Antes de enviar el request de creación, la APK valida localmente para dar feedback inmediato:

1. **Nombre no vacío:** el campo nombre no puede estar en blanco
2. **Nombre no muy corto:** mínimo 2 caracteres
3. **Nombre no muy largo:** máximo 30 caracteres
4. **Tipo seleccionado:** no puede continuar sin seleccionar Outline o WireGuard

Estas validaciones son de UI solamente. El backend hace sus propias validaciones de negocio que son las que mandan.

---

## Restricción: Un Tipo de Clave por Servidor

La lógica existente en `can_create_key_type()` del dominio establece que un usuario solo puede tener una clave por tipo de servidor. La APK refleja esto de la siguiente manera:

Si el usuario ya tiene una clave Outline activa y toca la opción Outline en el Paso 1, se muestra un mensaje inline debajo de la card: "Ya tienes una clave Outline activa. Elimínala para crear otra." y la opción queda deshabilitada visualmente (opacity reducida, sin tap).

Lo mismo para WireGuard.

---

## Notas de UX

- La pantalla de éxito con el QR debe tener un brillo/resplandor visual alrededor del QR (efecto neon cyan) para hacer memorable el momento.
- El botón "Copiar código" debe tener feedback inmediato (cambio de color + snackbar).
- Si el usuario cierra la pantalla de éxito sin copiar el código, se muestra un dialog: "¿Salir sin copiar? Podrás ver tu clave en cualquier momento desde Mis Claves."
