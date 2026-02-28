#!/usr/bin/env bash
#
# Script: merge_to_main.sh
# Descripción: Realiza merge limpio de develop a main usando squash
# y excluye archivos de desarrollo (planes, tests, etc.)
#

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables globales
DRY_RUN=false
FORCE=false
VERSION=""
WORKTREE_DIR=""
ORIGINAL_BRANCH=""

# Archivos y patrones a excluir de main
EXCLUDE_PATTERNS=(
    "docs/plans/"
    "PLAN.md"
    "spec.md"
    "tests/"
    "*_test.py"
    "test_*.py"
    "requirements-dev.txt"
    ".env.example"
    ".env.template"
    "scripts/dev_*.sh"
    "scripts/setup_dev*"
    ".github/workflows/dev*.yml"
    ".github/workflows/test*.yml"
    "conductor/"
    "**/.conductor/"
)

#######################################
# Funciones de utilidad
#######################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#######################################
# FASE 1: Validación Pre-Merge
#######################################

validate_pre_merge() {
    log_info "FASE 1: Validando condiciones pre-merge..."
    
    # Verificar que estamos en un repo git
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "No estás en un repositorio git"
        exit 1
    fi
    
    # Guardar rama actual
    ORIGINAL_BRANCH=$(git branch --show-current)
    
    # Verificar que estamos en develop
    if [[ "$ORIGINAL_BRANCH" != "develop" ]]; then
        log_error "Debes estar en la rama 'develop'. Rama actual: $ORIGINAL_BRANCH"
        log_info "Ejecuta: git checkout develop"
        exit 1
    fi
    
    # Verificar que no hay cambios sin commitear
    if ! git diff-index --quiet HEAD --; then
        log_error "Hay cambios sin commitear en develop"
        log_info "Ejecuta: git add . && git commit -m '...' o git stash"
        exit 1
    fi
    
    # Verificar que main existe
    if ! git show-ref --verify --quiet refs/heads/main; then
        log_error "La rama 'main' no existe"
        exit 1
    fi
    
    # Verificar que develop está actualizada respecto a origin
    git fetch origin develop --quiet 2>/dev/null || true
    LOCAL_DEVELOP=$(git rev-parse develop)
    REMOTE_DEVELOP=$(git rev-parse origin/develop 2>/dev/null || echo "$LOCAL_DEVELOP")
    
    if [[ "$LOCAL_DEVELOP" != "$REMOTE_DEVELOP" ]]; then
        log_warn "La rama develop local difiere de origin/develop"
        if [[ "$FORCE" == false ]]; then
            log_info "Ejecuta: git pull origin develop"
            exit 1
        fi
    fi
    
    # Validar formato de versión si se proporcionó
    if [[ -n "$VERSION" ]]; then
        if ! [[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            log_error "Formato de versión inválido: $VERSION"
            log_info "Usa formato semántico: vX.Y.Z (ej: v1.2.3)"
            exit 1
        fi
    fi
    
    log_info "Validación completada ✓"
}

#######################################
# FASE 2: Calcular siguiente versión
#######################################

calculate_next_version() {
    log_info "Calculando siguiente versión..."
    
    # Obtener último tag
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
    
    if [[ -n "$VERSION" ]]; then
        log_info "Versión especificada manualmente: $VERSION"
        return
    fi
    
    # Parsear versión actual
    local major minor patch
    major=$(echo "$last_tag" | sed -E 's/v([0-9]+)\.([0-9]+)\.([0-9]+)/\1/')
    minor=$(echo "$last_tag" | sed -E 's/v([0-9]+)\.([0-9]+)\.([0-9]+)/\2/')
    patch=$(echo "$last_tag" | sed -E 's/v([0-9]+)\.([0-9]+)\.([0-9]+)/\3/')
    
    # Analizar commits desde último tag para determinar bump
    local commits
    commits=$(git log "${last_tag}..develop" --pretty=format:"%s" 2>/dev/null || echo "")
    
    local has_breaking=false
    local has_feat=false
    local has_fix=false
    
    while IFS= read -r commit; do
        [[ -z "$commit" ]] && continue
        
        if [[ "$commit" =~ ^[a-z]+(\(.+\))?!: ]] || [[ "$commit" =~ BREAKING[[:space:]]CHANGE ]]; then
            has_breaking=true
        elif [[ "$commit" =~ ^feat(\(.+\))?: ]]; then
            has_feat=true
        elif [[ "$commit" =~ ^fix(\(.+\))?: ]]; then
            has_fix=true
        fi
    done <<< "$commits"
    
    # Calcular nueva versión
    if [[ "$has_breaking" == true ]]; then
        major=$((major + 1))
        minor=0
        patch=0
    elif [[ "$has_feat" == true ]]; then
        minor=$((minor + 1))
        patch=0
    elif [[ "$has_fix" == true ]]; then
        patch=$((patch + 1))
    else
        patch=$((patch + 1))
    fi
    
    VERSION="v${major}.${minor}.${patch}"
    log_info "Nueva versión calculada: $VERSION (desde $last_tag)"
}

#######################################
# FASE 3: Crear worktree limpio
#######################################

setup_worktree() {
    log_info "FASE 3: Configurando worktree temporal..."
    
    WORKTREE_DIR=$(mktemp -d -t merge-to-main.XXXXXX)
    log_info "Worktree creado en: $WORKTREE_DIR"
    
    # Crear worktree desde main
    git worktree add "$WORKTREE_DIR" main
    
    # Configurar sparse-checkout para excluir archivos
    cd "$WORKTREE_DIR"
    git sparse-checkout init --cone
    
    # En main queremos todo EXCEPTO los patrones excluidos
    # Git sparse-checkout funciona al revés: definimos qué INCLUIR
    # Por eso hacemos un approach diferente: merge y luego eliminar
    
    log_info "Worktree configurado ✓"
}

#######################################
# FASE 4: Generar Changelog
#######################################

generate_changelog() {
    log_info "FASE 4: Generando changelog..."
    
    local last_tag
    last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    local range
    if [[ -n "$last_tag" ]]; then
        range="${last_tag}..develop"
    else
        range="develop"
    fi
    
    local commits
    commits=$(git log "$range" --pretty=format:"%s" 2>/dev/null || echo "")
    
    local features=""
    local fixes=""
    local chores=""
    local others=""
    
    while IFS= read -r commit; do
        [[ -z "$commit" ]] && continue
        
        local msg
        msg=$(echo "$commit" | sed -E 's/^[a-z]+(\(.+\))?!?:[[:space:]]*//')
        
        if [[ "$commit" =~ ^feat(\(.+\))?!?: ]]; then
            features="${features}- ${msg}\n"
        elif [[ "$commit" =~ ^fix(\(.+\))?!?: ]]; then
            fixes="${fixes}- ${msg}\n"
        elif [[ "$commit" =~ ^chore(\(.+\))?!?: ]]; then
            chores="${chores}- ${msg}\n"
        elif [[ "$commit" =~ ^[a-z]+(\(.+\))?!?: ]]; then
            others="${others}- ${msg}\n"
        fi
    done <<< "$commits"
    
    # Crear contenido del changelog
    local changelog="## [$VERSION] - $(date +%Y-%m-%d)\n\n"
    
    if [[ -n "$features" ]]; then
        changelog="${changelog}### Features\n${features}\n"
    fi
    if [[ -n "$fixes" ]]; then
        changelog="${changelog}### Bug Fixes\n${fixes}\n"
    fi
    if [[ -n "$chores" ]]; then
        changelog="${changelog}### Chores\n${chores}\n"
    fi
    if [[ -n "$others" ]]; then
        changelog="${changelog}### Other Changes\n${others}\n"
    fi
    
    echo -e "$changelog"
}

#######################################
# FASE 5: Ejecutar Squash Merge
#######################################

execute_squash_merge() {
    log_info "FASE 5: Ejecutando squash merge..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "[DRY-RUN] Simulando merge..."
    fi
    
    cd "$WORKTREE_DIR"
    
    # Hacer squash merge desde develop
    if [[ "$DRY_RUN" == false ]]; then
        git merge --squash develop || {
            log_error "Conflicto durante el merge. Abortando."
            git merge --abort 2>/dev/null || true
            exit 1
        }
    fi
    
    # Eliminar archivos excluidos
    log_info "Eliminando archivos de desarrollo..."
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ "$pattern" == *"*"* ]]; then
            # Es un glob pattern
            find . -path "./.git" -prune -o -name "$pattern" -type f -print 2>/dev/null | head -20 | while read -r file; do
                if [[ "$DRY_RUN" == false ]]; then
                    rm -f "$file"
                fi
                log_info "  Eliminado: $file"
            done || true
        else
            # Es un path específico
            if [[ -e "$pattern" ]]; then
                if [[ "$DRY_RUN" == false ]]; then
                    rm -rf "$pattern"
                fi
                log_info "  Eliminado: $pattern"
            fi
        fi
    done
    
    log_info "Squash merge completado ✓"
}

#######################################
# FASE 6: Crear commit y tag
#######################################

create_commit_and_tag() {
    log_info "FASE 6: Creando commit y tag de release..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "[DRY-RUN] No se crea commit ni tag"
        return
    fi
    
    cd "$WORKTREE_DIR"
    
    # Generar changelog
    local changelog
    changelog=$(generate_changelog)
    
    # Actualizar CHANGELOG.md si existe
    if [[ -f "CHANGELOG.md" ]]; then
        local temp_changelog
        temp_changelog=$(mktemp)
        echo -e "$changelog\n" > "$temp_changelog"
        cat CHANGELOG.md >> "$temp_changelog"
        mv "$temp_changelog" CHANGELOG.md
        git add CHANGELOG.md
    fi
    
    # Actualizar versión en pyproject.toml si existe
    if [[ -f "pyproject.toml" ]]; then
        sed -i -E "s/version = \"[0-9]+\.[0-9]+\.[0-9]+\"/version = \"${VERSION#v}\"/" pyproject.toml
        git add pyproject.toml
    fi
    
    # Actualizar versión en package.json si existe
    if [[ -f "package.json" ]]; then
        sed -i -E "s/\"version\": \"[0-9]+\.[0-9]+\.[0-9]+\"/\"version\": \"${VERSION#v}\"/" package.json
        git add package.json
    fi
    
    # Crear commit
    git add -A
    git commit -m "chore(release): ${VERSION}

${changelog}" || {
        log_warn "No hay cambios para commitear"
        return
    }
    
    # Crear tag anotado
    git tag -a "$VERSION" -m "Release ${VERSION}"
    
    log_info "Commit y tag creados ✓"
    log_info "  Commit: $(git rev-parse --short HEAD)"
    log_info "  Tag: $VERSION"
}

#######################################
# FASE 7: Verificación y Push
#######################################

verify_and_push() {
    log_info "FASE 7: Verificación y push..."
    
    cd "$WORKTREE_DIR"
    
    # Verificar que no quedan archivos excluidos
    log_info "Verificando limpieza del árbol..."
    local found_excluded=false
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        if [[ -e "$pattern" ]]; then
            log_warn "Archivo excluido encontrado: $pattern"
            found_excluded=true
        fi
    done
    
    if [[ "$found_excluded" == true && "$FORCE" == false ]]; then
        log_error "Hay archivos excluidos presentes. Usa --force para ignorar."
        exit 1
    fi
    
    # Mostrar resumen
    log_info "Resumen de cambios:"
    git log --oneline main..HEAD | head -5
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "[DRY-RUN] No se realiza push"
        log_info "Para ejecutar realmente, omite --dry-run"
    else
        # Push a main
        git push origin main
        git push origin "$VERSION"
        log_info "Push completado ✓"
        log_info "Release $VERSION publicada en main"
    fi
}

#######################################
# Limpieza
#######################################

cleanup() {
    log_info "Limpiando..."
    
    if [[ -n "$WORKTREE_DIR" && -d "$WORKTREE_DIR" ]]; then
        cd "$WORKTREE_DIR/.." 2>/dev/null || true
        git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || rm -rf "$WORKTREE_DIR"
        log_info "Worktree eliminado"
    fi
    
    # Volver a rama original
    if [[ -n "$ORIGINAL_BRANCH" ]]; then
        cd - > /dev/null 2>&1 || true
        git checkout "$ORIGINAL_BRANCH" 2>/dev/null || true
    fi
}

#######################################
# Main
#######################################

show_usage() {
    cat << EOF
Uso: merge_to_main.sh [OPCIONES] [VERSION]

Realiza merge limpio de develop a main con squash, excluyendo archivos de desarrollo.

ARGUMENTOS:
  VERSION         Versión en formato vX.Y.Z (opcional, se auto-calcula si no se provee)

OPCIONES:
  -d, --dry-run   Simula el proceso sin hacer cambios reales
  -f, --force     Omite validaciones de seguridad
  -h, --help      Muestra esta ayuda

EJEMPLOS:
  merge_to_main.sh                    # Auto-calcula versión y ejecuta
  merge_to_main.sh v1.2.3             # Usa versión específica
  merge_to_main.sh --dry-run          # Simulación
  merge_to_main.sh v2.0.0 --dry-run   # Simulación con versión específica

ARCHIVOS EXCLUIDOS DE MAIN:
  - docs/plans/, PLAN.md, spec.md
  - tests/, *_test.py, test_*.py
  - requirements-dev.txt, .env.example
  - scripts/dev_*.sh
  - .github/workflows/dev*.yml
EOF
}

main() {
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            v[0-9]*.[0-9]*.[0-9]*)
                VERSION="$1"
                shift
                ;;
            *)
                log_error "Opción desconocida: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Mostrar banner
    echo "========================================"
    echo "  Git Merge to Main - Clean Release"
    echo "========================================"
    echo ""
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warn "MODO DRY-RUN: No se realizarán cambios reales"
        echo ""
    fi
    
    # Ejecutar fases
    validate_pre_merge
    calculate_next_version
    
    if [[ "$DRY_RUN" == false ]]; then
        log_info "La rama develop NUNCA será eliminada"
        log_info "Se creará release: $VERSION"
        echo ""
        read -p "¿Continuar? (s/N): " confirm
        if [[ ! "$confirm" =~ ^[Ss]$ ]]; then
            log_info "Operación cancelada"
            exit 0
        fi
    fi
    
    # Setup trap para limpieza
    trap cleanup EXIT
    
    setup_worktree
    execute_squash_merge
    create_commit_and_tag
    verify_and_push
    
    echo ""
    log_info "¡Merge completado exitosamente!"
    log_info "Release $VERSION disponible en main"
}

main "$@"
