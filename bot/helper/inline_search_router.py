#!/usr/bin/env python3
"""
Unified inline search router that handles AI Assistant and help messages.
Music search modules (Streamrip/Zotify) have been removed.
"""

from pyrogram.types import InlineQuery

from bot import LOGGER
from bot.core.config_manager import Config


class ModifiedInlineQuery:
    """A wrapper for InlineQuery with a modified query string."""
    def __init__(self, original_query, modified_text):
        self.original = original_query
        self.query = modified_text
        self.id = original_query.id
        self.from_user = original_query.from_user
        self.chat = getattr(original_query, 'chat', None)

    def __getattr__(self, name):
        return getattr(self.original, name)

    async def answer(self, *args, **kwargs):
        return await self.original.answer(*args, **kwargs)


async def unified_inline_search_handler(client, inline_query: InlineQuery):
    """
    Unified inline search handler that routes queries to appropriate modules.

    Routing logic:
    - Queries starting with 'ai:' or 'ask:' -> AI Assistant
    - All other queries -> AI if enabled or show help
    """
    query = inline_query.query.strip()

    # Route to AI Assistant if prefixed
    if query.startswith(("ai:", "ask:")):
        if Config.AI_ENABLED and getattr(Config, "AI_INLINE_MODE_ENABLED", True):
            # Extract AI query and remove prefix
            if query.startswith("ai:"):
                modified_query = query[3:].strip()
            elif query.startswith("ask:"):
                modified_query = query[4:].strip()

            # Create modified inline query for AI handler
            modified_inline_query = ModifiedInlineQuery(inline_query, modified_query)

            # Import and call AI inline handler
            try:
                from bot.modules.ai import AIENT_AVAILABLE, handle_ai_inline_query

                if not AIENT_AVAILABLE:
                    await show_ai_unavailable_error(inline_query, "AI dependencies not available")
                    return

                await handle_ai_inline_query(client, modified_inline_query)
                return
            except Exception as e:
                LOGGER.error(f"AI inline handler error: {e}")
                await show_ai_error(inline_query, str(e))
                return

        # AI disabled, show error
        from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
        await inline_query.answer(
            results=[
                InlineQueryResultArticle(
                    id="ai_disabled",
                    title="❌ AI Assistant Disabled",
                    description="AI Assistant is currently disabled",
                    input_message_content=InputTextMessageContent(
                        "❌ **AI Assistant Disabled**\n\nAI Assistant is currently disabled."
                    ),
                )
            ],
            cache_time=60,
        )
        return

    # If AI is enabled, route to AI directly if no prefix
    if Config.AI_ENABLED and getattr(Config, "AI_INLINE_MODE_ENABLED", True):
        try:
            from bot.modules.ai import AIENT_AVAILABLE, handle_ai_inline_query
            if AIENT_AVAILABLE:
                await handle_ai_inline_query(client, inline_query)
                return
        except Exception as e:
            LOGGER.error(f"AI inline handler error: {e}")
            # Fallback to help if AI fails

    # Default: Show help
    await show_search_help(inline_query)


async def show_ai_unavailable_error(inline_query: InlineQuery, error_msg: str):
    """Show AI unavailable error in inline mode."""
    from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id="ai_unavailable",
                title="❌ AI Assistant Unavailable",
                description=error_msg,
                input_message_content=InputTextMessageContent(
                    f"❌ **AI Assistant Unavailable**\n\n{error_msg}"
                ),
            )
        ],
        cache_time=60,
    )


async def show_ai_error(inline_query: InlineQuery, error_msg: str):
    """Show AI error in inline mode."""
    from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id="ai_error",
                title="⚠️ AI Assistant Error",
                description="An error occurred while processing your request",
                input_message_content=InputTextMessageContent(
                    f"⚠️ **AI Assistant Error**\n\n<code>{error_msg}</code>"
                ),
            )
        ],
        cache_time=30,
    )


async def show_search_help(inline_query: InlineQuery):
    """Show help information for AI assistant"""
    from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

    help_text = "🤖 <b>AI Assistant Inline Help</b>\n\n"

    if Config.AI_ENABLED and getattr(Config, "AI_INLINE_MODE_ENABLED", True):
        help_text += (
            "🤖 <b>AI Assistant:</b>\n"
            "<code>@bot_username ai:your question</code>\n"
            "<code>@bot_username ask:your question</code>\n"
            "<code>@bot_username your question</code>\n\n"
            "Examples:\n"
            "• <code>@bot_username ai:What is Python?</code>\n"
            "• <code>@bot_username ask:Write a function to sort a list</code>\n"
        )
    else:
        help_text += "❌ AI assistant is currently disabled."

    await inline_query.answer(
        results=[
            InlineQueryResultArticle(
                id="help",
                title="🤖 AI Assistant Help",
                description="Learn how to use the AI assistant",
                input_message_content=InputTextMessageContent(help_text),
            )
        ],
        cache_time=300,
    )


def init_unified_inline_search(bot):
    """Initialize the unified inline search handler."""
    from pyrogram.handlers import InlineQueryHandler

    async def safe_unified_inline_search_handler(client, inline_query: InlineQuery):
        try:
            await unified_inline_search_handler(client, inline_query)
        except Exception as e:
            LOGGER.error(f"Error in unified inline search handler: {e}")

    bot.add_handler(InlineQueryHandler(safe_unified_inline_search_handler))
    LOGGER.info("Unified inline search handler initialized successfully")
