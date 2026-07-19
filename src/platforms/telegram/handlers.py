# src/telegram/handlers.py


from telegram.ext import ContextTypes

from src.ai.base import BaseAIClient
from src.ai.factory import get_ai_client
from src.config.settings import Settings
from src.db.queries import DbQueries
from src.platforms.telegram.decorators import restricted
from src.platforms.telegram.media import MediaProcessor
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

# pyright: reportPrivateUsage=false


class BotHandlers:

    def __init__(self) -> None:
        self.db = DbQueries()
        self.ai: BaseAIClient = get_ai_client()
        self.media = MediaProcessor()

    # ── Internal helpers ────────────────────────────────────────

    def _maybe_summarize(self, chat_id: int) -> None:
        """Check message count and summarize/prune if window threshold is reached."""
        count = self.db.get_message_count(chat_id)
        if count >= Settings.MESSAGE_WINDOW:
            summary = self.ai.summarise(chat_id)
            self.db.save_summary(chat_id, summary)
            self.db.prune_old_messages(
                chat_id, keep=Settings.MESSAGE_WINDOW // 2)

    @restricted
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        chat_id = update.effective_chat.id
        self.db.get_or_create_conversation(chat_id)
        await update.message.reply_text(
            "Hey, I'm Synapse — an AI assistant built on Claude, here to be part of this chat.\n\n"
            f"Mention me (@{Settings.BOT_USERNAME}) with a question and I'll reply. "
            f"I keep track of the last {Settings.MESSAGE_WINDOW} messages and summarise older ones "
            "automatically, so I don't lose the thread of long conversations.\n\n"
            "Commands:\n"
            "/summary — see a summary of the conversation so far\n"
            "/clear — wipe stored history and start fresh\n"
            "/model — check which Claude model I'm currently using\n"
            "/switchmodel sonnet|haiku — switch models on the fly\n\n"
            "I can also read images, PDFs, diffs (.diff/.patch), and Word docs — "
            "just mention me (or reply to me) with one attached."
        )

    @restricted
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

    @restricted
    async def cmd_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat
        assert update.message
        assert update.effective_user
        user_id = update.effective_user.id

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Yes, clear it", callback_data=f"clear:confirm:{user_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel", callback_data=f"clear:cancel:{user_id}"),
                ]
            ]
        )
        await update.message.reply_text(
            "⚠️ This will permanently wipe stored history and the summary for this chat. Sure?",
            reply_markup=keyboard,
        )

    @restricted
    async def cb_clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        assert query and query.data
        assert update.effective_chat
        chat_id = update.effective_chat.id

        _, action, requester_id = query.data.split(":")

        if query.from_user.id != int(requester_id):
            await query.answer("Only the person who ran /clear can confirm this.", show_alert=True)
            return

        await query.answer()

        if action == "cancel":
            await query.edit_message_text("Cancelled — history left untouched.")
            return

        self.db.clear_history(chat_id)
        self.db.save_summary(chat_id, "")
        await query.edit_message_text("🗑️ History cleared. Fresh start.")

    @restricted
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

    @restricted
    async def cmd_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        await update.message.reply_text(
            f"🤖 Current model: `{self.ai._MODEL}`", parse_mode="Markdown"
        )

    # ── Messages & media ────────────────────────────────────────

    @restricted
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
            self._maybe_summarize(chat_id)
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
        self._maybe_summarize(chat_id)
        await message.reply_text(reply)

    @restricted
    async def handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message
        if not message or not (message.photo or message.document):
            return

        assert update.effective_chat
        assert message.from_user
        chat_id = update.effective_chat.id
        user = message.from_user
        user_name = user.username or user.first_name or "Someone"
        caption = message.caption or ""

        bot_username = Settings.BOT_USERNAME or (await context.bot.get_me()).username
        mention = f"@{bot_username}"
        replied_to_bot = (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.username == bot_username
        )
        if mention.lower() not in caption.lower() and not replied_to_bot:
            return

        clean_caption = caption.replace(
            mention, "").replace(mention.lower(), "").strip()

        if message.photo:
            file = await message.photo[-1].get_file()
            mime_type, filename = "image/jpeg", None
        else:
            doc = message.document
            assert doc is not None
            file = await doc.get_file()
            mime_type, filename = doc.mime_type, doc.file_name

        if not self.media.supports(mime_type, filename):
            await message.reply_text(
                "I can only read images, PDFs, diffs, and docx files right now 🙃"
            )
            return

        raw = bytes(await file.download_as_bytearray())
        outcome = self.media.process(raw, mime_type, filename, clean_caption)

        self.db.save_message(chat_id, "user", outcome.placeholder, user_name)
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        if outcome.media_block:
            reply = self.ai.get_reply(
                chat_id, media=[outcome.media_block], caption=clean_caption)
        else:
            # diff already lives in messages.content
            reply = self.ai.get_reply(chat_id)

        self.db.save_message(chat_id, "assistant", reply)
        self._maybe_summarize(chat_id)
        await message.reply_text(reply)
