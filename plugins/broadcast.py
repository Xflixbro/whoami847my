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
import random
import logging
from typing import Dict
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBot, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from bot import Bot
from config import RANDOM_IMAGES, START_PIC, OWNER_ID
from helper_func import admin
from database.database import db

# Logging setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

REPLY_ERROR = "<code>Please send a message to broadcast</code>"

# Custom filter for dbroadcast duration input
async def dbroadcast_duration_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    is_valid = state == "awaiting_dbroadcast_duration" and message.text and message.text.isdigit()
    logger.info(f"dbroadcast_duration_filter for chat {chat_id}: state={state}, text={message.text}, valid={is_valid}")
    return is_valid

async def show_broadcast_settings(client: Client, chat_id: int, message_id: int = None):
    """Display the broadcast settings menu."""
    settings_text = (
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<b>Broadcast Settings:</b>\n\n"
        "<blockquote><b>Available Options:</b></blockquote>\n"
        "<blockquote><b>1. Broadcast - Send a message to all users.</b></blockquote>\n"
        "<blockquote><b>2. Pin - Send and pin a message to all users.</b></blockquote>\n"
        "<blockquote><b>3. Delete - Send a message with auto-delete after a specified time.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• Broadcast •", callback_data="cast_broadcast"),
            InlineKeyboardButton("• Pin •", callback_data="cast_pbroadcast")
        ],
        [InlineKeyboardButton("• Delete •", callback_data="cast_dbroadcast")],
        [
            InlineKeyboardButton("• Refresh •", callback_data="cast_refresh"),
            InlineKeyboardButton("• Close •", callback_data="cast_close")
        ]
    ])

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
                logger.warning(f"Failed to send photo for chat {chat_id}: {e}")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info(f"Sent broadcast settings as text for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to show broadcast settings for chat {chat_id}: {e}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Failed to show broadcast settings.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('cast') & filters.private & admin)
async def cast_settings(client: Client, message: Message):
    """Handle /cast command to show broadcast settings."""
    chat_id = message.chat.id
    logger.info(f"/cast command from chat {chat_id}")
    admin_ids = await db.get_all_admins() or []
    if chat_id not in admin_ids and chat_id != OWNER_ID:
        await message.reply_text(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        return
    await show_broadcast_settings(client, chat_id)

@Bot.on_callback_query(filters.regex(r"^cast_"))
async def cast_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for broadcast settings."""
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id
    logger.info(f"Callback {data} for chat {chat_id}")

    admin_ids = await db.get_all_admins() or []
    if chat_id not in admin_ids and chat_id != OWNER_ID:
        await callback.answer("You are not authorized!", show_alert=True)
        return

    try:
        if data == "cast_broadcast":
            await db.set_temp_state(chat_id, "awaiting_broadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="cast_back"),
                        InlineKeyboardButton("✖️ Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Send a message to broadcast.")

        elif data == "cast_pbroadcast":
            await db.set_temp_state(chat_id, "awaiting_pbroadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="cast_back"),
                        InlineKeyboardButton("✖️ Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Send a message to broadcast and pin.")

        elif data == "cast_dbroadcast":
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_message")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="cast_back"),
                        InlineKeyboardButton("✖️ Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Send a message to broadcast with auto-delete.")

        elif data == "cast_refresh":
            await show_broadcast_settings(client, chat_id, message_id)
            await callback.answer("Settings refreshed!")

        elif data == "cast_close":
            await db.set_temp_state(chat_id, "")
            await callback.message.delete()
            await callback.answer("Settings closed!")

        elif data == "cast_back":
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id, message_id)
            await callback.answer("Back to settings!")

    except Exception as e:
        logger.error(f"Failed to handle callback {data} for chat {chat_id}: {e}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Failed to process callback.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")

async def broadcast_message(client: Client, user_id: int, message_data: Dict, pin: bool = False, auto_delete: int = None) -> Dict:
    """Send a broadcast message to a user."""
    try:
        entities = []
        for entity in message_data.get('entities', []):
            try:
                entity_type_str = entity['type'].upper()
                entity_type = getattr(pyrogram.enums.MessageEntityType, entity_type_str, None)
                if entity_type:
                    entities.append(
                        pyrogram.types.MessageEntity(
                            type=entity_type,
                            offset=entity['offset'],
                            length=entity['length'],
                            url=entity.get('url'),
                            user=entity.get('user'),
                            language=entity.get('language'),
                            custom_emoji_id=entity.get('custom_emoji_id')
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to process entity {entity['type']} for user {user_id}: {e}")
                continue

        if message_data.get('media'):
            if message_data['media']['type'] == 'photo':
                sent_msg = await client.send_photo(
                    chat_id=user_id,
                    photo=message_data['media']['file_id'],
                    caption=message_data.get('text'),
                    caption_entities=entities
                )
            elif message_data['media']['type'] == 'video':
                sent_msg = await client.send_video(
                    chat_id=user_id,
                    video=message_data['media']['file_id'],
                    caption=message_data.get('text'),
                    caption_entities=entities
                )
            else:
                logger.warning(f"Unsupported media type {message_data['media']['type']} for user {user_id}")
                return {"status": "unsuccessful", "error": "Unsupported media type"}
        else:
            sent_msg = await client.send_message(
                chat_id=user_id,
                text=message_data.get('text'),
                entities=entities
            )

        if pin:
            try:
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
            except Exception as e:
                logger.warning(f"Failed to pin message for user {user_id}: {e}")

        if auto_delete:
            await asyncio.sleep(auto_delete)
            await sent_msg.delete()

        return {"status": "success", "sent_msg": sent_msg}
    except FloodWait as e:
        if e.value > 60:
            logger.warning(f"FloodWait too long for user {user_id}: {e.value}s")
            return {"status": "unsuccessful", "error": "FloodWait too long"}
        await asyncio.sleep(e.value)
        return await broadcast_message(client, user_id, message_data, pin, auto_delete)
    except UserIsBot:
        logger.info(f"Skipping bot user {user_id}")
        return {"status": "unsuccessful", "error": "User is bot"}
    except UserIsBlocked:
        await db.del_user(user_id)
        logger.info(f"User {user_id} blocked, removed from database")
        return {"status": "blocked"}
    except InputUserDeactivated:
        await db.del_user(user_id)
        logger.info(f"User {user_id} deactivated, removed from database")
        return {"status": "deleted"}
    except PeerIdInvalid:
        await db.del_user(user_id)
        logger.warning(f"Removed invalid user ID {user_id} due to PeerIdInvalid")
        return {"status": "unsuccessful", "error": "PeerIdInvalid"}
    except Exception as e:
        logger.error(f"Failed to send message to {user_id}: {e}")
        return {"status": "unsuccessful", "error": str(e)}

@Bot.on_message(filters.private & admin & filters.text & filters.create(dbroadcast_duration_filter))
async def handle_dbroadcast_duration(client: Client, message: Message):
    """Handle duration input for auto-delete broadcast."""
    chat_id = message.chat.id
    logger.info(f"dbroadcast duration input for chat {chat_id}: {message.text}")

    try:
        admin_ids = await db.get_all_admins() or []
        if chat_id not in admin_ids and chat_id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        duration = int(message.text)
        if duration <= 0:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Please use a valid positive duration in seconds.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        broadcast_msg_data = await db.get_temp_data(chat_id, "broadcast_message")
        if not broadcast_msg_data:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Error: No message found to broadcast.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        query = await db.full_userbase()
        if not query:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Error: No users found to broadcast.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply(f"<i>Processing broadcast with auto-delete after {duration}s...</i>")
        for user_id in query:
            result = await broadcast_message(client, user_id, broadcast_msg_data, auto_delete=duration)
            total += 1
            if result["status"] == "success":
                successful += 1
            elif result["status"] == "blocked":
                blocked += 1
            elif result["status"] == "deleted":
                deleted += 1
            else:
                unsuccessful += 1

        status = (
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<b><u>Broadcast with Auto-Delete Completed</u></b>\n\n"
            f"Total Users: <code>{total}</code>\n"
            f"Successful: <code>{successful}</code>\n"
            f"Blocked Users: <code>{blocked}</code>\n"
            f"Deleted Accounts: <code>{deleted}</code>\n"
            f"Unsuccessful: <code>{unsuccessful}</code>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )

        await pls_wait.edit(status, parse_mode=ParseMode.HTML)
        await db.set_temp_state(chat_id, "")
        await db.set_temp_data(chat_id, "broadcast_message", None)
        await show_broadcast_settings(client, chat_id)
        logger.info(f"Broadcast completed for chat {chat_id}: {status}")

    except Exception as e:
        logger.error(f"Failed to process dbroadcast duration for chat {chat_id}: {e}")
        await message.reply(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Failed to process broadcast: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

@Bot.on_message(filters.private & admin & ~filters.command(["start", "link", "forcesub", "admin", "auto_delete", "fsettings", "premium_cmd", "broadcast_cmd", "cast", "pbroadcast", "dbroadcast"]))
async def handle_broadcast_input(client: Client, message: Message):
    """Handle input for broadcast messages based on state."""
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Broadcast input for chat {chat_id} with state {state}")

    try:
        admin_ids = await db.get_all_admins() or []
        if chat_id not in admin_ids and chat_id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        if state not in ["awaiting_broadcast_input", "awaiting_pbroadcast_input", "awaiting_dbroadcast_message"]:
            return

        broadcast_data = {
            'text': message.text or message.caption or "",
            'entities': [
                {
                    'type': entity.type.name.lower(),
                    'offset': entity.offset,
                    'length': entity.length,
                    'url': getattr(entity, 'url', None),
                    'user': getattr(entity, 'user', None),
                    'language': getattr(entity, 'language', None),
                    'custom_emoji_id': getattr(entity, 'custom_emoji_id', None)
                } for entity in (message.entities or message.caption_entities or [])
            ]
        }

        if message.photo:
            broadcast_data['media'] = {'type': 'photo', 'file_id': message.photo.file_id}
        elif message.video:
            broadcast_data['media'] = {'type': 'video', 'file_id': message.video.file_id}

        query = await db.full_userbase()
        if not query:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Error: No users found to broadcast.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pin = state == "awaiting_pbroadcast_input"

        if state == "awaiting_dbroadcast_message":
            await db.set_temp_data(chat_id, "broadcast_message", broadcast_data)
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_duration")
            await message.reply(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Please send the auto-delete duration in seconds.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="cast_back"),
                        InlineKeyboardButton("✖️ Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            return

        pls_wait = await message.reply("<i>Broadcast processing...</i>")
        for user_id in query:
            result = await broadcast_message(client, user_id, broadcast_data, pin=pin)
            total += 1
            if result["status"] == "success":
                successful += 1
            elif result["status"] == "blocked":
                blocked += 1
            elif result["status"] == "deleted":
                deleted += 1
            else:
                unsuccessful += 1

        broadcast_type = "Pinned Broadcast" if pin else "Broadcast"
        status = (
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b><u>{broadcast_type} Completed</u></b>\n\n"
            f"Total Users: <code>{total}</code>\n"
            f"Successful: <code>{successful}</code>\n"
            f"Blocked Users: <code>{blocked}</code>\n"
            f"Deleted Accounts: <code>{deleted}</code>\n"
            f"Unsuccessful: <code>{unsuccessful}</code>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )

        await pls_wait.edit(status, parse_mode=ParseMode.HTML)
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)
        logger.info(f"{broadcast_type} completed for chat {chat_id}: {status}")

    except Exception as e:
        logger.error(f"Failed to process broadcast input for chat {chat_id}: {e}")
        await message.reply(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Failed to process broadcast: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#
