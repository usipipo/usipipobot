# Widget de Latencia en Dashboard — Mini App Web

**Fecha:** 2026-03-18
**Estado:** COMPLETO
**Autor:** uSipipo Team
**Versión:** 1.0

---

## Historial de Implementación

| Fecha | Track | Estado | Commit |
|-------|-------|--------|--------|
| 2026-03-18 | Track 1: Estilos CSS | ✅ COMPLETO | 89664ab |
| 2026-03-18 | Track 2: HTML Dashboard | ✅ COMPLETO | ff73f14 |
| 2026-03-18 | Track 3: JavaScript Widget | ✅ COMPLETO | ff73f14 |
| 2026-03-18 | Track 4: Testing y Ajustes | ✅ COMPLETO | ff73f14 |

---

## 1. Resumen Ejecutivo

Implementar un widget de latencia en el Dashboard de la Mini App Web que muestre la latencia actual del servidor (en ms) con un gráfico sparkline SVG del histórico de los últimos 10 puntos. El widget se actualiza automáticamente cada 60 segundos y proporciona transparencia sobre el estado del servidor para todos los usuarios.

---

## 2. DAFO Técnico

### 💪 Fortalezas
- **F1**: API backend ya implementada (`GET /api/v1/miniapp/latency`)
- **F2**: Estilo cyberpunk existente facilita integración visual coherente
- **F3**: Sin dependencias externas de gráficos (SVG inline liviano)
- **F4**: Template `dashboard.html` ya tiene estructura de tarjetas reusable

### ⚠️ Debilidades / Deuda técnica relevante
- **D1**: Sin librería de gráficos → hay que implementar SVG sparkline manual
- **D2**: Polling cada 60s podría consumir batería/data en móviles
- **D3**: JavaScript vanilla sin framework → más código boilerplate

### 🚀 Oportunidades
- **O1**: Diferenciador de transparencia vs competidores VPN
- **O2**: Reduce tickets de soporte "el servidor está lento"
- **O3**: Base para futuros widgets de métricas (CPU, RAM, etc.)

### 🔴 Riesgos técnicos
- **R1**: Timeout en conexiones lentas → **Mitigación**: Fallback graceful con mensaje de error
- **R2**: SVG no responsive en pantallas chicas → **Mitigación**: viewBox + preserveAspectRatio
- **R3**: Memory leak por setInterval → **Mitigación**: clearInterval en pagehide/unload

---

## 3. Arquitectura

### Visión general

El widget se integra como una tarjeta más en el Dashboard existente. Utiliza JavaScript vanilla para hacer polling a la API cada 60 segundos, renderiza un gráfico SVG sparkline inline y aplica colores dinámicos según el quality_score retornado por la API.

### Diagrama de componentes (texto)

```
┌─────────────────────────────────────────────────────────┐
│  Dashboard (dashboard.html)                              │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Widget Latencia (nueva tarjeta .card)          │     │
│  │                                                  │     │
│  │  ┌──────────────────────────────────────────┐   │     │
│  │  │  Header: "📡 Latencia del Servidor"       │   │     │
│  │  │  + Badge de estado (🟢 Excelente)         │   │     │
│  │  └──────────────────────────────────────────┘   │     │
│  │                                                  │     │
│  │  ┌──────────────────────────────────────────┐   │     │
│  │  │  Valor actual: "23 ms" (color dinámico)   │   │     │
│  │  └──────────────────────────────────────────┘   │     │
│  │                                                  │     │
│  │  ┌──────────────────────────────────────────┐   │     │
│  │  │  SVG Sparkline (histórico 10 puntos)      │   │     │
│  │  └──────────────────────────────────────────┘   │     │
│  │                                                  │     │
│  │  ┌──────────────────────────────────────────┐   │     │
│  │  │  Loading: "⏳ Recopilando datos..."       │   │     │
│  │  │  Error: "❌ Sin conexión"                 │   │     │
│  │  └──────────────────────────────────────────┘   │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  app.js (MiniApp.latency)     │
            │  - fetchLatency()             │
            │  - renderSparkline()          │
            │  - updateWidget()             │
            │  - setInterval (60s)          │
            └───────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │  API Backend                  │
            │  GET /api/v1/miniapp/latency  │
            │  Returns: {                   │
            │    current: { ping_ms, ... }, │
            │    history: [...],            │
            │    quality_score,             │
            │    status_icon,               │
            │    status_label               │
            │  }                            │
            └───────────────────────────────┘
```

### Stack técnico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| Frontend HTML | Jinja2 template | Consistente con el resto de la Mini App |
| Frontend CSS | Cyberpunk theme existente | Variables CSS ya definidas (--neon-cyan, --neon-magenta, --amber) |
| Frontend JS | Vanilla JavaScript | Sin dependencias externas, consistente con app.js |
| Gráfico | SVG inline | Liviano, responsive, sin librerías |
| API | FastAPI backend | Ya implementada en Track 3 del backend |
| Polling | setInterval (60s) | Simple, efectivo, bajo consumo |

### Estructura de directorios

```
usipipobot/
├── miniapp/
│   ├── templates/
│   │   └── dashboard.html          # MODIFICAR: Agregar widget
│   └── static/
│       ├── css/
│       │   └── cyberpunk.css       # MODIFICAR: Estilos del widget
│       └── js/
│           └── app.js              # MODIFICAR: Lógica del widget
├── infrastructure/
│   └── api/routes/
│       └── miniapp_latency.py      # YA EXISTE: API endpoint
└── docs/plans/
    └── 2026-03-18_plan-4-widget-latencia-dashboard.md
```

### Modelos de datos (API Response)

```typescript
// GET /api/v1/miniapp/latency response
interface LatencyResponse {
  status: "ok" | "error";
  current: {
    timestamp: string;        // ISO 8601
    ping_ms: number;          // RTT en ms
    cpu_percent: number;      // 0-100 (no usamos en widget)
    ram_percent: number;      // 0-100 (no usamos en widget)
    // ... otros campos no usados
  };
  quality_score: number;      // 0-100
  status_icon: string;        // "🟢" | "🟡" | "🔴"
  status_label: string;       // "Excelente" | "Normal" | "Alta carga"
  history: Array<{
    timestamp: string;
    ping_ms: number;
  }>;
}
```

---

## 4. Tracks de Implementación

### Track 1: Estilos CSS del Widget — Complejidad: Baja

**Objetivo:** Agregar los estilos CSS para el widget de latencia en `cyberpunk.css` y `base.html`.

**Entregable verificable:**
- Clases CSS creadas: `.latency-widget`, `.latency-header`, `.latency-value`, `.latency-sparkline`
- Colores dinámicos: `.latency-excellent` (cyan), `.latency-normal` (magenta), `.latency-poor` (amber)
- Loading y error states: `.latency-loading`, `.latency-error`

**Archivos que modifica:**
- `miniapp/static/css/cyberpunk.css` (agregar ~80 líneas de CSS)
- `miniapp/templates/base.html` (opcional: si hay estilos inline necesarios)

**Dependencias:** Ninguna

**Estimación:** 30-45 minutos

---

### Track 2: HTML del Widget en Dashboard — Complejidad: Baja

**Objetivo:** Agregar el markup HTML del widget en `dashboard.html`.

**Entregable verificable:**
- Nueva tarjeta `.card` insertada debajo del grid de métricas
- Estructura HTML completa con:
  - Header con título y badge de estado
  - Valor de latencia grande
  - Contenedor SVG para el sparkline
  - Estados de loading y error (ocultos por defecto)

**Archivos que modifica:**
- `miniapp/templates/dashboard.html` (agregar ~40 líneas de HTML)

**Dependencias:** Track 1 (estilos CSS)

**Estimación:** 20-30 minutos

---

### Track 3: JavaScript del Widget — Complejidad: Media

**Objetivo:** Implementar la lógica JavaScript para fetch, renderizado y auto-refresh.

**Entregable verificable:**
- Función `fetchLatency()`: Fetch a `/api/v1/miniapp/latency` con manejo de errores
- Función `renderSparkline(history)`: Genera SVG path dinámico con los últimos 10 puntos
- Función `updateWidget(data)`: Actualiza DOM con valores y aplica colores dinámicos
- Función `startLatencyPolling()`: setInterval cada 60s con cleanup
- Loading state inicial: "⏳ Recopilando datos..."
- Error state: "❌ Sin conexión" con reintento automático

**Archivos que modifica:**
- `miniapp/static/js/app.js` (agregar ~150 líneas de JS)

**Dependencias:** Track 1 (CSS), Track 2 (HTML)

**Estimación:** 1.5-2 horas

---

### Track 4: Testing Manual y Ajustes — Complejidad: Baja

**Objetivo:** Probar el widget en diferentes escenarios y ajustar detalles.

**Entregable verificable:**
- ✅ Widget carga correctamente al abrir Dashboard
- ✅ Loading state se muestra por ~500ms-1s
- ✅ Gráfico sparkline se renderiza correctamente
- ✅ Colores dinámicos cambian según quality_score
- ✅ Auto-refresh funciona cada 60s
- ✅ Error state se muestra si la API falla
- ✅ Reintento automático funciona
- ✅ Responsive en pantallas chicas (<360px)
- ✅ Haptic feedback al actualizar

**Archivos que modifica:**
- Ninguno (solo ajustes si se encuentran bugs)

**Dependencias:** Track 1, Track 2, Track 3

**Estimación:** 45-60 minutos

---

## 5. Estimación Total

| Track | Complejidad | Estimación |
|-------|------------|------------|
| Track 1: Estilos CSS | Baja | 30-45 min |
| Track 2: HTML Dashboard | Baja | 20-30 min |
| Track 3: JavaScript Widget | Media | 1.5-2 horas |
| Track 4: Testing y Ajustes | Baja | 45-60 min |
| **TOTAL** | | **3.5 - 4.5 horas** |

**Margen de incertidumbre:** ±20% — Depende de la complejidad del SVG sparkline y ajustes de responsive.

---

## 6. Dependencias Externas

| Servicio / Lib | Para qué | Credencial necesaria |
|---------------|----------|---------------------|
| API Backend `/api/v1/miniapp/latency` | Obtener métricas de latencia | Ninguna (usa Telegram initData) |
| Telegram WebApp SDK | Haptic feedback | Incluido en base.html |

---

## 7. Decisiones de Diseño

### Decisión 1: Ubicación del Widget
**Opción elegida:** Tarjeta nueva debajo del grid de métricas
**Alternativas consideradas:**
- 4ta columna en el grid (descartado: rompe responsive en pantallas chicas)
- Inline dentro del grid (descartado: muy chico)
**Razón:** Mantiene consistencia visual, espacio adecuado para el gráfico, fácil de scrollear.

### Decisión 2: Colores del Estado
**Opción elegida:** Cian (excelente), Magenta (normal), Ámbar (alta)
**Alternativas consideradas:**
- Verde/Amarillo/Rojo (descartado: no coincide con estilo cyberpunk)
- Solo íconos sin color (descartado: menos impacto visual)
**Razón:** Coherente con el tema cyberpunk existente (--neon-cyan, --neon-magenta, --amber).

### Decisión 3: Gráfico SVG Sparkline
**Opción elegida:** SVG inline generado dinámicamente con JavaScript
**Alternativas consideradas:**
- Librería Chart.js (descartado: muy pesada, 60KB+)
- Canvas API (descartado: menos nítido en móviles)
- Sin gráfico (descartado: pierde valor del histórico)
**Razón:** Liviano (<1KB), responsive, sin dependencias, consistente con vanilla JS.

### Decisión 4: Polling vs WebSocket
**Opción elegida:** Polling con setInterval cada 60s
**Alternativas consideradas:**
- WebSocket en tiempo real (descartado: overkill, más complejidad)
- Pull manual con botón (descartado: menos usable)
**Razón:** Balance perfecto entre frescura de datos y consumo de recursos.

### Decisión 5: Loading State Inicial
**Opción elegida:** Mostrar "⏳ Recopilando datos..." mientras carga la primera vez
**Alternativas consideradas:**
- Spinner animado (descartado: muy genérico)
- Skeleton loader (descartado: más complejo de implementar)
- Sin loading (descartado: confunde al usuario)
**Razón:** Claro, consistente con el estilo terminal del proyecto, fácil de implementar.

---

## 8. Plan de Testing

| Track | Tipo de test | Qué verifica |
|-------|-------------|-------------|
| Track 1 | Visual | Estilos CSS aplican correctamente, colores dinámicos |
| Track 2 | Visual | HTML estructura correcta, responsive |
| Track 3 | Funcional | Fetch API funciona, renderizado SVG, polling |
| Track 4 | Manual E2E | Widget completo en Dashboard, todos los estados |

**Criterios de aceptación:**
1. Widget visible en Dashboard al cargar
2. Loading state se muestra <2 segundos
3. Latencia actual coincide con API
4. Gráfico sparkline muestra 10 puntos históricos
5. Color cambia según quality_score (🟢 <75, 🟡 50-74, 🔴 <50)
6. Auto-refresh cada 60s sin intervención del usuario
7. Error state se muestra si API falla (timeout 5s)
8. Reintento automático después de error (próximo ciclo)

---

## 9. Checklist de Aprobación

Antes de pasar a implementación, confirmar:

- [x] Arquitectura revisada y aprobada
- [x] Tracks ordenados correctamente (sin dependencias circulares)
- [x] Stack técnico acordado (vanilla JS + SVG inline)
- [x] API backend ya disponible (`/api/v1/miniapp/latency`)
- [x] Estimación aceptada (3.5-4.5 horas)
- [x] Decisiones de diseño confirmadas (ubicación, colores, sparkline)
- [x] Loading state definido ("⏳ Recopilando datos...")

---

## 10. Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-03-18 | 1.0 | Documento inicial |

---

## Mockup Visual (ASCII)

```
┌─────────────────────────────────────────────────┐
│  📡 Latencia del Servidor          🟢 Excelente │
├─────────────────────────────────────────────────┤
│                                                 │
│          23 ms                                  │
│          ━━━━━                                  │
│                                                 │
│    ┌──────────────────────────────────────┐     │
│    │  ⚡━━━╮                                │     │
│    │      ╰━━━╮                            │     │
│    │          ╰━━━╮    ╭━━━                │     │
│    │              ╰━━━━╯                   │     │
│    └──────────────────────────────────────┘     │
│                                                 │
│  Actualizado: hace 12s                          │
└─────────────────────────────────────────────────┘

Loading state:
┌─────────────────────────────────────────────────┐
│  📡 Latencia del Servidor                       │
├─────────────────────────────────────────────────┤
│                                                 │
│     ⏳ Recopilando datos...                     │
│                                                 │
└─────────────────────────────────────────────────┘

Error state:
┌─────────────────────────────────────────────────┐
│  📡 Latencia del Servidor                       │
├─────────────────────────────────────────────────┤
│                                                 │
│     ❌ Sin conexión                             │
│     🔄 Reintentando en 30s...                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Especificación Técnica Detallada

### SVG Sparkline

```javascript
// Dimensiones
const width = 280;  // 100% del contenedor
const height = 60;
const padding = 4;

// Normalización de datos
const pingValues = history.map(h => h.ping_ms);
const minPing = Math.min(...pingValues);
const maxPing = Math.max(...pingValues);
const range = maxPing - minPing || 1;

// Generar path
const points = pingValues.map((ping, i) => {
  const x = (i / (pingValues.length - 1)) * (width - padding * 2) + padding;
  const y = height - padding - ((ping - minPing) / range) * (height - padding * 2);
  return `${x},${y}`;
});

const pathD = `M ${points.join(' L ')}`;

// Color según quality_score
const strokeColor = qualityScore >= 75 ? 'var(--neon-cyan)'
  : qualityScore >= 50 ? 'var(--neon-magenta)'
  : 'var(--amber)';
```

### Colores Dinámicos

```javascript
function getStatusClass(qualityScore) {
  if (qualityScore >= 75) return 'latency-excellent';  // cyan
  if (qualityScore >= 50) return 'latency-normal';     // magenta
  return 'latency-poor';                               // amber
}
```

### Polling con Cleanup

```javascript
let latencyPollInterval = null;

function startLatencyPolling() {
  // Fetch inmediato
  fetchLatency();

  // Poll cada 60s
  latencyPollInterval = setInterval(fetchLatency, 60000);

  // Cleanup en pagehide
  window.addEventListener('pagehide', () => {
    if (latencyPollInterval) {
      clearInterval(latencyPollInterval);
    }
  });
}
```

---

**Fin del documento de diseño**
