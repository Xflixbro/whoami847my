#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#

import asyncio
import os
import random
import sys
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBot, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from bot import Bot
from config import *
from helper_func import *
from database.database import *

logger = logging.getLogger(__name__)

#=====================================================================================##

REPLY_ERROR = "<code>Please send a message to broadcast</code>"

# Global flag to track broadcast mode
broadcast_active = False
broadcast_active_timestamp = 0
BROADCAST_TIMEOUT = 60  # 60 seconds timeout

# Custom filter for checking broadcast active state
async def broadcast_active_filter(_, __, message: Message):
    is_active = broadcast_active
    logger.info(f"Checking broadcast_active_filter for chat {message.chat.id}: is_active={is_active}")
    return is_active

# Custom filter for dbroadcast duration input
async def dbroadcast_duration_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    is_valid = state == "awaiting_dbroadcast_duration" and message.text and message.text.isdigit()
    logger.info(f"Checking dbroadcast_duration_filter for chat {chat_id}: state={state}, message_text={message.text}, is_valid={is_valid}")
    return is_valid

async def reset_broadcast_mode(client: Client, chat_id: int):
    """Reset broadcast mode after timeout."""
    global broadcast_active, broadcast_active_timestamp
    await asyncio.sleep(BROADCAST_TIMEOUT)
    if time.time() - broadcast_active_timestamp >= BROADCAST_TIMEOUT:
        broadcast_active = False
        logger.info("Broadcast mode deactivated due to timeout")
        try:
            await client.send_message(
                chat_id=chat_id,
                text="Broadcast mode has timed out. Please use /cast to restart.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send timeout message to chat {chat_id}: {str(e)}")

#=====================================================================================##

async def show_broadcast_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>Broadcast Settings:</b>\n\n"
    settings_text += "<blockquote><b>Available Broadcast Options:</b></blockquote>\n\n"
    settings_text += "<blockquote><b>1. Broadcast - Send a message to all users.</b></blockquote>\n"
    settings_text += "<blockquote><b>2. Pin - Send and pin a message to all users.</b></blockquote>\n"
    settings_text += "<blockquote><b>3. Delete - Send a message with auto-delete after a specified time.</b></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Broadcast", callback_data="cast_broadcast"),
                InlineKeyboardButton("Pin", callback_data="cast_pbroadcast")
            ],
            [
                InlineKeyboardButton("Delete", callback_data="cast_dbroadcast")
            ],
            [
                InlineKeyboardButton("Refresh", callback_data="cast_refresh"),
                InlineKeyboardButton("Close", callback_data="cast_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    try:
        if message_id:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info(f"Edited broadcast settings for chat {chat_id}")
        else:
            try:
                await client.send_photo(
                    chat_id=chat_id,
                    photo=selected_image,
                    caption=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Sent broadcast settings with photo for chat {chat_id}")
            except Exception as e:
                logger.warning(f"Failed to send photo for chat {chat_id}: {str(e)}")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info(f"Sent broadcast settings as text for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to show broadcast settings for chat {chat_id}: {str(e)}")
        await client.send_message(
            chat_id=chat_id,
            text="Failed to show broadcast settings. Please try again.",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('cast') & filters.private & admin)
async def cast(client: Client, message: Message):
    """Handle /cast command to display broadcast settings."""
    logger.info(f"Cast command triggered by user {message.from_user.id}")
    await show_broadcast_settings(client, message.chat.id)
    await message.delete()

@Bot.on_callback_query(filters.regex(r"^cast_(broadcast|pbroadcast|dbroadcast|refresh|close)$"))
async def cast_callback(client: Client, query: CallbackQuery):
    """Handle callback queries for broadcast settings."""
    global broadcast_active, broadcast_active_timestamp
    action = query.data.split("_")[1]
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    logger.info(f"Cast callback triggered by user {user_id} with action {action}")

    if not await admin_check(client, query.message):
        await query.answer("You are not authorized!", show_alert=True)
        return

    if action == "refresh":
        await show_broadcast_settings(client, chat_id, query.message.id)
        await query.answer("Settings refreshed")
    elif action == "close":
        await query.message.delete()
        await query.answer("Settings closed")
    else:
        broadcast_active = True
        broadcast_active_timestamp = time.time()
        if action == "broadcast":
            await db.set_temp_state(chat_id, "awaiting_broadcast_input")
            text = "<b>Please send the message to broadcast to all users.</b>"
        elif action == "pbroadcast":
            await db.set_temp_state(chat_id, "awaiting_pbroadcast_input")
            text = "<b>Please send the message to broadcast and pin to all users.</b>"
        elif action == "dbroadcast":
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_message")
            text = "<b>Please send the message to broadcast with auto-delete.</b>"

        try:
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Cancel", callback_data="cast_cancel")]
                ])
            )
            await query.answer(f"Send the message for {action}")
            asyncio.create_task(reset_broadcast_mode(client, chat_id))
        except Exception as e:
            logger.error(f"Failed to edit message for {action} in chat {chat_id}: {str(e)}")
            await query.message.reply_text(
                text="Failed to proceed. Please try again.",
                parse_mode=ParseMode.HTML
            )
            broadcast_active = False

@Bot.on_callback_query(filters.regex(r"^cast_cancel$"))
async def cast_cancel(client: Client, query: CallbackQuery):
    """Handle cancellation of broadcast process."""
    global broadcast_active
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    logger.info(f"Cast cancel triggered by user {user_id}")

    if not await admin_check(client, query.message):
        await query.answer("You are not authorized!", show_alert=True)
        return

    broadcast_active = False
    await db.clear_temp_state(chat_id)
    try:
        await query.message.edit_text(
            text="<b>Broadcast process cancelled.</b>",
            parse_mode=ParseMode.HTML
        )
        await query.answer("Broadcast cancelled")
    except Exception as e:
        logger.error(f"Failed to cancel broadcast for chat {chat_id}: {str(e)}")
        await query.message.reply_text(
            text="Failed to cancel. Please try again.",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.create(broadcast_active_filter) & ~filters.command, group=-2)
async def handle_broadcast_input(client: Client, message: Message):
    """Handle input for broadcast, pbroadcast, and dbroadcast messages."""
    global broadcast_active
    chat_id = message.chat.id
    user_id = message.from_user.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Handling broadcast input for user {user_id}, state: {state}")

    if not await admin_check(client, message):
        await message.reply_text("<b>You are not authorized!</b>", parse_mode=ParseMode.HTML)
        return

    if state not in ["awaiting_broadcast_input", "awaiting_pbroadcast_input", "awaiting_dbroadcast_message"]:
        logger.info(f"Invalid state {state} for broadcast input from user {user_id}")
        return

    if not (message.text or message.media):
        await message.reply_text(REPLY_ERROR, parse_mode=ParseMode.HTML)
        return

    if state == "awaiting_dbroadcast_message":
        await db.set_temp_state(chat_id, "awaiting_dbroadcast_duration")
        try:
            await message.reply_text(
                "<b>Please send the duration in minutes for auto-delete.</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Cancel", callback_data="cast_cancel")]
                ])
            )
        except Exception as e:
            logger.error(f"Failed to request duration for dbroadcast in chat {chat_id}: {str(e)}")
            await message.reply_text(
                "Failed to proceed. Please try again.",
                parse_mode=ParseMode.HTML
            )
            broadcast_active = False
        return

    # Process broadcast or pbroadcast
    broadcast_type = "pin" if state == "awaiting_pbroadcast_input" else "normal"
    broadcast_active = False
    await db.clear_temp_state(chat_id)

    users = await db.get_all_users()
    total = len(users)
    success = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0
    status_message = None

    await client.send_chat_action(chat_id, ChatAction.TYPING)
    status_message = await message.reply_text(
        f"<b>Broadcasting to {total} users...</b>",
        parse_mode=ParseMode.HTML
    )

    start_time = time.time()
    for user in users:
        try:
            user_id = user['id']
            sent_message = await message.copy(
                chat_id=user_id,
                disable_notification=(broadcast_type != "pin")
            )
            if broadcast_type == "pin":
                await client.pin_chat_message(
                    chat_id=user_id,
                    message_id=sent_message.id,
                    disable_notification=True
                )
            success += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            unsuccessful += 1
        except UserIsBlocked:
            blocked += 1
            await db.delete_user(user_id)
        except InputUserDeactivated:
            deleted += 1
            await db.delete_user(user_id)
        except PeerIdInvalid:
            unsuccessful += 1
        except Exception as e:
            logger.error(f"Failed to broadcast to user {user_id}: {str(e)}")
            unsuccessful += 1

    end_time = time.time()
    time_taken = timedelta(seconds=int(end_time - start_time))
    status_text = (
        f"<b>Broadcast Completed</b>\n\n"
        f"<b>Total Users:</b> {total}\n"
        f"<b>Success:</b> {success}\n"
        f"<b>Blocked:</b> {blocked}\n"
        f"<b>Deleted:</b> {deleted}\n"
        f"<b>Unsuccessful:</b> {unsuccessful}\n"
        f"<b>Time Taken:</b> {time_taken}"
    )

    try:
        await status_message.edit_text(
            text=status_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to update status message in chat {chat_id}: {str(e)}")
        await message.reply_text(
            text=status_text,
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.create(dbroadcast_duration_filter))
async def handle_dbroadcast_duration(client: Client, message: Message):
    """Handle duration input for dbroadcast."""
    global broadcast_active
    chat_id = message.chat.id
    user_id = message.from_user.id
    duration = int(message.text)
    logger.info(f"Handling dbroadcast duration input for user {user_id}: {duration} minutes")

    if not await admin_check(client, message):
        await message.reply_text("<b>You are not authorized!</b>", parse_mode=ParseMode.HTML)
        return

    broadcast_active = False
    await db.clear_temp_state(chat_id)

    users = await db.get_all_users()
    total = len(users)
    success = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0
    status_message = None

    await client.send_chat_action(chat_id, ChatAction.TYPING)
    status_message = await message.reply_text(
        f"<b>Broadcasting to {total} users with auto-delete after {duration} minutes...</b>",
        parse_mode=ParseMode.HTML
    )

    start_time = time.time()
    for user in users:
        try:
            user_id = user['id']
            sent_message = await message.reply_to_message.copy(
                chat_id=user_id,
                disable_notification=True
            )
            await asyncio.sleep(duration * 60)
            await client.delete_messages(
                chat_id=user_id,
                message_ids=sent_message.id
            )
            success += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            unsuccessful += 1
        except UserIsBlocked:
            blocked += 1
            await db.delete_user(user_id)
        except InputUserDeactivated:
            deleted += 1
            await db.delete_user(user_id)
        except PeerIdInvalid:
            unsuccessful += 1
        except Exception as e:
            logger.error(f"Failed to broadcast to user {user_id}: {str(e)}")
            unsuccessful += 1

    end_time = time.time()
    time_taken = timedelta(seconds=int(end_time - start_time))
    status_text = (
        f"<b>Delete Broadcast Completed</b>\n\n"
        f"<b>Total Users:</b> {total}\n"
        f"<b>Success:</b> {success}\n"
        f"<b>Blocked:</b> {blocked}\n"
        f"<b>Deleted:</b> {deleted}\n"
        f"<b>Unsuccessful:</b> {unsuccessful}\n"
        f"<b>Time Taken:</b> {time_taken}\n"
        f"<b>Auto-delete after:</b> {duration} minutes"
    )

    try:
        await status_message.edit_text(
            text=status_text,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to update status message in chat {chat_id}: {str(e)}")
        await message.reply_text(
            text=status_text,
            parse_mode=ParseMode.HTML
        )

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#
