

# src/telegram/handlers.py

from src.db.queries import DbQueries
from src.config.settings import Settings
from src.ai.base import BaseAIClient
from src.ai.factory import get_ai_client
from telegram import Update
from telegram.ext import ContextTypes

# pyright: reportPrivateUsage=false


class BotHandlers:

    def __init__(self) -> None:
        self.db = DbQueries()
        self.ai: BaseAIClient = get_ai_client()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        self.db.get_or_create_conversation(chat_id)
        await update.message.reply_text(
            "👋 Claude is in the chat. @mention me to ask anything.\n"
            f"I remember the last {Settings.MESSAGE_WINDOW} messages and summarise older ones automatically."
        )

    async def cmd_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        summary = self.ai.summarise(chat_id)
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

    async def cmd_switch_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        if not context.args:
            await update.message.reply_text("Usage: /switchmodel sonnet | haiku")
            return

        model = context.args[0].lower()
        if model not in ["sonnet", "haiku"]:
            await update.message.reply_text("❌ Unknown model. Choose: sonnet or haiku")
            return

        self.ai._MODEL = self.ai.get_model(model)
        await update.message.reply_text(f"✅ Switched to `{self.ai._MODEL}`", parse_mode="Markdown")

    async def cmd_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        await update.message.reply_text(f"🤖 Current model: `{self.ai._MODEL}`", parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not message.text:
            return

        assert update.effective_chat
        assert message.from_user
        chat_id = update.effective_chat.id
        # print(f"CHAT ID: {chat_id}")
        user = message.from_user
        user_name = user.username or user.first_name or "Someone"
        text = message.text

        bot_username = Settings.BOT_USERNAME or (await context.bot.get_me()).username
        mention = f"@{bot_username}"

        if mention.lower() not in text.lower():
            self.db.save_message(chat_id, "user", text, user_name)
            count = self.db.get_message_count(chat_id)
            if count > 0 and count % Settings.MESSAGE_WINDOW == 0:
                summary = self.ai.summarise(chat_id)
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

        reply = self.ai.get_reply(chat_id)

        self.db.save_message(chat_id, "assistant", reply)
        await message.reply_text(reply)
