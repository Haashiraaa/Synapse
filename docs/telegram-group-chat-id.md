# Finding Your Group's Chat ID

Synapse is restricted to a set of groups via `ALLOWED_CHAT_IDS` in `.env` (checked in `src/telegram/decorators.py`'s `@restricted` decorator). This doc covers how to find a group's numeric ID — repeat the process below for each group you want Synapse to run in.


> Requires a bot token already set up - see `docs/telegram-bot-setup.md` first if you haven't done that yet.

## 1. Add the bot to your group

1. Open the Telegram group you want Synapse to run in (do this once per group).
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

If this is your only group:

```env
ALLOWED_CHAT_IDS=-1001234567890
```

+If you have multiple groups, repeat steps 1-3 for each one, then comma-separate all the chat_ids:
+
+```env
+ALLOWED_CHAT_IDS=-1001234567890,-1009876543210
+```
+
+> **Check the variable name carefully.** `src/config/settings.py` reads `ALLOWED_CHAT_IDS` (plural). If you're upgrading from an older version of Synapse, your `.env` may still say `ALLOWED_CHAT_ID` (singular) - rename it, or the bot will fail to start with a missing-required-variable error rather than silently misbehaving.

## Troubleshooting: empty `"result": []`

If `getUpdates` returns an empty result array, it usually means one of:

- **No new messages since the bot last polled.** Telegram's `getUpdates` only returns updates it hasn't delivered yet. If Synapse (or any prior test) already ran and consumed the update, send a fresh message in the group and reload the URL.
- **Privacy mode is still enabled.** Go back to BotFather and confirm `/setprivacy`  Disable was actually applied.
- **The bot isn't actually in the group**, or was removed/re-added after the message was sent.

## Next step

With `TELEGRAM_TOKEN`, `BOT_USERNAME`, and `ALLOWED_CHAT_ID` all set in `.env`, along with `ANTHROPIC_API_KEY` and `DATABASE_URL`, Synapse has everything it needs to start.

## Upgrading from a single-group setup

Versions prior to 0.4.0 used a single `ALLOWED_CHAT_ID` variable. If you're upgrading:

1. Rename `ALLOWED_CHAT_ID` to `ALLOWED_CHAT_IDS` in your `.env`.
2. The value itself doesn't need to change if you're staying single-group — just wrap it under the new name.
3. To add more groups, follow steps 1-4 above for each new group and append its chat_id to the comma-separated list.

The bot will refuse to start (not silently misbehave) if `ALLOWED_CHAT_IDS` is missing, so you'll know immediately if you forgot this step.
