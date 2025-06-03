import asyncio
import os
import logging
from datetime import datetime
from aiohttp import web
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from plugins import web_server
from config import *
from database.database import db

name = "『A N I M E _ L O R D』"

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TW_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = logger

    async def start(self):
        session_file = "Bot.session"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                self.LOGGER.info("Removed old session file")
            except Exception as e:
                self.LOGGER.error(f"Failed to remove session file: {e}")

        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        invalid_channels = await db.validate_channels(self)
        if invalid_channels:
            try:
                await self.send_message(
                    chat_id=OWNER_ID,
                    text=f"🚨 Removed {len(invalid_channels)} invalid channels from force-sub list: {invalid_channels}"
                )
            except Exception as e:
                self.LOGGER.error(f"Failed to notify owner about invalid channels: {e}")

        global PROTECT_CONTENT, HIDE_CAPTION, DISABLE_CHANNEL_BUTTON, BUTTON_NAME, BUTTON_LINK
        settings = await db.get_settings()
        PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)
        HIDE_CAPTION = settings.get('HIDE_CAPTION', False)
        DISABLE_CHANNEL_BUTTON = settings.get('DISABLE_CHANNEL_BUTTON', True)
        BUTTON_NAME = settings.get('BUTTON_NAME', None)
        BUTTON_LINK = settings.get('BUTTON_LINK', None)

        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER.error(f"Error accessing DB channel: {e}")
            self.LOGGER.info(f"Bot stopped. Ensure bot is admin in DB channel and CHANNEL_ID ({CHANNEL_ID}) is correct.")
            self.LOGGER.info("Join https://t.me/Anime_Lord_Support for support")
            sys.exit(1)

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER.info(
            f"Bot is alive!\n\nCreated by AnimeLord-Bots\n"
            f"Deployed by @who-am-i\n"
            f"Bot: @{usr_bot_me.username}\n"
            f"{'-'*50}\n"
            f"|{' '*20}『A N I M E  L O R D』{' '*20}|\n"
            f"{'-'*80}\n"
            f"🔥 I AM ALIVE 🔥\n"
            f"Accessing... █████ 100%"
        )
        self.username = usr_bot_me.username

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        try:
            await self.send_message(OWNER_ID, "<b>Bot restarted by @AnimeLord_Bots</b>")
        except Exception as e:
            self.LOGGER.error(f"Failed to send startup message to OWNER_ID: {e}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER.info("Bot stopped.")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
