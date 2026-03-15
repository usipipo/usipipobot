"""
Tests for spinner utilities.

Tests the spinner functionality and message replacement.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import BadRequest

from utils.spinner import SpinnerManager
from utils.telegram_utils import TelegramUtils


class TestReplaceSpinnerWithMessage:
    """Test the replace_spinner_with_message function."""

    @pytest.mark.asyncio
    async def test_replace_spinner_callback_with_text(self):
        """Test replacing spinner when callback message has text."""
        update = MagicMock()
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.delete_message = AsyncMock()

        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        update.callback_query = MagicMock()
        update.callback_query.edit_message_text = AsyncMock()

        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id=999, text="Test message"
        )

        # Verify spinner was deleted
        context.bot.delete_message.assert_called_once_with(chat_id=12345, message_id=999)
        # Verify callback message was edited
        update.callback_query.edit_message_text.assert_called_once_with(
            text="Test message", reply_markup=None, parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_replace_spinner_no_text_in_message_fallback(self):
        """Test fallback to send_message when callback has no text to edit."""
        update = MagicMock()
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.delete_message = AsyncMock()
        context.bot.send_message = AsyncMock()

        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        update.callback_query = MagicMock()
        # Simulate "no text in message" error
        update.callback_query.edit_message_text = AsyncMock(
            side_effect=BadRequest("There is no text in the message to edit")
        )

        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id=999, text="Test message"
        )

        # Verify spinner was deleted
        context.bot.delete_message.assert_called_once()
        # Verify edit was attempted
        update.callback_query.edit_message_text.assert_called_once()
        # Verify fallback to send_message
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Test message", reply_markup=None, parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_replace_spinner_message_not_modified(self):
        """Test handling of 'message not modified' error - no action needed."""
        update = MagicMock()
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.delete_message = AsyncMock()
        context.bot.send_message = AsyncMock()

        update.effective_chat = MagicMock()
        update.effective_chat.id = 12345
        update.callback_query = MagicMock()
        # Simulate "message not modified" error
        update.callback_query.edit_message_text = AsyncMock(
            side_effect=BadRequest(
                "Message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message"
            )
        )

        # Should not raise - message not modified is not an error, just means content is the same
        await SpinnerManager.replace_spinner_with_message(
            update, context, spinner_message_id=999, text="Same message"
        )

        # When message is not modified, we just log it - no fallback needed
        # since the message already has the same content
        context.bot.send_message.assert_not_called()


class TestSafeEditMessage:
    """Test the TelegramUtils.safe_edit_message function."""

    @pytest.mark.asyncio
    async def test_safe_edit_success(self):
        """Test successful message edit."""
        query = MagicMock()
        query.edit_message_text = AsyncMock()
        context = MagicMock()

        result = await TelegramUtils.safe_edit_message(query, context, "Test message")

        assert result is True
        query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_edit_no_text_fallback(self):
        """Test fallback when message has no text."""
        query = MagicMock()
        query.message = MagicMock()
        query.message.chat = MagicMock()
        query.message.chat.id = 12345
        query.edit_message_text = AsyncMock(
            side_effect=BadRequest("There is no text in the message to edit")
        )
        context = MagicMock()
        context.bot = MagicMock()
        context.bot.send_message = AsyncMock()

        result = await TelegramUtils.safe_edit_message(query, context, "Test message")

        assert result is True
        # Verify fallback to send_message
        context.bot.send_message.assert_called_once_with(
            chat_id=12345, text="Test message", reply_markup=None, parse_mode=None
        )

    @pytest.mark.asyncio
    async def test_safe_edit_message_not_modified(self):
        """Test handling of message not modified error."""
        query = MagicMock()
        query.edit_message_text = AsyncMock(side_effect=BadRequest("Message is not modified"))
        context = MagicMock()

        result = await TelegramUtils.safe_edit_message(query, context, "Same content")

        assert result is True  # Should return True as it's not a real error

    @pytest.mark.asyncio
    async def test_safe_edit_parse_error_fallback(self):
        """Test fallback when Markdown parsing fails."""
        query = MagicMock()
        query.edit_message_text = AsyncMock(
            side_effect=[
                BadRequest(
                    "Can't parse entities: can't find end of the entity starting at byte offset 10"
                ),
                None,  # Second call succeeds
            ]
        )
        context = MagicMock()

        result = await TelegramUtils.safe_edit_message(
            query, context, "Test with *invalid markdown", parse_mode="Markdown"
        )

        assert result is True
        # Verify second call without parse_mode
        assert query.edit_message_text.call_count == 2
        second_call = query.edit_message_text.call_args_list[1]
        assert "parse_mode" not in second_call.kwargs
