
# Synapse

Synapse is a free, open-source Telegram bot that brings Claude into one or more group chats as a participant, not a command-line tool. It remembers the conversation, summarizes older history automatically, and can read images, PDFs, diffs, and Word docs shared in the group.

## Features

 - **Claude-powered replies** via the Anthropic API, mentioned like any other member of the group (`@YourBot ...`)
 - **Persistent conversation memory** backed by PostgreSQL, with a sliding context window that auto-summarizes older messages instead of losing them
 - **Multi-group access control** - the bot only responds in the group(s) listed in `ALLOWED_CHAT_IDS`, each with its own independent conversation history and summary
 - **Runtime model switching** between Claude models via `/switchmodel`, without restarting the bot
 - **Image, PDF, diff, and docx support** - send a photo or document and mention the bot (or reply to it) to ask about it
 - **Graceful shutdown notifications** in the group when the bot is stopped or redeployed
 - **Optional email alerts** on bot start, stop, and error, via Gmail SMTP
 - **Swappable AI provider architecture** - Claude is implemented today; other providers can be added behind the same interface

## Multi-group behavior

Synapse can run in multiple groups simultaneously. Each group's conversation history, rolling summary, and message window are tracked independently by `chat_id` — activity in one group never bleeds into another. Startup/shutdown notifications are sent to every group listed in `ALLOWED_CHAT_IDS`.

## Requirements

- Python 3.10+
- A PostgreSQL database (local or hosted)
- A Telegram bot token
- An Anthropic API key

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Haashiraaa/Synapse.git
cd Synapse
pip install -e ".[dev]"
```

### 2. Create your bot and get your group's chat ID

Two guides walk through this:

- [`docs/telegram-bot-setup.md`](docs/telegram-bot-setup.md) - creating a bot via BotFather, getting the token, disabling privacy mode
- [`docs/telegram-group-chat-id.md`](docs/telegram-group-chat-id.md) - finding your group's numeric chat ID via `getUpdates`

### 3. Configure environment variables

```bash
cp .env.example .env
```

Then fill in `.env`:

 | Variable | Required | Description |
 |---|---|---|
 | `TELEGRAM_TOKEN` | Yes | From BotFather |
 | `BOT_USERNAME` | Yes | Your bot's username, without `@` | 
 | `ALLOWED_CHAT_IDS` | Yes | Comma-separated list of group chat_ids this bot will respond in (negative numbers), e.g. `-1001234567890,-1009876543210` |
 | `ANTHROPIC_API_KEY` | Yes | From the Anthropic Console |
 | `DATABASE_URL` | Yes | PostgreSQL connection string |
 | `AI_PROVIDER` | No | Defaults to `claude` - only provider implemented currently |
 | `MESSAGE_WINDOW` | No | Messages kept before auto-summarizing (default: 8) |
 | `ALERT_EMAIL_FROM` / `ALERT_EMAIL_TO` / `ALERT_EMAIL_PASSWORD` | No | Enables email alerts on start/stop/error if all three are set |

### 4. Run it

```bash
synapse
```

(Or `python3 -m app` if you haven't installed the package.)

## Commands

 | Command | Description |
 |---|---| 
 | `/start` | Initializes the conversation record for this group |
 | `/summary` | Generates and displays a summary of the current conversation |
 | `/clear` | Wipes stored history and summary for this group (asks for confirmation first) |
 | `/model` | Shows the currently active Claude model |
 | `/switchmodel sonnet\|haiku` | Switches the active model at runtime |

## Supported media

Mention the bot (or reply to it) with one of the following attached:

- **Images** (jpeg, png, webp, gif) - sent through Claude's vision pipeline
- **PDFs** - sent through Claude's document pipeline
- **Diffs / patches** (`.diff`, `.patch`) - decoded as text and persisted in conversation history, capped at 50 KB
- **Word documents** (`.docx`) - text and table content extracted via `python-docx`, capped at 20,000 characters

## Project structure

```
app/                  entry point (python -m app)
src/
  ai/                 provider-agnostic AI interface, Claude implementation, prompt
  config/             environment-driven settings
  db/                 PostgreSQL connection and queries
  loggers/            optional email alerting
  telegram/           command/message handlers, access control decorator, media processing
  exceptions/         custom error types
docs/                 setup guides
```

## Versioning and releases

Synapse follows [Semantic Versioning](https://semver.org/). Releases are cut automatically: bumping `version` in `pyproject.toml` and pushing to `main` triggers a GitHub Actions workflow that tags the commit, generates release notes from commit history, and publishes a GitHub Release. See `CHANGELOG.md` for the full history.

## License

MIT
