"""
Tests para Message Separators Utilities

Author: uSipipo Team
"""

import pytest

from utils.message_separators import (
    MessageSeparatorBuilder,
    SeparatorStyle,
    SeparatorTemplates,
    TreeSymbol,
    compact_separator,
    section_separator,
    tree_separator,
)


class TestMessageSeparatorBuilder:
    """Tests para MessageSeparatorBuilder."""

    def test_compact_default(self):
        """Test separador compacto por defecto."""
        result = MessageSeparatorBuilder().compact().build()
        assert len(result) == 13
        assert result == "─" * 13

    def test_compact_double_style(self):
        """Test separador con estilo double."""
        result = MessageSeparatorBuilder().compact().style("double").build()
        assert "═" in result

    def test_compact_bold_style(self):
        """Test separador con estilo bold."""
        result = MessageSeparatorBuilder().compact().style("bold").build()
        assert "━" in result

    def test_compact_custom_length(self):
        """Test separador con longitud personalizada."""
        result = MessageSeparatorBuilder().compact().length(20).build()
        assert len(result) == 20

    def test_compact_length_bounds(self):
        """Test límites de longitud."""
        # Mínimo
        result = MessageSeparatorBuilder().compact().length(3).build()
        assert len(result) == 5  # MIN_LENGTH

        # Máximo
        result = MessageSeparatorBuilder().compact().length(50).build()
        assert len(result) == 30  # MAX_LENGTH

    def test_compact_with_emoji_both(self):
        """Test separador con emoji en ambos lados."""
        result = MessageSeparatorBuilder().compact().with_emoji("🔒").build()
        assert result.startswith("🔒")
        assert result.endswith("🔒")
        assert "─" in result

    def test_compact_with_emoji_start(self):
        """Test separador con emoji al inicio."""
        result = MessageSeparatorBuilder().compact().with_emoji("🔒", "start").build()
        assert result.startswith("🔒")
        assert not result.endswith("🔒")

    def test_compact_with_emoji_end(self):
        """Test separador con emoji al final."""
        result = MessageSeparatorBuilder().compact().with_emoji("🔒", "end").build()
        assert not result.startswith("🔒")
        assert result.endswith("🔒")

    def test_tree_single_branch(self):
        """Test árbol con una sola rama."""
        result = MessageSeparatorBuilder().tree().add_branch("Root").build()
        assert "Root" in result
        assert TreeSymbol.END.value in result

    def test_tree_branch_with_leaves(self):
        """Test árbol con rama y hojas."""
        result = (
            MessageSeparatorBuilder()
            .tree()
            .add_branch("Servidores")
            .add_leaf("USA")
            .add_leaf("Germany")
            .build()
        )

        assert "Servidores" in result
        assert "USA" in result
        assert "Germany" in result
        assert TreeSymbol.BRANCH.value in result or TreeSymbol.END.value in result

    def test_tree_multiple_branches(self):
        """Test árbol con múltiples ramas."""
        result = (
            MessageSeparatorBuilder()
            .tree()
            .add_branch("A")
            .add_leaf("A1")
            .add_branch("B")
            .add_leaf("B1")
            .build()
        )

        assert "A" in result
        assert "B" in result
        assert "A1" in result
        assert "B1" in result

    def test_tree_vertical_line_continues(self):
        """Test que las líneas verticales continúan cuando hay más hermanos."""
        result = (
            MessageSeparatorBuilder()
            .tree()
            .add_branch("Parent")
            .add_leaf("Child1")
            .add_leaf("Child2")
            .build()
        )

        lines = result.split("\n")
        # La primera línea debe tener el símbolo de fin
        assert TreeSymbol.END.value in lines[0] or TreeSymbol.BRANCH.value in lines[0]

    def test_chaining_methods(self):
        """Test encadenamiento de métodos."""
        result = (
            MessageSeparatorBuilder()
            .compact()
            .style("double")
            .length(15)
            .with_emoji("✨")
            .build()
        )

        assert "✨" in result
        assert "═" in result
        assert len(result) > 15  # Incluye emojis y espacios


class TestSeparatorTemplates:
    """Tests para SeparatorTemplates."""

    def test_simple_template(self):
        """Test template simple."""
        result = SeparatorTemplates.simple()
        assert len(result) == 13
        assert "─" in result

    def test_double_template(self):
        """Test template double."""
        result = SeparatorTemplates.double()
        assert "═" in result

    def test_bold_template(self):
        """Test template bold."""
        result = SeparatorTemplates.bold()
        assert "━" in result

    def test_section_header_with_title(self):
        """Test header de sección con título."""
        result = SeparatorTemplates.section_header("Test Section", "📌")
        assert "Test Section" in result
        assert "📌" in result
        assert "═" in result

    def test_section_header_without_title(self):
        """Test header de sección sin título."""
        result = SeparatorTemplates.section_header()
        assert "═" in result
        assert "\n" in result

    def test_menu_divider(self):
        """Test divisor de menú."""
        result = SeparatorTemplates.menu_divider()
        assert "─" in result
        assert len(result) == 15

    def test_decorative(self):
        """Test separador decorativo."""
        result = SeparatorTemplates.decorative("✨")
        assert "✨" in result
        assert "─" in result

    def test_tree_root(self):
        """Test raíz de árbol."""
        result = SeparatorTemplates.tree_root("Root")
        assert "Root" in result


class TestHelperFunctions:
    """Tests para funciones helper."""

    def test_compact_separator_default(self):
        """Test función compact_separator por defecto."""
        result = compact_separator()
        assert len(result) == 13
        assert "─" in result

    def test_compact_separator_with_emoji(self):
        """Test función compact_separator con emoji."""
        result = compact_separator("double", 15, "🔒")
        assert "🔒" in result
        assert "═" in result

    def test_compact_separator_different_styles(self):
        """Test compact_separator con diferentes estilos."""
        styles = ["simple", "double", "bold", "dotted", "dashed"]
        for style in styles:
            result = compact_separator(style)
            assert len(result) > 0

    def test_tree_separator_with_root(self):
        """Test tree_separator con raíz."""
        result = tree_separator(["Item1", "Item2"], "Root")
        assert "Root" in result
        assert "Item1" in result
        assert "Item2" in result

    def test_tree_separator_without_root(self):
        """Test tree_separator sin raíz."""
        result = tree_separator(["A", "B", "C"])
        assert "A" in result
        assert "B" in result
        assert "C" in result

    def test_section_separator(self):
        """Test section_separator."""
        result = section_separator("My Section", "🎯")
        assert "My Section" in result
        assert "🎯" in result
        assert "═" in result


class TestSeparatorStyles:
    """Tests para los estilos de separador."""

    def test_all_styles_have_char(self):
        """Test que todos los estilos tienen carácter."""
        for style in SeparatorStyle:
            assert len(style.value) > 0
            assert isinstance(style.value, str)

    def test_tree_symbols(self):
        """Test símbolos de árbol."""
        assert len(TreeSymbol.VERTICAL.value) == 1
        assert len(TreeSymbol.BRANCH.value) == 2
        assert len(TreeSymbol.END.value) == 2


class TestEdgeCases:
    """Tests para casos edge."""

    def test_empty_tree_build(self):
        """Test construir árbol vacío."""
        result = MessageSeparatorBuilder().tree().build()
        assert result == ""

    def test_build_without_mode_defaults_to_compact(self):
        """Test que build sin modo usa compact."""
        result = MessageSeparatorBuilder().build()
        assert "─" in result

    def test_add_leaf_without_branch_creates_branch(self):
        """Test que add_leaf sin branch crea uno."""
        result = MessageSeparatorBuilder().tree().add_leaf("Leaf").build()
        assert "Leaf" in result

    def test_invalid_style_ignored(self):
        """Test que estilo inválido es ignorado."""
        result = MessageSeparatorBuilder().compact().style("invalid").build()
        # Debe usar el estilo por defecto (simple)
        assert "─" in result

    def test_unicode_support(self):
        """Test soporte de caracteres Unicode."""
        result = MessageSeparatorBuilder().compact().style("double").build()
        # Verificar que los caracteres Unicode se manejan correctamente
        assert isinstance(result, str)
        assert len(result.encode("utf-8")) > len(result)  # Multi-byte chars
