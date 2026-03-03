# Tarea: Auditoría y refactorización de archivos Python por límite de líneas

## Contexto
Sigue estrictamente las reglas definidas en el archivo `CLAUDE.md` de este
monorepo sobre límites de líneas por archivo Python antes de comenzar.

---

## Flujo de trabajo completo (ejecuta cada fase en orden)

### FASE 1 — Auditoría del código

1. Escanea **recursivamente** todos los archivos `.py` del monorepo,
   excluyendo:
   - `**/migrations/**`
   - `**/__pycache__/**`
   - `**/venv/**`, `**/.venv/**`
   - `**/.git/**`

2. Para cada archivo, cuenta las líneas de código lógico
   (excluye líneas en blanco y líneas que sean solo comentarios o docstrings).

3. Clasifica cada archivo según los límites del `CLAUDE.md`:
   - ✅ Dentro del límite
   - ⚠️  Supera el objetivo pero no el máximo
   - ❌ Supera el máximo absoluto — requiere refactorización obligatoria

4. Genera un reporte interno con este formato:

   ```
   REPORTE DE AUDITORÍA
   ─────────────────────────────────────────────────
   ❌ packages/payments/services.py         — 1.240 líneas
   ❌ packages/users/models.py              —   870 líneas
   ⚠️  packages/orders/utils.py             —   430 líneas
   ✅ packages/notifications/handlers.py   —   210 líneas
   ─────────────────────────────────────────────────
   Total archivos escaneados : XX
   Requieren refactorización : XX
   ```

---

### FASE 2 — Crear Issue en GitHub

Usando la GitHub CLI (`gh`), crea un issue con la siguiente estructura:

```bash
gh issue create \
  --title "refactor: archivos Python superan límite de líneas definido en CLAUDE.md" \
  --label "refactor,technical-debt,python" \
  --body "$(cat <<'EOF'
## Problema detectado

Durante la auditoría automática del monorepo se encontraron archivos Python
que superan los límites de líneas definidos en `CLAUDE.md`.

Archivos con mayor cantidad de líneas por encima del límite:
<!-- INSERTAR TABLA DE REPORTE AQUÍ -->

## Impacto

- Dificulta la mantenibilidad y legibilidad del código.
- Viola el principio SRP (Single Responsibility Principle).
- Aumenta el riesgo de conflictos en PRs dentro del monorepo.

## Criterios de aceptación

- [ ] Todos los archivos `.py` deben estar dentro de los límites del `CLAUDE.md`.
- [ ] Cada archivo nuevo creado debe tener una única responsabilidad.
- [ ] Los tests existentes deben seguir pasando tras la refactorización.
- [ ] El linter (`ruff` / `flake8` / `pylint`) no debe reportar errores nuevos.

## Referencias
- Estándares internos: `CLAUDE.md`
- PEP 8: https://peps.python.org/pep-0008/
EOF
)"
```

Guarda el número del issue creado (ej: `#42`) para usarlo en el commit final.

---

### FASE 3 — Preparar la rama de trabajo

```bash
# Asegúrate de estar actualizado
git checkout develop
git pull origin develop

# Crea y muévete a la rama de refactorización
git checkout -b refactor/python-file-line-limits
```

---

### FASE 4 — Refactorización de archivos

Para **cada archivo** marcado como ❌ en la auditoría:

1. **Analiza** su contenido e identifica responsabilidades distintas.
2. **Propón y ejecuta** la división siguiendo el patrón del `CLAUDE.md`:
   ```
   <feature>/
   ├── models.py
   ├── services.py
   ├── validators.py
   ├── exceptions.py
   └── utils.py
   ```
3. **Actualiza** los imports en todos los archivos del monorepo que
   referencien el archivo original.
4. **Verifica** que el archivo original pueda eliminarse o quede solo
   como re-exportador en `__init__.py` si es necesario por compatibilidad.
5. **Confirma** que el nuevo archivo no supere su propio límite antes
   de continuar con el siguiente.

---

### FASE 5 — Verificaciones y tests (obligatorio antes del merge)

Ejecuta **en este orden** y detente si alguno falla:

```bash
# 1. Linting
ruff check .
# o alternativamente:
flake8 .
pylint packages/

# 2. Formato
ruff format --check .
# o:
black --check .

# 3. Tipado estático (si el proyecto usa mypy)
mypy .

# 4. Tests
pytest --tb=short -q

# 5. Cobertura mínima (ajusta el % según tu proyecto)
pytest --cov=packages --cov-fail-under=80
```

Si alguna verificación falla:
- Corrige el error.
- Vuelve a ejecutar **todas** las verificaciones desde el inicio.
- No avances al merge hasta que todas pasen con ✅.

---

### FASE 6 — Merge a develop

```bash
# Commit de la refactorización en la rama actual
git add .
git commit -m "refactor: dividir archivos Python que superan límite de líneas

- Archivos refactorizados: [lista los archivos principales]
- Closes #<NÚMERO_DE_ISSUE>

Siguiendo estándares definidos en CLAUDE.md:
- Máximo 300 líneas por módulo de lógica de negocio
- Aplicado SRP en cada archivo resultante
- Todos los tests pasan y linter sin errores"

# Merge a develop
git checkout develop
git pull origin develop
git merge --no-ff refactor/python-file-line-limits \
  -m "Merge refactor/python-file-line-limits → develop: closes #<NÚMERO_DE_ISSUE>"
```

---

### FASE 7 — Push y cierre del issue

```bash
# Push de develop a origin
git push origin develop

# Cierra el issue automáticamente con comentario de cierre
gh issue close <NÚMERO_DE_ISSUE> \
  --comment "✅ Refactorización completada y mergeada en \`develop\`.

**Resumen de cambios:**
- Archivos divididos: XX
- Archivos creados: XX
- Líneas máximas tras refactor: XXX
- Tests: ✅ todos pasan
- Linter: ✅ sin errores
- Cobertura: ✅ XX%

Ver merge commit: \`git log develop --oneline -1\`"
```

---

## Reglas generales del agente durante esta tarea

- **Nunca** modifiques lógica de negocio durante la refactorización.
  Solo reorganiza y divide responsabilidades.
- **Nunca** hagas merge si alguna verificación de la Fase 5 falla.
- **Siempre** actualiza los imports en todos los archivos afectados.
- **Siempre** informa el progreso fase por fase antes de continuar.
- Si encuentras ambigüedad en cómo dividir un archivo, **pregunta** antes
  de proceder.