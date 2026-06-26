

# src/telegram/handlers.py

from src.db.queries import DbQueries
from src.config.settings import Settings
from src.ai.claude.client import Claude
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


class BotHandlers:

    def __init__(self) -> None:
        self.db = DbQueries()
        self.settings = Settings()
        self.claude = Claude()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        assert update.effective_chat
        chat_id = update.effective_chat.id
        self.db.get_or_create_conversation(chat_id)

        assert update.message
        await update.message.reply_text(
            "👋 Claude is in the chat. @mention me to ask anything.\n"
            f"I remember the last {self.settings.MESSAGE_WINDOW} messages and summarise older ones automatically."
        )

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text:
            return

        chat_id = update.effective_chat.id
        user = message.from_user
        user_name = user.username or user.first_name or "Someone"
        text = message.text

        # only respond when @mentioned
        bot_username = BOT_USERNAME or (await context.bot.get_me()).username
        mention = f"@{bot_username}"

        if mention.lower() not in text.lower():
            # still save the message to keep conversation context
            save_message(chat_id, "user", text, user_name)

            # auto-summarise every MESSAGE_WINDOW user messages
            count = get_message_count(chat_id)
            if count > 0 and count % MESSAGE_WINDOW == 0:
                summarise_conversation(chat_id)
            return

        # strip the mention from the text before saving/sending
        clean_text = text.replace(mention, "").replace(
            mention.lower(), "").strip()
        if not clean_text:
            await message.reply_text("Yeah? Ask me something 👀")
            return

        save_message(chat_id, "user", clean_text, user_name)

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        messages = build_messages(chat_id)

        try:
            response = anthropic.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            reply = response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
            await message.reply_text("⚠️ Something went wrong calling Claude. Try again.")
            return

        save_message(chat_id, "assistant", reply)
        await message.reply_text(reply)

    async def cmd_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manual /summary command — useful for pinning context."""

        assert update.effective_chat
        chat_id = update.effective_chat.id

        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        summary = self.claude.summarise(chat_id)
        assert update.message
        await update.message.reply_text(f"📋 *Conversation Summary*\n\n{summary}", parse_mode="Markdown")

    async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Wipe history and summary — fresh start."""
        chat_id = update.effective_chat.id
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM messages WHERE chat_id = %s", (chat_id,))
                cur.execute(
                    "UPDATE conversations SET summary = '' WHERE chat_id = %s", (
                        chat_id,)
                )
            conn.commit()
        await update.message.reply_text("🗑️ History cleared. Fresh start.")
