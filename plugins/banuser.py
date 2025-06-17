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

# Function to show user settings with user list and buttons
async def show_user_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Uꜱᴇʀ Sᴇᴛᴛɪɴɢꜱ:</b>\n\n"
    user_ids = await db.full_userbase()

    if not user_ids:
        settings_text += "<i>Nᴏ ᴜꜱᴇʀꜱ ᴄᴏɴғɪɢᴜʀᴇᴅ ʏᴇᴛ.</i>"
    else:
        settings_text += "<blockquote><b>⚡ Cᴜʀʀᴇɴᴛ Uꜱᴇʀꜱ:</b></blockquote>\n\n"
        for idx, user_id in enumerate(user_ids[:5], 1):  # Show up to 5 users
            try:
                user = await client.get_users(user_id)
                name = user.first_name if user.first_name else "Unknown"
                settings_text += f"<blockquote><b>{idx}. {name} - <code>{user_id}</code></b></blockquote>\n"
            except Exception as e:
                settings_text += f"<blockquote><b>{idx}. Unknown - <code>{user_id}</code></b></blockquote>\n"
        if len(user_ids) > 5:
            settings_text += f"<blockquote><i>...and {len(user_ids) - 5} more.</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Bᴀɴ Uꜱᴇʀ", callback_data="user_ban"),
                InlineKeyboardButton("Uɴʙᴀɴ Uꜱᴇʀ •", callback_data="user_unban")
            ],
            [
                InlineKeyboardButton("Uꜱᴇʀ Lɪꜱᴛ", callback_data="user_list"),
                InlineKeyboardButton("Bᴀɴ Lɪꜱᴛ", callback_data="user_banlist")
            ],
            [
                InlineKeyboardButton("• Rᴇꜰʀᴇꜱʜ •", callback_data="user_refresh"),
                InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
            ]
        ]
    )

    # Select random image
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if message_id:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to edit user settings message: {e}")
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send user settings with photo: {e}")
            # Fallback to text-only message
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
