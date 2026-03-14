"""
Message Separators Utilities

Sistema de separadores visuales para mensajes de Telegram.
Proporciona dos estilos principales:
- Vista Compacta: Separadores lineales simples
- Vista de Árbol: Estructuras jerárquicas

Author: uSipipo Team
Version: 1.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Self

# Longitud óptima para visualización en móviles (Telegram)
# Basado en análisis de BitBread IA: 13 caracteres es el punto
# óptimo para pantallas pequeñas sin romper la línea
TELEGRAM_MOBILE_WIDTH = 13

# Longitud alternativa para más énfasis visual
TELEGRAM_WIDE_WIDTH = 17

# Límites generales
MAX_SEPARATOR_LENGTH = 30
MIN_SEPARATOR_LENGTH = 5


class SeparatorStyle(Enum):
    """Estilos de separadores lineales."""

    SIMPLE = "─"  # U+2500 Box Drawings Light Horizontal
    DOUBLE = "═"  # U+2550 Box Drawings Double Horizontal
    BOLD = "━"  # U+2501 Box Drawings Heavy Horizontal
    DOTTED = "┈"  # U+2508 Box Drawings Light Quadruple Dash Horizontal
    DASHED = "┄"  # U+2504 Box Drawings Light Triple Dash Horizontal


class TreeSymbol(Enum):
    """Símbolos para estructuras de árbol."""

    VERTICAL = "│"  # U+2502
    BRANCH = "├─"  # U+251C + U+2500
    END = "└─"  # U+2514 + U+2500
    SPACE = "  "


@dataclass
class TreeNode:
    """Nodo para estructura de árbol."""

    label: str
    is_last: bool = False
    children: List["TreeNode"] = field(default_factory=list)


class MessageSeparatorBuilder:
    """
    Builder para crear separadores visuales de mensajes.

    Uso:
        # Separador compacto simple
        sep = MessageSeparatorBuilder().compact().build()

        # Separador con emoji
        sep = MessageSeparatorBuilder()\
            .compact()\
            .style('double')\
            .with_emoji('🔒')\
            .build()

        # Estructura de árbol
        tree = MessageSeparatorBuilder()\
            .tree()\
            .add_branch("Servidores")\
            .add_leaf("🇺🇸 USA")\
            .add_leaf("🇩🇪 Alemania")\
            .build()
    """

    # Referencias a constantes del módulo para compatibilidad
    DEFAULT_LENGTH = TELEGRAM_MOBILE_WIDTH
    MAX_LENGTH = MAX_SEPARATOR_LENGTH
    MIN_LENGTH = MIN_SEPARATOR_LENGTH

    def __init__(self):
        self._mode: Optional[str] = None
        self._style: SeparatorStyle = SeparatorStyle.SIMPLE
        self._length: int = self.DEFAULT_LENGTH
        self._emoji: Optional[str] = None
        self._emoji_position: str = "both"  # 'start', 'end', 'both'
        self._tree_nodes: List[TreeNode] = []
        self._current_branch: Optional[TreeNode] = None

    def compact(self) -> Self:
        """Modo compacto - separadores lineales."""
        self._mode = "compact"
        return self

    def tree(self) -> Self:
        """Modo árbol - estructura jerárquica."""
        self._mode = "tree"
        return self

    def style(self, style_name: str) -> Self:
        """
        Estilo del separador lineal.

        Args:
            style_name: 'simple', 'double', 'bold', 'dotted', 'dashed'
        """
        style_map = {
            "simple": SeparatorStyle.SIMPLE,
            "double": SeparatorStyle.DOUBLE,
            "bold": SeparatorStyle.BOLD,
            "dotted": SeparatorStyle.DOTTED,
            "dashed": SeparatorStyle.DASHED,
        }
        if style_name.lower() in style_map:
            self._style = style_map[style_name.lower()]
        return self

    def length(self, chars: int) -> Self:
        """
        Longitud del separador en caracteres.

        Args:
            chars: Número de caracteres (5-30)
        """
        self._length = max(self.MIN_LENGTH, min(self.MAX_LENGTH, chars))
        return self

    def with_emoji(self, emoji: str, position: str = "both") -> Self:
        """
        Agregar emoji al separador.

        Args:
            emoji: Emoji a incluir
            position: 'start', 'end', o 'both'
        """
        self._emoji = emoji
        self._emoji_position = position
        return self

    def add_branch(self, label: str) -> Self:
        """
        Agregar una rama principal en modo árbol.

        Args:
            label: Etiqueta de la rama
        """
        if self._mode != "tree":
            self._mode = "tree"

        branch = TreeNode(label=label)
        self._tree_nodes.append(branch)
        self._current_branch = branch
        return self

    def add_leaf(self, label: str) -> Self:
        """
        Agregar una hoja a la rama actual en modo árbol.

        Args:
            label: Etiqueta de la hoja
        """
        if self._mode != "tree":
            self._mode = "tree"

        if self._current_branch is None:
            self.add_branch("Root")

        leaf = TreeNode(label=label)
        if self._current_branch is not None:
            self._current_branch.children.append(leaf)
        return self

    def add_nested_branch(self, label: str) -> Self:
        """
        Agregar una sub-rama a la rama actual.

        Args:
            label: Etiqueta de la sub-rama
        """
        nested = TreeNode(label=label)
        if self._current_branch is None:
            self._tree_nodes.append(nested)
            self._current_branch = nested
        else:
            self._current_branch.children.append(nested)
        return self

    def _build_compact(self) -> str:
        """Construir separador compacto."""
        separator = self._style.value * self._length

        if self._emoji:
            if self._emoji_position == "both":
                return f"{self._emoji} {separator} {self._emoji}"
            elif self._emoji_position == "start":
                return f"{self._emoji} {separator}"
            elif self._emoji_position == "end":
                return f"{separator} {self._emoji}"

        return separator

    def _build_tree(self) -> str:
        """Construir estructura de árbol."""
        lines = []

        for i, node in enumerate(self._tree_nodes):
            is_last_node = i == len(self._tree_nodes) - 1

            # Nodo principal
            prefix = TreeSymbol.END.value if is_last_node else TreeSymbol.BRANCH.value
            lines.append(f"{prefix} {node.label}")

            # Hijos del nodo
            for j, child in enumerate(node.children):
                is_last_child = j == len(node.children) - 1
                child_prefix = TreeSymbol.END.value if is_last_child else TreeSymbol.BRANCH.value

                # Indentación con línea vertical si hay más hermanos
                indent = TreeSymbol.VERTICAL.value if not is_last_node else TreeSymbol.SPACE.value
                lines.append(f"{indent}  {child_prefix} {child.label}")

        return "\n".join(lines) if lines else ""

    def build(self) -> str:
        """
        Construir y retornar el separador.

        Returns:
            str: Separador formateado
        """
        if self._mode == "tree":
            return self._build_tree()
        else:
            # Default to compact
            return self._build_compact()


class SeparatorTemplates:
    """
    Plantillas predefinidas de separadores para uso rápido.
    """

    @staticmethod
    def simple(length: int = 13) -> str:
        """Separador simple."""
        return MessageSeparatorBuilder().compact().length(length).build()

    @staticmethod
    def double(length: int = 13) -> str:
        """Separador doble."""
        return MessageSeparatorBuilder().compact().style("double").length(length).build()

    @staticmethod
    def bold(length: int = 13) -> str:
        """Separador bold."""
        return MessageSeparatorBuilder().compact().style("bold").length(length).build()

    @staticmethod
    def section_header(title: str = "", emoji: str = "📌") -> str:
        """Separador de sección con título."""
        if title:
            return f"\n{emoji} {title}\n{SeparatorTemplates.double()}\n"
        return f"\n{SeparatorTemplates.double()}\n"

    @staticmethod
    def menu_divider() -> str:
        """Separador para menús."""
        return MessageSeparatorBuilder().compact().style("simple").length(15).build()

    @staticmethod
    def decorative(emoji: str = "✨") -> str:
        """Separador decorativo con emoji."""
        return MessageSeparatorBuilder().compact().with_emoji(emoji).build()

    @staticmethod
    def tree_root(label: str) -> str:
        """Raíz de árbol."""
        return MessageSeparatorBuilder().tree().add_branch(label).build()


# Constantes predefinidas para uso directo
SEPARATOR_SIMPLE = SeparatorTemplates.simple()
SEPARATOR_DOUBLE = SeparatorTemplates.double()
SEPARATOR_BOLD = SeparatorTemplates.bold()
SEPARATOR_MENU = SeparatorTemplates.menu_divider()


def compact_separator(style: str = "simple", length: int = 13, emoji: Optional[str] = None) -> str:
    """
    Función rápida para separador compacto.

    Args:
        style: 'simple', 'double', 'bold', 'dotted', 'dashed'
        length: Longitud del separador
        emoji: Emoji opcional

    Returns:
        str: Separador formateado

    Example:
        >>> compact_separator('double', 15, '🔒')
        '🔒 ═══════════════ 🔒'
    """
    builder = MessageSeparatorBuilder().compact().style(style).length(length)
    if emoji:
        builder.with_emoji(emoji)
    return builder.build()


def tree_separator(items: List[str], root_label: Optional[str] = None) -> str:
    """
    Función rápida para estructura de árbol.

    Args:
        items: Lista de elementos
        root_label: Etiqueta opcional de la raíz

    Returns:
        str: Árbol formateado

    Example:
        >>> tree_separator(['Item 1', 'Item 2'], 'Root')
        '└─ Root\n   ├─ Item 1\n   └─ Item 2'
    """
    builder = MessageSeparatorBuilder().tree()

    if root_label:
        builder.add_branch(root_label)
        for item in items:
            builder.add_leaf(item)
    else:
        for i, item in enumerate(items):
            if i == 0:
                builder.add_branch(item)
            else:
                builder.add_leaf(item)

    return builder.build()


def section_separator(title: str, emoji: str = "📌") -> str:
    """
    Separador de sección completo con título.

    Args:
        title: Título de la sección
        emoji: Emoji del título

    Returns:
        str: Separador formateado
    """
    return SeparatorTemplates.section_header(title, emoji)
