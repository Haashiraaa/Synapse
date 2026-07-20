

# src/main/teams.py

import sys
import traceback

from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity

from src.config.settings import Settings
from src.db.connection import DbConnection
from src.platforms.teams.bot import SynapseTeamsBot

SETTINGS = BotFrameworkAdapterSettings(
    app_id=Settings.MICROSOFT_APP_ID,
    app_password=Settings.MICROSOFT_APP_PASSWORD,
)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = SynapseTeamsBot()


async def _on_error(context: TurnContext, error: Exception) -> None:
    print(f"[on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()
    await context.send_activity("⚠️ Something went wrong. Try again.")


ADAPTER.on_turn_error = _on_error


async def messages(req: Request) -> Response:
    if "application/json" not in req.headers.get("Content-Type", ""):
        return Response(status=415)

    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return Response(status=response.status, body=response.body)
    return Response(status=201)


async def health(req: Request) -> Response:
    return Response(status=200, text="ok")


def main() -> None:
    if not Settings.MICROSOFT_APP_ID or not Settings.MICROSOFT_APP_PASSWORD:
        print(
            "⚠️  MICROSOFT_APP_ID / MICROSOFT_APP_PASSWORD not set — "
            "fine for Bot Framework Emulator testing, but real Teams "
            "deployment will reject unauthenticated traffic.",
            file=sys.stderr,
        )

    import logging

    from haashi_pkg.utility import Logger

    logger = Logger(level=logging.INFO)
    DbConnection.init_db(logger)

    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_get("/health", health)

    web.run_app(app, host="0.0.0.0", port=3978)


if __name__ == "__main__":
    main()
