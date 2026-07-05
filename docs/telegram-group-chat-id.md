# Finding Your Group's Chat ID

Synapse is restricted to a single group via `ALLOWED_CHAT_ID` in `.env` (checked in `src/telegram/decorators.py`'s `@restricted` decorator). This doc covers how to find that numeric ID.

> Requires a bot token already set up - see `docs/telegram-bot-setup.md` first if you haven't done that yet.

## 1. Add the bot to your group

1. Open the Telegram group you want Synapse to run in.
2. Add your bot the same way you'd add any member (group settings  Add Members  search your bot's username).
3. Make sure `/setprivacy` was disabled in BotFather (see the bot-setup doc) - otherwise the bot may not receive the message you're about to send.

## 2. Send any message in the group

Send literally anything in the group chat - even just `hi`. This gives Telegram something to report back when you query updates in the next step.

## 3. Call `getUpdates`

Open this URL in your browser, replacing `<TELEGRAM_TOKEN>` with your actual token:

```
https://api.telegram.org/bot<TELEGRAM_TOKEN>/getUpdates
```

For example, if your token is `123456789:AAExampleTokenStringGoesHere`:

```
https://api.telegram.org/bot123456789:AAExampleTokenStringGoesHere/getUpdates
```

This returns a JSON response. Look for a `"chat"` object inside `"message"`:

```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "message_id": 42,
        "from": { "id": 987654321, "first_name": "Haashiraaa" },
        "chat": {
          "id": -1001234567890,
          "title": "Your Group Name",
          "type": "supergroup"
        },
        "date": 1234567890,
        "text": "hi"
      }
    }
  ]
}
```

The number you want is `"chat"."id"` - in this example, `-1001234567890`.

## Important: group chat IDs are negative

Group and supergroup chat IDs are always **negative numbers** (private one-on-one chats with a user are positive). Supergroups often have a long `-100...` prefix, like the example above. This is normal - copy it exactly as shown, including the minus sign.

## 4. Set it in `.env`

```env
ALLOWED_CHAT_ID=-1001234567890
```

> **Check the variable name carefully.** `src/config/settings.py` reads `ALLOWED_CHAT_ID`. If `.env.example` in your copy still says `GROUP_CHAT_ID`, rename it to `ALLOWED_CHAT_ID` - otherwise the value is silently ignored, `Settings.ALLOWED_CHAT_ID` defaults to `0`, and the bot won't respond in any group at all.

## Troubleshooting: empty `"result": []`

If `getUpdates` returns an empty result array, it usually means one of:

- **No new messages since the bot last polled.** Telegram's `getUpdates` only returns updates it hasn't delivered yet. If Synapse (or any prior test) already ran and consumed the update, send a fresh message in the group and reload the URL.
- **Privacy mode is still enabled.** Go back to BotFather and confirm `/setprivacy`  Disable was actually applied.
- **The bot isn't actually in the group**, or was removed/re-added after the message was sent.

## Next step

With `TELEGRAM_TOKEN`, `BOT_USERNAME`, and `ALLOWED_CHAT_ID` all set in `.env`, along with `ANTHROPIC_API_KEY` and `DATABASE_URL`, Synapse has everything it needs to start.
