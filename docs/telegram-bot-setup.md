# Creating a Telegram Bot

Synapse needs a bot account and a token before it can run. Telegram bots are created and managed through **@BotFather**, an official Telegram bot.

## 1. Talk to BotFather

1. Open Telegram and search for `@BotFather` (verified, blue checkmark).
2. Start a chat and send:
   ```
   /newbot
   ```
3. BotFather will ask for a **display name** - this is what shows up in chats (e.g. `Synapse`). Can be changed later.
4. BotFather will then ask for a **username** - must be unique across all of Telegram and must end in `bot` (e.g. `SynapseAIBot` or `synapse_ai_bot`).

## 2. Save the token

Once created, BotFather replies with a message containing a line like:

```
Use this token to access the HTTP API:
123456789:AAExampleTokenStringGoesHere
```

Copy that whole string. This is your `TELEGRAM_TOKEN`.

> **Treat this token like a password.** Anyone with it can control your bot. Never commit it to git - it belongs in `.env`, which is already covered by `.gitignore`.

## 3. Fill in `.env`

From the project root:

```bash
cp .env.example .env
```

Then open `.env` and set:

```env
TELEGRAM_TOKEN=123456789:AAExampleTokenStringGoesHere
BOT_USERNAME=SynapseAIBot
```

`BOT_USERNAME` should match the username you gave BotFather in step 1 (without the `@`). Synapse uses this to detect when someone `@mentions` it in a group.

## 4. (Optional) Bot settings via BotFather

Still inside the BotFather chat, you can further configure your bot:

- `/setdescription` - shown on the bot's profile page before anyone starts a chat
- `/setabouttext` - shorter blurb shown in shared profiles
- `/setuserpic` - upload a profile picture
- `/setjoingroups` - make sure this is **Enabled** so the bot can be added to groups at all
- `/setprivacy` - **must be Disabled** for Synapse to work correctly. By default, Telegram bots in group chats only receive messages that start with `/` or that directly `@mention` them. Synapse relies on seeing all group messages (to build conversation context and detect `@mentions` anywhere in a message), so privacy mode has to be turned off.

To disable privacy mode:
```
/setprivacy
```
 select your bot  choose **Disable**.

> If you skip this step, Synapse will still start and run, but it'll appear to "ignore" most messages - it'll only ever see commands and messages that begin with the mention, not messages that mention it mid-sentence or messages from other users used for context.

## Next step

Once the bot exists and the token is in `.env`, you'll need the numeric ID of the group you want Synapse to operate in - covered in `docs/telegram-group-chat-id.md`.
