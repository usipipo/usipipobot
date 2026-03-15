# GitHub Actions - Configuración Completada ✅

## 📊 Resumen de Configuración

### ✅ Secrets Configurados (vía gh cli)

| Secret | Estado | Fecha |
|--------|--------|-------|
| `ANDROID_KEYSTORE_B64` | ✅ Configurado | 2026-03-14 |
| `ANDROID_KEYSTORE_PASSWORD` | ✅ Configurado | 2026-03-14 |
| `ANDROID_KEY_ALIAS` | ✅ Configurado | 2026-03-14 |
| `ANDROID_KEY_PASSWORD` | ✅ Configurado | 2026-03-14 |
| `QWEN_API_KEY` | ✅ Configurado | 2026-03-15 |
| `TELEGRAM_BOT_TOKEN` | ✅ Configurado | 2026-03-15 |

---

### ⚠️ Variables (Requieren configuración manual)

**Nota:** Las variables no se pudieron configurar automáticamente porque la API de GitHub requiere permisos adicionales. Debes configurarlas manualmente:

#### Variables del Repositorio

Ve a: **GitHub → usipipo/usipipobot → Settings → Secrets and variables → Actions → Variables**

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | Endpoint de Qwen API |
| `QWEN_MODEL` | `qwen-max` | Modelo de Qwen |
| `QWEN_CLI_VERSION` | `latest` | Versión del CLI |
| `UPLOAD_ARTIFACTS` | `true` | Subir artifacts de Qwen |
| `DEBUG` | `false` | Modo debug |

#### Variables de Environment (production)

Ve a: **GitHub → usipipo/usipipobot → Settings → Environments → production → Variables**

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `APP_URL` | `https://usipipo.com` | URL de producción |

---

### ⚠️ Environments (Requieren admin)

**Nota:** No se pudieron crear los environments porque requieres permisos de admin.

#### Environments a crear manualmente:

Ve a: **GitHub → usipipo/usipipobot → Settings → Environments → New environment**

1. **staging**
   - URL: `https://staging.usipipo.com`
   - Deployment branches: All branches

2. **release**
   - URL: (dejar vacío o URL de releases)
   - Deployment branches: `main` only

---

## 🔧 Instrucciones Manuales Paso a Paso

### 1. Configurar Variables del Repositorio

1. Ve a `https://github.com/usipipo/usipipobot/settings/actions/variables`
2. Haz clic en **"New repository variable"**
3. Agrega cada variable:

```
Name: QWEN_BASE_URL
Value: https://dashscope.aliyuncs.com/compatible-mode/v1
```

```
Name: QWEN_MODEL
Value: qwen-max
```

```
Name: QWEN_CLI_VERSION
Value: latest
```

```
Name: UPLOAD_ARTIFACTS
Value: true
```

```
Name: DEBUG
Value: false
```

### 2. Configurar Variables de Telegram (opcional)

Si quieres notificaciones de releases en Telegram:

1. Necesitas obtener el **Chat ID** de tu canal/grupo
2. Agrega la variable:

```
Name: TELEGRAM_CHAT_ID
Value: -1001234567890  (reemplaza con tu chat ID real)
```

**¿Cómo obtener el Chat ID?**
- Agrega tu bot a un grupo/canal
- Envía un mensaje al grupo
- Usa: `curl https://api.telegram.org/bot5289896929:AAHbbT83MnRjVtQwft6T2PFdCLf6uv_3ngM/getUpdates`
- Busca `"chat":{"id":...}` en la respuesta

### 3. Crear Environments

1. Ve a `https://github.com/usipipo/usipipobot/settings/environments`
2. Haz clic en **"New environment"**
3. Crea **staging**:
   - Name: `staging`
   - Deployment branches: All branches
   - Environment URL: `https://staging.usipipo.com`

4. Crea **release**:
   - Name: `release`
   - Deployment branches: Only `main` branch

### 4. Configurar Variables por Environment

**Para production:**
1. Ve a `production` environment
2. Agrega variable: `APP_URL` = `https://usipipo.com`

**Para staging:**
1. Ve a `staging` environment
2. Agrega variable: `APP_URL` = `https://staging.usipipo.com`

---

## 📋 Workflows Disponibles

### Workflows de CI/CD (sin configuración adicional)

| Workflow | Estado | Notas |
|----------|--------|-------|
| `ci.yml` | ✅ Listo | Sin configuración necesaria |
| `docker.yml` | ✅ Listo | Sin configuración necesaria |
| `codeql.yml` | ✅ Listo | Sin configuración necesaria |
| `android-ci.yml` | ✅ Listo | Secrets ya configurados |
| `performance.yml` | ✅ Listo | Sin configuración necesaria |

### Workflows con configuración completada

| Workflow | Estado | Secrets | Variables |
|----------|--------|---------|-----------|
| `release.yml` | ⚠️ Parcial | ✅ TELEGRAM_BOT_TOKEN | ⚠️ TELEGRAM_CHAT_ID (manual) |
| `manual-deploy.yml` | ⚠️ Parcial | ⚠️ DEPLOY_* (si usas deploy) | ⚠️ APP_URL (manual) |

### Workflows de Qwen Code

| Workflow | Estado | Secrets | Variables |
|----------|--------|---------|-----------|
| `qwen-dispatch.yml` | ⚠️ Parcial | ✅ QWEN_API_KEY | ⚠️ QWEN_* vars (manual) |
| `qwen-invoke.yml` | ⚠️ Parcial | ✅ QWEN_API_KEY | ⚠️ QWEN_* vars (manual) |
| `qwen-review.yml` | ⚠️ Parcial | ✅ QWEN_API_KEY | ⚠️ QWEN_* vars (manual) |
| `qwen-triage.yml` | ⚠️ Parcial | ✅ QWEN_API_KEY | ⚠️ QWEN_* vars (manual) |
| `qwen-scheduled-triage.yml` | ⚠️ Parcial | ✅ QWEN_API_KEY | ⚠️ QWEN_* vars (manual) |

---

## ✅ Verificación Final

Después de configurar las variables manualmente, verifica:

```bash
# Ver secrets
gh secret list

# Ver environments
gh api /repos/usipipo/usipipobot/environments | jq '.environments[].name'

# Ver variables (si tienes permisos)
gh api /repos/usipipo/usipipobot/actions/variables | jq '.variables[].name'
```

---

## 🚀 Próximos Pasos

1. **Configurar variables manualmente** (ver instrucciones arriba)
2. **Solicitar permisos de admin** si necesitas crear environments
3. **Probar workflows**:
   ```bash
   # Trigger CI workflow
   gh workflow run ci.yml
   
   # View workflow runs
   gh run list
   ```

---

## 📝 Notas Importantes

1. **Qwen API Key**: Se configuró con tu token OAuth de `~/.qwen/oauth_creds.json`
2. **Telegram Bot Token**: Se configuró con el token proporcionado
3. **Android Secrets**: Ya estaban configurados desde antes
4. **Variables**: Requieren configuración manual vía GitHub UI
5. **Environments**: Requieren permisos de admin para crear

---

*Configuración realizada: 2026-03-15*
*Usuario: mowgliph (Jelvys Triana)*
*Repositorio: usipipo/usipipobot*
