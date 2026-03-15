# 🚀 INICIO RÁPIDO - Implementación APK uSipipo

> **Guardar este archivo como referencia rápida entre sesiones**

---

## 📋 En una Nueva Sesión de Claude Code

### Paso 1: Verificar Progreso Actual

```bash
# Ir a la carpeta de planes
cd /home/mowgli/usipipobot/docs/plans/apk/IMPLEMENTACION

# Verificar último estado
cat PROGRESO.md
```

### Paso 2: Identificar Próxima Fase

Buscar en `PROGRESO.md` la primera fase con estado `⏳ Pendiente`.

**Ejemplo:** Si la fase `01.2` está pendiente, el próximo archivo es:
```
FASE_01_AUTENTICACION/01.2_backend_otp_verify.md
```

### Paso 3: Invocar Skill de Ejecución

```
# Invocar la skill "executing-plans" o "writing-plans"

El agente leerá automáticamente el plan de la fase actual
y ejecutará exactamente lo especificado.
```

---

## 🎯 Próxima Fase a Implementar

**FASE ACTUAL:** [COMPLETAR EN CADA SESIÓN]

**Archivo del Plan:**
```bash
cat /home/mowgli/usipipobot/docs/plans/apk/IMPLEMENTACION/FASE_XX/XX.X_description.md
```

**Tareas Máximas:** 5 (por diseño para evitar errores)

**Duración Estimada:** 1-3 horas

---

## ✅ Checklist de Verificación Rápida

### Antes de Comenzar
- [ ] Fase anterior está 100% completada
- [ ] Todos los tests de la fase anterior pasan
- [ ] No hay errores en logs del backend
- [ ] `PROGRESO.md` está actualizado

### Al Completar
- [ ] Todos los comandos de verificación se ejecutaron
- [ ] Todos los criterios de aceptación están marcados
- [ ] `PROGRESO.md` actualizado
- [ ] Cambios commiteados en Git

---

## 📂 Estructura de Planes

```
IMPLEMENTACION/
├── FASE_01_AUTENTICACION/
│   ├── 01.1_backend_otp_request.md    ← Request OTP
│   ├── 01.2_backend_otp_verify.md     ← Verify OTP + JWT
│   ├── 01.3_backend_jwt_auth.md       ← Auth deps + refresh + logout
│   ├── 01.4_apk_login_screen.md       ← APK login UI
│   ├── 01.5_apk_otp_screen.md         ← APK OTP UI
│   └── 01.6_testing_flujo_completo.md ← E2E testing
│
├── FASE_02_DASHBOARD/
│   ├── 02.1_backend_dashboard_endpoint.md
│   ├── 02.2_apk_dashboard_layout.md
│   ├── 02.3_apk_dashboard_cards.md
│   └── 02.4_dashboard_cache.md
│
└── ... (más fases)
```

---

## 🚨 Rollback Rápido

Si algo sale mal:

```bash
# 1. Detener backend
sudo systemctl stop usipipo-backend

# 2. Revertir última fase
git checkout HEAD~1 -- infrastructure/api/android/

# 3. Reiniciar backend
sudo systemctl start usipipo-backend

# 4. Verificar
curl http://localhost:8000/health
```

---

## 📞 Comandos de Emergencia

### Backend no responde
```bash
sudo systemctl restart usipipo-backend
sudo journalctl -u usipipo-backend -n 100
```

### Redis caído
```bash
sudo systemctl status redis
sudo systemctl restart redis
redis-cli ping
```

### PostgreSQL caído
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
sudo -u postgres psql -c "SELECT 1"
```

---

## 📝 Notas de la Sesión Anterior

[ESPACIO PARA NOTAS]

```
Fecha: ___________
Fase completada: ___________
Issues encontrados: ___________
Próxima fase: ___________
```

---

*Última actualización: [FECHA]*
