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

# Custom filter for timer input to avoid conflict with request_fsub
async def timer_input_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    if state == "awaiting_timer_input" and message.text and message.text.isdigit():
        logger.info(f"Timer input received for chat {chat_id}: {message.text}")
        return True
    return False

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
    try:
        msg = await client.send_photo(
            chat_id=message.chat.id,
            photo=selected_image,
            caption=WAIT_MSG
        )
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        msg = await client.send_message(
            chat_id=message.chat.id,
            text=WAIT_MSG
        )
    users = await db.full_userbase()
    try:
        await msg.edit_media(
            media=InputMediaPhoto(
                media=selected_image,
                caption=f"{len(users)} Uꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="user_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
                ]
            ])
        )
    except Exception as e:
        logger.error(f"Failed to edit message with image: {e}")
        await msg.edit(
            text=f"{len(users)} Uꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="user_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
                ]
            ])
        )

# AUTO-DELETE SETTINGS

# Function to show the auto-delete settings with inline buttons
async def show_auto_delete_settings(client: Bot, chat_id: int, message_id: int = None):
    auto_delete_mode = await db.get_auto_delete_mode()
    delete_timer = await db.get_del_timer()
    
    mode_status = "Eɴᴀʙʟᴇᴅ ✅" if auto_delete_mode else "Dɪsᴀʙʟᴇᴅ ❌"
    timer_text = get_readable_time(delete_timer)

    settings_text = (
        "» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢꜱ</b>\n\n"
        f"<blockquote>» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ:</b> {mode_status}</blockquote>\n"
        f"<blockquote>» <b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ:</b> {timer_text}</blockquote>\n\n"
        "<b>Cʟɪᴄᴋ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴꜱ Tᴏ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢꜱ</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Dɪsᴀʙʟᴇᴅ ❌" if auto_delete_mode else "• Eɴᴀʙʟᴇᴅ ✅", callback_data="auto_toggle"),
                InlineKeyboardButton(" Sᴇᴛ Tɪᴍᴇʀ •", callback_data="auto_set_timer")
            ],
            [
                InlineKeyboardButton("• Rᴇғʀᴇꜱʜ", callback_data="auto_refresh"),
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
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

@Bot.on_message(filters.private & filters.command('auto_delete') & admin)
async def auto_delete_settings(client: Bot, message: Message):
    # Reset state to avoid conflicts with previous operations
    await db.set_temp_state(message.chat.id, "")
    logger.info(f"Reset state for chat {message.chat.id} before showing auto-delete settings")
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
        await callback.answer(f"<blockquote><b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ {'Eɴᴀʙʟᴇᴅ' if new_mode else 'Dɪꜱᴀʙʟᴇᴅ'}!</b></blockquote>")
    
    elif data == "auto_set_timer":
        # Set a state to indicate that we are expecting a timer input
        await db.set_temp_state(chat_id, "awaiting_timer_input")
        logger.info(f"Set state to 'awaiting_timer_input' for chat {chat_id}")
        try:
            await callback.message.reply_photo(
                photo=selected_image,
                caption=(
                    "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ꜰᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                    "<blockquote><b>Eхᴀᴄᴀᴍᴘʟᴇ: 300 (ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ)</b></blockquote>"
                ),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.message.reply(
                "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ꜰᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                "<blockquote><b>Eхᴀᴄᴀᴍᴘʟᴇ: 300 (ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ)</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        await callback.answer("<blockquote><b>Eɴᴛᴇʀ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ!</b></blockquote>")
    
    elif data == "auto_refresh":
        await show_auto_delete_settings(client, chat_id, callback.message.id)
        await callback.answer("<blockquote><b>Sᴇᴛᴛɪɴɢꜱ ʀᴇꜰʀᴇꜱʜᴇᴅ!</b></blockquote>")
    
    elif data == "auto_back":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer("<blockquote><b>Bᴀᴄᴋ ᴛᴏ ᴘʀᴇᴠɪᴏᴜꜱ ᴍᴇɴᴜ!</b></blockquote>")

@Bot.on_message(filters.private & admin & filters.create(timer_input_filter), group=2)
async def set_timer(client: Bot, message: Message):
    chat_id = message.chat.id
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    
    logger.info(f"Received numeric input: {message.text} from chat {chat_id} in set_timer")

    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError("Duration must be a positive integer")
        await db.set_del_timer(duration)
        # Verify the timer was set
        new_timer = await db.get_del_timer()
        if new_timer == duration:
            try:
                await message.reply_photo(
                    photo=selected_image,
                    caption=f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
                await message.reply(
                    f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
            logger.info(f"Successfully set delete timer to {duration} seconds for chat {chat_id}")
        else:
            logger.error(f"Failed to set delete timer to {duration} seconds for chat {chat_id}")
            await message.reply(
                "<blockquote><b>Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        # Clear the state after processing
        await db.set_temp_state(chat_id, "")
        logger.info(f"Cleared state for chat {chat_id}")
    except ValueError as e:
        logger.error(f"Invalid duration input: {message.text} from chat {chat_id} - {str(e)}")
        try:
            await message.reply_photo(
                photo=selected_image,
                caption="<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴘᴏꜱɪᴛɪᴠᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await message.reply(
                "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴘᴏꜱɪᴛɪᴠᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
