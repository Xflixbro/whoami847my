#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *

#=====================================================================================##

REPLY_ERROR = "<code>Uꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ꜱᴘᴀᴄᴇꜱ.</code>"

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('pbroadcast') & admin)
async def send_pin_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                # Send and pin the message
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except Exception as e:
                print(f"Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴏʀ ᴘɪɴ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ {chat_id}: {e}")
                unsuccessful += 1
            total += 1

        status = f"""<b><u>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>

Tᴏᴛᴀʟ Uꜱᴇʀꜱ: <code>{total}</code>
Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{successful}</code>
Bʟᴏᴄᴋᴇᴅ Uꜱᴇʀꜱ: <code>{blocked}</code>
Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ: <code>{deleted}</code>
Uɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʰʀᴏᴀᴅᴄᴀꜱᴛ ᴀɴᴅ ᴘɪɴ ɪᴛ.")
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('broadcast') & admin)
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>

Tᴏᴛᴀʟ Uꜱᴇʀꜱ: <code>{total}</code>
Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{successful}</code>
Bʟᴏᴄᴋᴇᴅ Uꜱᴇʀꜱ: <code>{blocked}</code>
Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ: <code>{deleted}</code>
Uɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##
#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

# broadcast with auto-del
#

@Bot.on_message(filters.private & filters.command('dbroadcast') & admin)
async def delete_broadcast(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])  # Get the duration in seconds
        except (IndexError, ValueError):
            await message.reply("<b>Pʟᴇᴀꜱᴇ ᴜꜱᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ.</b> Uꜱᴀɢᴇ: /dbroadcast {duration}")
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴘʀᴏᴄᴇꜱꜱɪɴɢ....</i>")
        for chat_id in query:
            try:
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)  # Wait for the specified duration
                await sent_msg.delete()  # Delete the message after the duration
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(chat_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await db.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Bʀᴏᴀᴅᴄᴀꜱᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u></b>

Tᴏᴛᴀʟ Uꜱᴇʀꜱ: <code>{total}</code>
Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{successful}</code>
Bʟᴏᴄᴋᴇᴅ Uꜱᴇʀꜱ: <code>{blocked}</code>
Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛꜱ: <code>{deleted}</code>
Uɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Pʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ.")
        await asyncio.sleep(8)
        await msg.delete()

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#