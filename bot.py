#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

from aiohttp import web
from plugins import web_server
import asyncio
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
#ᴀɴɪᴍᴇ ʟᴏʀᴅ
from config import *
from database.database import db  # Updated import

name = """『A N I M E _ L O R D』"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Load settings from database
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
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴅʙ ᴄʜᴀɴɴᴇʟ, ᴀɴᴅ ᴅᴏᴜʙʟᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ_ɪᴅ ᴠᴀʟᴜᴇ, ᴄᴜʀʀᴇɴᴛ ᴠᴀʟᴜᴇ {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nʙᴏᴛ sᴛᴏᴘᴘᴇᴅ. ᴊᴏɪɴ https://t.me/+3lpawaYvxBU4YTY1 ғᴏʀ sᴜᴘᴘᴏʀᴛ")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"ʙᴏᴛ ɪs ᴀʟɪᴠᴇ..!\n\nᴄʀᴇᴀᴛᴇᴅ ʙʏ \n 『ᴀɴɪᴍᴇ-ʟᴏʀᴅ-ʙᴏᴛ』")
        self.LOGGER(__name__).info(f"ʙᴏᴛ ᴅᴇᴘʟᴏʏᴇᴅ ʙʏ @ᴡʜᴏ-ᴀᴍ-ɪ")
        self.set_parse_mode(ParseMode.HTML)
        self.username = usr_bot_me.username
        self.LOGGER(__name__).info(f"ʙᴏᴛ ɪs ᴀʟɪᴠᴇ..! ᴍᴀᴅᴇ ʙʏ @ᴀɴɪᴍᴇ ʟᴏʀᴅ")   

        # sᴛᴀʀᴛ ᴡᴇʙ sᴇʀᴠᴇʀ
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        try:
            await self.send_message(OWNER_ID, text=f"<b><blockquote>ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ʙʏ @ᴀɴɪᴍᴇ_ʟᴏʀᴅ_ʙᴏᴛ\n\n<code>{name}</code></blockquote></b>")
        except Exception as e:
            self.LOGGER(__name__).warning(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ sᴛᴀʀᴛᴜᴘ ᴍᴇssᴀɢᴇ ᴛᴏ OWNER_ID: {str(e)}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("ʙᴏᴛ sᴛᴏᴘᴘᴇᴅ.")

    def run(self):
        """Run the bot."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.start())
        self.LOGGER(__name__).info(f"ʙᴏᴛ ɪs ɴᴏᴡ ᴀʟɪᴠᴇ. ᴛʜᴀɴᴋs ᴛᴏ @ᴡʜᴏ-ᴀᴍ-ɪ")
        self.LOGGER(__name__).info(f"""
▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄
|------------------『A N I M E  L O R D』----------------------|
▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀
               ◈◈◈◈◈◈ ɪ_s_ᴀ_ʟ_ɪ_ᴠ_ᴇ ◈◈◈◈◈◈  
                       ▼   ᴀᴄᴄᴇssɪɴɢ   ▼  
                         ███████] 99%  
""")  

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self.LOGGER(__name__).info("ғᴜᴄᴋɪɴ ᴅᴏᴡɴ...")
        finally:
            loop.run_until_complete(self.stop())

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
