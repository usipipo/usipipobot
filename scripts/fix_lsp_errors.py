#!/usr/bin/env python3
"""
Script automatizado para corregir errores LSP comunes.
Ejecutar desde la raíz del proyecto.
"""

import re
from pathlib import Path


def fix_implicit_optional(content: str) -> str:
    """Corrige parámetros con default None sin tipo Optional."""
    patterns = [
        (r'(\w+):\s*int\s*=\s*None', r'\1: int | None = None'),
        (r'(\w+):\s*str\s*=\s*None', r'\1: str | None = None'),
        (r'(\w+):\s*TicketService\s*=\s*None', r'\1: TicketService | None = None'),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content


def add_none_guard_for_user(content: str) -> str:
    """Añade guard para update.effective_user."""
    pattern = r'(\s+)(user_id|admin_id)\s*=\s*update\.effective_user\.id'
    replacement = r'\1user = update.effective_user\n\1if user is None:\n\1    return\n\1\2 = user.id'
    return re.sub(pattern, replacement, content)


def add_none_guard_for_query_data(content: str) -> str:
    """Añade guard para query.data."""
    pattern = r'(\s+)(\w+)\s*=\s*int\(query\.data\.split'
    replacement = r'\1if query is None or query.data is None:\n\1    return\n\1\2 = int(query.data.split'
    return re.sub(pattern, replacement, content)


def add_none_guard_for_context_userdata(content: str) -> str:
    """Añade guard para context.user_data."""
    pattern = r'(\s+)context\.user_data\[([^\]]+)\]'
    replacement = r'\1if context.user_data is not None:\n\1    context.user_data[\2]'
    return re.sub(pattern, replacement, content)


def fix_base_handler_context_param(content: str) -> str:
    """Corrige el parámetro context con default None en base_handler.py."""
    pattern = r'context:\s*ContextTypes\.DEFAULT_TYPE\s*=\s*None'
    replacement = r'context: ContextTypes.DEFAULT_TYPE | None = None'
    return re.sub(pattern, replacement, content)


def fix_common_keyboards_defaults(content: str) -> str:
    """Corrige defaults en keyboards.py."""
    patterns = [
        (r'target_id:\s*int\s*=\s*None', r'target_id: int | None = None'),
        (r'secondary_text:\s*str\s*=\s*None', r'secondary_text: str | None = None'),
        (r'secondary_callback:\s*str\s*=\s*None', r'secondary_callback: str | None = None'),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content


def fix_telegram_utils_defaults(content: str) -> str:
    """Corrige defaults en telegram_utils.py."""
    patterns = [
        (r'max_length:\s*int\s*=\s*None', r'max_length: int | None = None'),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    return content


def fix_spinner_chat_id(content: str) -> str:
    """Corrige acceso a effective_chat.id en spinner.py."""
    pattern = r'chat_id\s*=\s*update\.effective_chat\.id'
    replacement = '''chat = update.effective_chat
        if chat is None:
            return -1
        chat_id = chat.id'''
    return re.sub(pattern, replacement, content)


def fix_spinner_return_none(content: str) -> str:
    """Corrige return None a return -1 en spinner.py."""
    patterns = [
        (r'return\s+None\s*$', r'return -1'),
    ]
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    return content


def process_file(filepath: Path) -> bool:
    """Procesa un archivo aplicando todas las correcciones."""
    try:
        content = filepath.read_text()
        original = content
        
        if 'handlers' in str(filepath) or 'decorator' in str(filepath):
            content = fix_implicit_optional(content)
        
        if 'base_handler.py' in str(filepath):
            content = fix_base_handler_context_param(content)
        
        if 'keyboards.py' in str(filepath):
            content = fix_common_keyboards_defaults(content)
        
        if 'telegram_utils.py' in str(filepath):
            content = fix_telegram_utils_defaults(content)
        
        if 'spinner.py' in str(filepath):
            content = fix_spinner_chat_id(content)
        
        if content != original:
            filepath.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    
    directories = [
        project_root / "telegram_bot",
        project_root / "utils",
        project_root / "application",
        project_root / "infrastructure",
    ]
    
    fixed_count = 0
    for directory in directories:
        if not directory.exists():
            continue
        for filepath in directory.rglob("*.py"):
            if process_file(filepath):
                fixed_count += 1
                print(f"Fixed: {filepath.relative_to(project_root)}")
    
    print(f"\nTotal files fixed: {fixed_count}")


if __name__ == "__main__":
    main()
