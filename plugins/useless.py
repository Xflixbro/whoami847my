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
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges, InputMediaPhoto
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import RANDOM_IMAGES, START_PIC
from helper_func import *
from database.database import *

# Set up logging for this module
logger = logging.getLogger(__name__)

# Define message effect IDs
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

#=====================================================================================##

@Bot.on_message(filters.command('stats') & admin)
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))

#=====================================================================================##

WAIT_MSG = "<b>Wᴏʀᴋɪɴɢ...</b>"

#=====================================================================================##

@Bot.on_message(filters.command('users') & filters.private & admin)
async def get_users(client: Bot, message: Message):
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    logger.info(f"Processing /users command from user {message.from_user.id}")
    
    try:
        # Send initial "Working..." message
        msg = await client.send_photo(
            chat_id=message.chat.id,
            photo=selected_image,
            caption=WAIT_MSG,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to send initial photo for /users: {e}")
        msg = await client.send_message(
            chat_id=message.chat.id,
            text=WAIT_MSG,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

    try:
        # Fetch userbase with a timeout to prevent hanging
        logger.info("Attempting to fetch userbase from database")
        users = await asyncio.wait_for(db.full_userbase(), timeout=10.0)
        user_count = len(users)
        caption = f"{user_count} Uꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ"
        logger.info(f"Successfully fetched {user_count} users")
        
        try:
            await msg.edit_media(
                media=InputMediaPhoto(
                    media=selected_image,
                    caption=caption
                ),
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await msg.edit(
                text=caption,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    except asyncio.TimeoutError:
        logger.error("Database query timed out while fetching userbase")
        await msg.edit(
            text="Error: Database query timed out. Please check the database connection and try again.",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to fetch userbase: {e}")
        await msg.edit(
            text=f"Error: Could not fetch user data. Details: {str(e)}",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

#=====================================================================================##

# AUTO-DELETE SETTINGS

# Function to show the auto-delete settings with inline buttons
async def show_auto_delete_settings(client: Bot, chat_id: int, message_id: int = None):
    auto_delete_mode = await db.get_auto_delete_mode()
    delete_timer = await db.get_del_timer()
    
    mode_status = "Eɴᴀʙʟᴇᴅ ✅" if auto_delete_mode else "Dɪsᴀʙʟᴇᴅ ❌"
    timer_text = get_readable_time(delete_timer)

    settings_text = (
        "» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<blockquote>» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ:</b> {mode_status}</blockquote>\n"
        f"<blockquote>» <b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ:</b> {timer_text}</blockquote>\n\n"
        "<b>Cʟɪᴄᴋ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴs Tᴏ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢs</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Dɪsᴀʙʟᴇᴅ ❌" if auto_delete_mode else "• Eɴᴀʙʟᴇᴅ ✅", callback_data="auto_toggle"),
                InlineKeyboardButton(" Sᴇᴛ Tɪᴍᴇʀ •", callback_data="auto_set_timer")
            ],
            [
                InlineKeyboardButton("• Rᴇғʀᴇsʜ", callback_data="auto_refresh"),
                InlineKeyboardButton("Bᴀᴄᴋ •", callback_data="auto_back")
            ]
        ]
    )

    # Select a random image
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if message_id:
        try:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=keyboard,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

@Bot.on_message(filters.private & filters.command('auto_delete') & admin)
async def auto_delete_settings(client: Bot, message: Message):
    await show_auto_delete_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^auto_"))
async def auto_delete_callback(client: Bot, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if data == "auto_toggle":
        current_mode = await db.get_auto_delete_mode()
        new_mode = not current_mode
        await db.set_auto_delete_mode(new_mode)
        await show_auto_delete_settings(client, chat_id, callback.message.id)
        await callback.answer(f"<blockquote><b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ {'Eɴᴀʙʟᴇᴅ' if new_mode else 'Dɪsᴀʙʟᴇᴅ'}!</b></blockquote>")
    
    elif data == "auto_set_timer":
        # Set a state to indicate that we are expecting a timer input
        await db.set_temp_state(chat_id, "awaiting_timer_input")
        logger.info(f"Set state to 'awaiting_timer_input' for chat {chat_id}")
        try:
            await callback.message.reply_photo(
                photo=selected_image,
                caption=(
                    "<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs ғᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                    "<blockquote><b>Exᴀᴄᴀᴍᴘʟᴇ: 300 (ғᴏʀ 5 ᴍɪɴᴜᴛᴇs)</b></blockquote>"
                ),
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.message.reply(
                "<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs ғᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                "<blockquote><b>Exᴀᴄᴀᴍᴘʟᴇ: 300 (ғᴏʀ 5 ᴍɪɴᴜᴛᴇs)</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        await callback.answer("<blockquote><b>Eɴᴛᴇʀ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ!</b></blockquote>")
    
    elif data == "auto_refresh":
        await show_auto_delete_settings(client, chat_id, callback.message.id)
        await callback.answer("<blockquote><b>Sᴇᴛᴛɪɴɢs ʀᴇғʀᴇsʜᴇᴅ!</b></blockquote>")
    
    elif data == "auto_back":
        await callback.message.delete()
        await callback.answer("<blockquote><b>Bᴀᴄᴋ ᴛᴏ ᴘʀᴇᴠɪᴏᴜs ᴍᴇɴᴜ!</b></blockquote>")

@Bot.on_message(filters.private & filters.regex(r"^\d+$") & admin)
async def set_timer(client: Bot, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    
    logger.info(f"Received numeric input: {message.text} from chat {chat_id}, current state: {state}")

    # Only process the input if the state is "awaiting_timer_input"
    if state == "awaiting_timer_input":
        try:
            duration = int(message.text)
            await db.set_del_timer(duration)
            try:
                await message.reply_photo(
                    photo=selected_image,
                    caption=f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
                await message.reply(
                    f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀs ʙᴇᴇɴ sᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            logger.info(f"Set delete timer to {duration} seconds for chat {chat_id}")
            # Clear the state after processing
            await db.set_temp_state(chat_id, "")
        except ValueError:
            try:
                await message.reply_photo(
                    photo=selected_image,
                    caption="<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
                await message.reply(
                    "<b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ sᴇᴄᴏɴᴅs.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            logger.error(f"Invalid duration input: {message.text} from chat {chat_id}")
    else:
        logger.info(f"Ignoring numeric input: {message.text} as state is not 'awaiting_timer_input' for chat {chat_id}")

#=====================================================================================##

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
