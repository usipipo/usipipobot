# Skill: Estándares de tamaño de archivos Python en Monorepo

## Regla principal
Ningún archivo Python nuevo debe superar las **300 líneas de código lógico**
(sin contar líneas en blanco ni comentarios/docstrings).

---

## Límites por tipo de archivo

| Tipo de archivo                        | Objetivo   | Máximo absoluto |
|----------------------------------------|------------|-----------------|
| Módulo / lógica de negocio             | 200–300    | 400 líneas      |
| Clase principal                        | 150–250    | 350 líneas      |
| Utilidades (`utils.py`, `helpers.py`)  | 100–200    | 300 líneas      |
| Configuración (`settings.py`)          | 50–150     | 250 líneas      |
| Tests (`test_*.py`)                    | 200–400    | 500 líneas      |
| `__init__.py`                          | 10–30      | 80 líneas       |
| Scripts de entrada (`main.py`,`cli.py`)| 50–100     | 150 líneas      |

---

## Cuándo dividir un archivo (obligatorio)

Divide el archivo si se cumple **alguna** de estas condiciones:

- [ ] Supera el máximo absoluto definido en la tabla anterior.
- [ ] Contiene más de una clase con responsabilidades distintas.
- [ ] Tiene más de 15 imports en la sección de cabecera.
- [ ] Mezcla lógica de negocio, validación y acceso a datos en el mismo archivo.
- [ ] Es difícil de testear de forma aislada.

---

## Patrón de división recomendado

Cuando un módulo crece, divídelo siguiendo esta estructura:

```
packages/
└── <feature>/
    ├── __init__.py        # Solo exports públicos (< 30 líneas)
    ├── models.py          # Modelos de datos / schemas
    ├── services.py        # Lógica de negocio principal
    ├── validators.py      # Validaciones de entrada
    ├── exceptions.py      # Excepciones personalizadas
    ├── utils.py           # Helpers internos del módulo
    └── tests/
        ├── test_services.py
        └── test_validators.py
```

---

## Instrucciones para generación de código nuevo

Al crear un archivo Python nuevo:

1. **Estima** el número de líneas antes de escribir. Si la estimación supera
   el límite del tipo, propón la división desde el inicio.

2. **Aplica SRP** (Single Responsibility Principle): cada archivo tiene
   una única razón para cambiar.

3. **No acumules** en `utils.py`. Si ese archivo crece más de 200 líneas,
   subdivídelo por dominio (ej: `date_utils.py`, `string_utils.py`).

4. **Reporta** al finalizar cuántas líneas tiene el archivo creado:
   ```
   ✅ services.py — 187 líneas (dentro del límite: 300)
   ⚠️  validators.py — 310 líneas (supera objetivo, considera dividir)
   ❌ models.py — 520 líneas (supera máximo absoluto — dividir obligatorio)
   ```

5. **Nunca** combines en un mismo archivo:
   - Lógica de negocio + acceso a base de datos
   - Modelos de datos + lógica de transformación
   - Configuración + lógica de aplicación

---

## Refactorización de archivos existentes con > 400 líneas

Si se te pide modificar o extender un archivo que ya supera el máximo:

1. Notifica el problema antes de continuar:
   > "Este archivo tiene X líneas, lo que supera el máximo de Y.
   > Recomiendo refactorizarlo antes de agregar más código."

2. Propón un plan de división con los nuevos archivos y su contenido estimado.

3. Ejecuta la división **antes** de agregar la nueva funcionalidad, salvo
   indicación explícita del usuario.

---

## Configuración de linters (referencia)

```toml
# pyproject.toml
[tool.ruff]
line-length = 88

[tool.pylint.FORMAT]
max-line-length = 88
max-module-lines = 400
```

```ini
# .flake8
[flake8]
max-line-length = 88
max-module-lines = 400
```
