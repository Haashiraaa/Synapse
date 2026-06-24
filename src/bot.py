import os
import logging
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor
from anthropic import Anthropic
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
BOT_USERNAME = os.getenv("BOT_USERNAME")  # e.g. @YourBotName
MESSAGE_WINDOW = int(os.getenv("MESSAGE_WINDOW", 20))  # sliding window size

anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a collaborative AI assistant embedded in a team group chat.
The team uses you to brainstorm, get answers, and work through ideas together.
Messages will be prefixed with the sender's name so you know who said what.
Be concise and direct. When writing code, use plain code blocks since this is Telegram.
Address people by name when relevant."""


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT UNIQUE NOT NULL,
                    summary TEXT DEFAULT '',
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    user_name TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_messages_chat_id
                    ON messages (chat_id, created_at DESC);
            """)
        conn.commit()
    logger.info("DB initialised")


def get_or_create_conversation(chat_id: int) -> dict:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM conversations WHERE chat_id = %s", (chat_id,)
            )
            row = cur.fetchone()
            if row:
                return dict(row)

            cur.execute(
                "INSERT INTO conversations (chat_id) VALUES (%s) RETURNING *",
                (chat_id,),
            )
            conn.commit()
            return dict(cur.fetchone())


def save_message(chat_id: int, role: str, content: str, user_name: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO messages (chat_id, role, content, user_name)
                   VALUES (%s, %s, %s, %s)""",
                (chat_id, role, content, user_name),
            )
        conn.commit()


def get_recent_messages(chat_id: int, limit: int = MESSAGE_WINDOW) -> list[dict]:
    """Returns messages oldest-first for the context window."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT role, content, user_name, created_at
                   FROM messages
                   WHERE chat_id = %s
                   ORDER BY created_at DESC
                   LIMIT %s""",
                (chat_id, limit),
            )
            rows = cur.fetchall()
    return list(reversed(rows))  # flip to chronological


def get_message_count(chat_id: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE chat_id = %s",
                (chat_id,),
            )
            return cur.fetchone()["cnt"]


def save_summary(chat_id: int, summary: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE conversations
                   SET summary = %s, updated_at = NOW()
                   WHERE chat_id = %s""",
                (summary, chat_id),
            )
        conn.commit()


def prune_old_messages(chat_id: int, keep: int = MESSAGE_WINDOW):
    """Delete everything except the most recent `keep` messages."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """DELETE FROM messages
                   WHERE chat_id = %s
                     AND id NOT IN (
                         SELECT id FROM messages
                         WHERE chat_id = %s
                         ORDER BY created_at DESC
                         LIMIT %s
                     )""",
                (chat_id, chat_id, keep),
            )
        conn.commit()


# ── Summarisation ─────────────────────────────────────────────────────────────

def summarise_conversation(chat_id: int):
    """Call Claude to summarise the current window, store it, prune rows."""
    convo = get_or_create_conversation(chat_id)
    recent = get_recent_messages(chat_id, limit=MESSAGE_WINDOW)

    if not recent:
        return

    history_text = "\n".join(
        f"{m['user_name'] or m['role']}: {m['content']}" for m in recent
    )

    prev_summary = convo.get("summary", "")
    prompt = (
        f"Previous summary:\n{prev_summary}\n\n"
        f"New messages:\n{history_text}\n\n"
        "Write a concise summary (max 300 words) of the entire conversation so far, "
        "capturing key decisions, code snippets discussed, open questions, and who said what."
    )

    response = anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    new_summary = response.content[0].text
    save_summary(chat_id, new_summary)
    prune_old_messages(chat_id, keep=MESSAGE_WINDOW)
    logger.info(f"Summarised and pruned chat {chat_id}")


# ── Build Claude context ──────────────────────────────────────────────────────

def build_messages(chat_id: int) -> list[dict]:
    convo = get_or_create_conversation(chat_id)
    recent = get_recent_messages(chat_id)

    messages = []

    # inject summary as the first user turn if it exists
    summary = convo.get("summary", "").strip()
    if summary:
        messages.append({
            "role": "user",
            "content": f"[Conversation summary so far]\n{summary}",
        })
        messages.append({
            "role": "assistant",
            "content": "Got it, I have context from the earlier conversation.",
        })

    for m in recent:
        if m["role"] == "user":
            prefix = f"{m['user_name']}: " if m["user_name"] else ""
            messages.append({"role": "user", "content": prefix + m["content"]})
        else:
            messages.append({"role": "assistant", "content": m["content"]})

    return messages


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    get_or_create_conversation(chat_id)
    await update.message.reply_text(
        "👋 Claude is in the chat. @mention me to ask anything.\n"
        f"I remember the last {MESSAGE_WINDOW} messages and summarise older ones automatically."
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
    clean_text = text.replace(mention, "").replace(mention.lower(), "").strip()
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


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual /summary command — useful for pinning context."""
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    summarise_conversation(chat_id)
    convo = get_or_create_conversation(chat_id)
    summary = convo.get("summary", "No summary yet.")
    await update.message.reply_text(f"📋 *Conversation Summary*\n\n{summary}", parse_mode="Markdown")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wipe history and summary — fresh start."""
    chat_id = update.effective_chat.id
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))
            cur.execute(
                "UPDATE conversations SET summary = '' WHERE chat_id = %s", (chat_id,)
            )
        conn.commit()
    await update.message.reply_text("🗑️ History cleared. Fresh start.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    init_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
