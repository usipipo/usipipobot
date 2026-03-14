# 📚 Guía Completa de Implementación por Fases

> **Para:** Equipo de Desarrollo uSipipo
> 
> **Propósito:** Cómo implementar la APK Android sin errores, fase por fase

---

## 🎯 Filosofía de Implementación

### ¿Por qué fases pequeñas?

Cada archivo de plan tiene **máximo 5 tareas** porque:

1. **Evita errores por sobrecarga cognitiva** - El agente puede enfocarse en pocas cosas a la vez
2. **Facilita testing incremental** - Testear después de cada fase pequeña
3. **Permite rollback rápido** - Si algo falla, solo se revierte una fase pequeña
4. **Mantiene sesiones cortas** - Cada fase toma 1-3 horas máximo
5. **Reduce integración conflictiva** - Menos cambios simultáneos = menos conflictos

---

## 📋 Flujo de Trabajo Entre Sesiones

### Sesión 1: Comienzo

```bash
# 1. Leer guía de inicio rápido
cat docs/plans/apk/IMPLEMENTACION/INICIO_RAPIDO.md

# 2. Verificar prerrequisitos
bash scripts/verify_prerequisites.sh  # (si existe)

# 3. Comenzar Fase 01.1
cat docs/plans/apk/IMPLEMENTACION/FASE_01_AUTENTICACION/01.1_backend_otp_request.md

# 4. Invocar skill de ejecución de planes
# (El agente lee el plan y ejecuta las 5 tareas)

# 5. Verificar con comandos del plan
# (Cada plan tiene sus comandos de verificación)

# 6. Si todo pasa, actualizar PROGRESO.md
# Marcar fase 01.1 como ✅ Completada

# 7. Hacer commit
git add .
git commit -m "feat: FASE 01.1 completada - Backend Request OTP"
git push
```

### Sesión 2: Continuación

```bash
# 1. Leer PROGRESO.md para ver dónde quedaste
cat docs/plans/apk/IMPLEMENTACION/PROGRESO.md

# 2. Verificar que fase 01.1 está completada

# 3. Comenzar Fase 01.2
cat docs/plans/apk/IMPLEMENTACION/FASE_01_AUTENTICACION/01.2_backend_otp_verify.md

# 4. Invocar skill de ejecución

# 5. Verificar, actualizar PROGRESO.md, hacer commit
```

### Sesión N: Cualquier Fase Posterior

```bash
# Mismo flujo:
# 1. Leer PROGRESO.md
# 2. Identificar próxima fase pendiente
# 3. Leer plan de esa fase
# 4. Ejecutar skill
# 5. Verificar y commitear
```

---

## 🗂️ Estructura de Archivos de Plan

Cada archivo de fase contiene:

```markdown
# FASE XX.Y - Título Descriptivo

> **Documento Base:** documentos originales (03_MODULO_AUTH.md, etc.)
> 
> **Duración Estimada:** 1-3 horas
> 
> **Prioridad:** ALTA/MEDIA/BAJA
> 
> **Prerrequisito:** Fases que deben estar completas antes

## 📋 Contexto
[Explicación de qué se está implementando y por qué]

## 🎯 Tareas (Máximo 5)

### Tarea 1: [Descripción específica]
**Archivos a crear/modificar:**
- ruta/al/archivo.py

**Contenido específico:**
```python
# Código exacto o instrucciones
```

**Verificación:**
```bash
# Comandos exactos para verificar
```

### Tarea 2: [Descripción específica]
...

(Repetir hasta máximo 5 tareas)

## ✅ Criterios de Aceptación
- [ ] Criterio 1
- [ ] Criterio 2
- [ ] Criterio 3
- [ ] Criterio 4
- [ ] Criterio 5

## 🔄 Rollback (si algo falla)
```bash
# Comandos exactos para revertir
```

## 📝 Notas para la Siguiente Fase
[Qué está listo y qué falta para la próxima fase]
```

---

## 📊 Orden de Implementación Recomendado

### Prioridad 1: Autenticación (Fase 01)
```
01.1 → 01.2 → 01.3 → 01.4 → 01.5 → 01.6
```
**Por qué:** Sin autenticación, nada más funciona.

### Prioridad 2: Dashboard (Fase 02)
```
02.1 → 02.2 → 02.3 → 02.4
```
**Por qué:** Es la pantalla principal que los usuarios ven post-login.

### Prioridad 3: Claves VPN (Fase 03-04)
```
03.1 → 03.2 → 03.3 → 03.4  (Listado)
04.1 → 04.2 → 04.3 → 04.4 → 04.5  (Creación)
```
**Por qué:** Es la funcionalidad core del producto.

### Prioridad 4: Compras (Fase 05-07)
```
05.1 → 05.2 → 05.3  (Catálogo)
06.1 → 06.2 → 06.3 → 06.4  (Stars)
07.1 → 07.2 → 07.3 → 07.4  (USDT)
```
**Por qué:** Es cómo se monetiza el producto.

### Prioridad 5: Perfil y Tickets (Fase 08-09)
```
08.1 → 08.2 → 08.3 → 08.4  (Perfil)
09.1 → 09.2 → 09.3 → 09.4  (Tickets)
```
**Por qué:** Funcionalidad de soporte y configuración.

### Prioridad 6: Notificaciones y UI (Fase 10-11)
```
10.1 → 10.2 → 10.3  (Notificaciones)
11.1 → 11.2 → 11.3  (Diseño visual)
```
**Por qué:** Pulido final de la UX.

### Prioridad 7: Build y Deploy (Fase 12)
```
12.1 → 12.2 → 12.3 → 12.4
```
**Por qué:** Para distribuir la APK a testers.

### Prioridad 8: Infraestructura (Fase 13)
```
13.1 → 13.2 → 13.3 → 13.4 → 13.5 → 13.6 → 13.7 → 13.8
```
**Por qué:** Optimizaciones que pueden hacerse en paralelo.

---

## ⚠️ Reglas de Oro

### 1. NO Saltar Fases
Cada fase depende de la anterior. Si saltas una, algo va a fallar.

### 2. NO Modificar Más de 5 Archivos por Fase
Si el plan pide modificar más de 5 archivos, está mal diseñado.

### 3. NO Continuar si una Fase Falla
Si una fase no pasa todos los criterios de aceptación:
- NO continuar a la siguiente fase
- SÍ hacer rollback
- SÍ debuggear hasta que pase
- SÍ reintentar la fase

### 4. SIEMPRE Verificar con Comandos del Plan
No asumir que funciona. Ejecutar TODOS los comandos de verificación.

### 5. SIEMPRE Actualizar PROGRESO.md
Si no está en PROGRESO.md, no está completado.

---

## 🐛 Manejo de Errores

### Error en Tarea Individual

Si una tarea dentro de una fase falla:

1. **No continuar** con las tareas restantes de esa fase
2. **Debuggear** esa tarea específica
3. **Si se resuelve:** Continuar con tarea siguiente
4. **Si no se resuelve en 30 min:** Hacer rollback de toda la fase

### Error en Fase Completa

Si una fase completa no pasa los criterios de aceptación:

1. **No continuar** a la siguiente fase
2. **Revertir** usando el rollback del plan
3. **Documentar** el error en PROGRESO.md (tabla de Issues)
4. **Esperar** revisión humana

### Error en Integración

Si después de completar una fase, algo deja de funcionar:

1. **Verificar logs:** `sudo journalctl -u usipipo-backend -f`
2. **Verificar Redis:** `redis-cli KEYS "*"`
3. **Verificar DB:** `sudo -u postgres psql usipipodb -c "SELECT 1"`
4. **Si no se encuentra:** Revertir última fase

---

## 📝 Ejemplo de Sesión Exitosa

### Inicio de Sesión

```
Usuario: Voy a implementar la fase 01.1

Agente: Perfecto. Verifiquemos que estás en el directorio correcto.

Usuario: cd /home/mowgli/usipipobot/docs/plans/apk/IMPLEMENTACION

Agente: Ahora leamos el plan de la fase 01.1

Usuario: cat FASE_01_AUTENTICACION/01.1_backend_otp_request.md

Agente: Entendido. Comencemos con la Tarea 1: Crear estructura de carpetas...
```

### Durante la Sesión

```
Agente: Tarea 1 completada. Ejecutemos la verificación:

Usuario: ls -la infrastructure/api/android/

Agente: ✅ Verificado. Continuemos con la Tarea 2...

(Repetir para cada tarea)
```

### Fin de Sesión

```
Agente: Todas las tareas completadas. Ejecutemos los criterios de aceptación:

Usuario: [Marca todos los criterios en PROGRESO.md]

Agente: ✅ Fase 01.1 completada. Hagamos commit:

Usuario: git add . && git commit -m "feat: FASE 01.1 completada" && git push

Agente: ✅ Push exitoso. Próxima fase: 01.2_backend_otp_verify.md
```

---

## 🎯 Métricas de Progreso

### Por Sesión
- **Fases completadas:** 1-2 (ideal)
- **Tareas completadas:** 3-5 (por fase)
- **Errores encontrados:** 0-2 (normal)
- **Tiempo total:** 2-4 horas (ideal)

### Por Semana
- **Fases completadas:** 5-10 (buen ritmo)
- **Issues críticos:** 0-1 (manejable)
- **Horas totales:** 10-20 (sostenible)

### Por Mes
- **Fases completadas:** 20-30 (proyecto completo)
- **APK funcional:** Sí (alpha listo)
- **Issues abiertos:** 0-2 (cierre próximo)

---

## 📞 Soporte

### Si un Plan no Está Claro

1. Re-leer el contexto de la fase
2. Revisar los documentos base (03_MODULO_AUTH.md, etc.)
3. Si aún hay duda: **NO implementar**, preguntar primero

### Si un Comando de Verificación Falla

1. Copiar el error exacto
2. Revisar si es error de sintaxis (Python) o de lógica
3. Si es de sintaxis: revisar el archivo creado
4. Si es de lógica: revisar dependencias de fases anteriores

### Si los Criterios de Aceptación No Se Cumplen

1. Identificar cuál criterio falla
2. Revisar la tarea que debería haberlo cumplido
3. Re-ejecutar esa tarea
4. Si persiste: rollback de fase

---

## ✅ Checklist Final Antes de Producción

Cuando todas las fases estén completas:

- [ ] Todas las fases en PROGRESO.md están ✅
- [ ] No hay issues abiertos en la tabla de Issues
- [ ] Todos los tests manuales pasan
- [ ] Los logs del backend no tienen errores
- [ ] Redis está limpio (sin keys huérfanas)
- [ ] La DB tiene todos los índices
- [ ] El backup está configurado
- [ ] El monitoreo está activo
- [ ] La APK compila sin errores
- [ ] La APK funciona en dispositivo físico

---

*Documento versión 1.0 - Fecha: Marzo 2026*
*Guardar como referencia en cada sesión de implementación*
