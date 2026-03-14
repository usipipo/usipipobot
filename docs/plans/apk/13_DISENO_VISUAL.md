# 13 — Sistema de Diseño Visual

## Objetivo
Definir el sistema de diseño de la APK para mantener consistencia visual con el mini app web (tema cyberpunk) y con las imágenes de referencia proporcionadas (diseño azul claro con fondo oscuro).

---

## Paleta de Colores

La APK hereda exactamente la paleta del `cyberpunk.css` del mini app web:

| Variable | Color Hex | Uso |
|---|---|---|
| `--bg-void` | `#0a0a0f` | Fondo de pantallas principales |
| `--bg-surface` | `#12121a` | Fondo de la bottom navigation bar |
| `--bg-card` | `#1a1a24` | Cards, paneles, bottom sheets |
| `--neon-cyan` | `#00f0ff` | Color primario, acentos, botones principales |
| `--neon-magenta` | `#ff00aa` | Color secundario, etiquetas de estado especial |
| `--terminal-green` | `#00ff41` | Estados positivos, "Activo", "Conectado" |
| `--amber` | `#ff9500` | Advertencias, datos al 75-90% |
| `--text-primary` | `#e0e0e0` | Texto principal |
| `--text-secondary` | `#8a8a9a` | Texto secundario, labels |
| `--text-muted` | `#5a5a6a` | Texto de marcador de posición, fechas |
| Error | `#ff4444` | Estados de error, datos al 100%, cuenta suspendida |

---

## Notas sobre las Imágenes de Referencia

Las imágenes enviadas muestran otra app VPN con diseño azul claro sobre fondo blanco. La APK de uSipipo NO copia ese diseño directamente. En cambio, adapta el concepto (lista de servidores, botón de conexión central, indicadores de latencia) al tema cyberpunk oscuro que ya tiene el ecosistema uSipipo. Esto garantiza consistencia visual entre el bot, el mini app y la APK.

**Elementos que SÍ se adaptan de las imágenes de referencia:**
- Layout de lista de servidores con bandera del país + latencia + badge "Free/VIP"
- Botón circular grande de conexión/desconexión (para versión futura con conexión directa)
- Pestañas Free / VIP / Historial en el selector de servidores

---

## Tipografía

| Fuente | Archivo | Uso |
|---|---|---|
| JetBrains Mono Regular | `JetBrainsMono-Regular.ttf` | Claves VPN, direcciones wallet, estadísticas numéricas, códigos |
| JetBrains Mono Bold | `JetBrainsMono-Bold.ttf` | Números importantes, títulos de datos técnicos |
| Roboto Regular | Sistema Android | Texto general, labels, descripciones |
| Roboto Medium | Sistema Android | Títulos de pantallas, labels activos de nav |

---

## Sistema de KivyMD: Configuración del Tema

En el archivo `main.py` de la APK, el tema de KivyMD se configura así:

```
MDTheme:
  primary_palette: "Cyan"         → Color principal para componentes MDButton, MDSwitch
  accent_palette: "Pink"          → Color de acento para MDCheckbox, cursores
  theme_style: "Dark"             → Fondo oscuro nativo en todos los widgets
```

Adicionalmente, los colores exactos de la paleta cyberpunk se aplican manualmente en el código KV para sobreescribir donde sea necesario.

---

## Componentes UI y Especificaciones

### Cards (MDCard)
```
md_bg_color: [26/255, 26/255, 36/255, 1]   → --bg-card
radius: [12, 12, 12, 12]                     → Esquinas redondeadas 12dp
elevation: 0                                 → Sin sombra (diseño flat)
padding: [16, 16, 16, 16]
```
Borde opcional neon:
```
canvas.before:
  Color: [0/255, 240/255, 255/255, 0.3]     → --neon-cyan con 30% opacidad
  Line: width=1, rounded_rectangle=...
```

### Botones Primarios (MDRaisedButton)
```
md_bg_color: [0/255, 240/255, 255/255, 1]  → --neon-cyan
text_color: [10/255, 10/255, 15/255, 1]    → --bg-void (texto oscuro sobre cyan)
font_name: "Roboto"
font_size: 14
height: 48
radius: [8]
```

### Botones Secundarios / Outline (MDOutlineButton)
```
line_color: [0/255, 240/255, 255/255, 0.5]
text_color: [0/255, 240/255, 255/255, 1]
```

### Campos de Texto (MDTextField)
```
line_color_normal: [90/255, 90/255, 106/255, 1]   → --text-muted
line_color_focus: [0/255, 240/255, 255/255, 1]    → --neon-cyan
hint_text_color_normal: [90/255, 90/255, 106/255, 1]
hint_text_color_focus: [0/255, 240/255, 255/255, 1]
text_color_normal: [224/255, 224/255, 224/255, 1]  → --text-primary
```

### Bottom Navigation (MDBottomNavigation)
```
md_bg_color: [18/255, 18/255, 26/255, 1]           → --bg-surface
text_color_active: [0/255, 240/255, 255/255, 1]    → --neon-cyan
text_color_inactive: [90/255, 90/255, 106/255, 1]  → --text-muted
```

### Barras de Progreso de Datos (MDProgressBar)
La barra cambia de color dinámicamente según el porcentaje:
```
0-60%:   [0/255, 240/255, 255/255, 1]    → --neon-cyan
60-85%:  [255/255, 149/255, 0/255, 1]    → --amber
85-100%: [255/255, 68/255, 68/255, 1]    → rojo
```

### Snackbars (MDSnackbar)
```
md_bg_color: [26/255, 26/255, 36/255, 0.95]
text_color: [224/255, 224/255, 224/255, 1]
duration: 3           → 3 segundos
y: 16                 → 16dp sobre el bottom nav
```

### Badges de Notificación
```
MDBadge:
  md_bg_color: [255/255, 0/255, 170/255, 1]     → --neon-magenta
  text_color: [255/255, 255/255, 255/255, 1]
  font_size: 10
```

---

## Animaciones

### Transiciones entre Pantallas
- **Fade:** 0.2 segundos de fade in al entrar a una pantalla nueva
- **Slide:** slide horizontal al navegar hacia adelante/atrás en un flujo (ej: pasos de crear clave)

### Skeleton Loader (mientras carga datos)
- Rectángulos con fondo `--bg-card` que tienen una animación de shimmer de izquierda a derecha
- Color del shimmer: `rgba(0, 240, 255, 0.05)` → un destello muy tenue de cyan

### Efecto Glitch del Logo
En la pantalla de splash y en el encabezado del menú, el logo "uSipipo VPN" tiene el efecto glitch definido en `cyberpunk.css`: duplicaciones de texto en cyan y magenta que se desfasan ligeramente. En Kivy esto se implementa con `Animation` sobre las propiedades `pos_hint` de labels duplicados.

### Botón de Poder (Referencia imágenes)
Para versión futura donde se implemente conexión directa desde la APK, el botón circular central de la imagen de referencia se implementará como:
- Círculo con gradiente radial de cyan a transparente
- Pulsación suave (scale 1.0 → 1.05 → 1.0) cuando está conectado
- Cuando está desconectado: glow rojo pulsante

---

## Layout y Espaciado

Siguiendo Material Design 3 (que usa KivyMD por defecto):

| Elemento | Valor |
|---|---|
| Margen horizontal de pantalla | 16dp |
| Espacio entre cards | 12dp |
| Padding interno de cards | 16dp |
| Altura de TopBar | 56dp |
| Altura de BottomNavigation | 80dp |
| Altura de botones primarios | 48dp |
| Radio de esquinas de cards | 12dp |
| Radio de esquinas de botones | 8dp |
| Tamaño mínimo de área tocable | 48x48dp |

---

## Ícono de la APK

El ícono de la APK (launcher icon) mantiene el mismo diseño que el `favicon.svg` del mini app web: el isotipo/logo de uSipipo con el esquema de colores neon sobre fondo oscuro. Se genera en los siguientes tamaños requeridos por Android:

- 48x48 (mdpi)
- 72x72 (hdpi)
- 96x96 (xhdpi)
- 144x144 (xxhdpi)
- 192x192 (xxxhdpi)
- 512x512 (Google Play Store)
