

# src/telegram/handlers.py

from src.db.queries import DbQueries
from src.config.settings import Settings
from src.ai.claude.client import Claude
from telegram import Update
from telegram.ext import ContextTypes


class BotHandlers:

    def __init__(self) -> None:
        self.db = DbQueries()
        self.claude = Claude()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        self.db.get_or_create_conversation(chat_id)
        await update.message.reply_text(
            "👋 Claude is in the chat. @mention me to ask anything.\n"
            f"I remember the last {Settings.MESSAGE_WINDOW} messages and summarise older ones automatically."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text:
            return

        assert update.effective_chat
        assert message.from_user
        chat_id = update.effective_chat.id
        user = message.from_user
        user_name = user.username or user.first_name or "Someone"
        text = message.text

        bot_username = Settings.BOT_USERNAME or (await context.bot.get_me()).username
        mention = f"@{bot_username}"

        if mention.lower() not in text.lower():
            self.db.save_message(chat_id, "user", text, user_name)
            count = self.db.get_message_count(chat_id)
            if count > 0 and count % Settings.MESSAGE_WINDOW == 0:
                summary = self.claude.summarise(chat_id)
                self.db.save_summary(chat_id, summary)
                self.db.prune_old_messages(chat_id)
            return

        clean_text = text.replace(mention, "").replace(
            mention.lower(), "").strip()
        if not clean_text:
            await message.reply_text("Yeah? Ask me something 👀")
            return

        self.db.save_message(chat_id, "user", clean_text, user_name)
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        try:
            reply = self.claude.get_reply(chat_id)
        except Exception as e:
            await message.reply_text("⚠️ Something went wrong calling Claude. Try again.")
            return

        self.db.save_message(chat_id, "assistant", reply)
        await message.reply_text(reply)

    async def cmd_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        summary = self.claude.summarise(chat_id)
        self.db.save_summary(chat_id, summary)
        await update.message.reply_text(
            f"📋 *Conversation Summary*\n\n{summary}", parse_mode="Markdown"
        )

    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        self.db.clear_history(chat_id)
        self.db.save_summary(chat_id, "")
        await update.message.reply_text("🗑️ History cleared. Fresh start.")
