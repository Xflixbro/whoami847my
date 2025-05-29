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

# Custom filter for dbroadcast duration input
async def dbroadcast_duration_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    is_valid = state == "awaiting_dbroadcast_duration" and message.text and message.text.isdigit()
    logger.info(f"Checking dbroadcast_duration_filter for chat {chat_id}: state={state}, message_text={message.text}, is_valid={is_valid}")
    return is_valid

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
async def cast_settings(client: Client, message: Message):
    logger.info(f"Received /cast command from chat {message.chat.id}")
    await show_broadcast_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^cast_"))
async def cast_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id
    logger.info(f"Handling callback {data} for chat {chat_id}")

    try:
        if data == "cast_broadcast":
            await db.set_temp_state(chat_id, "awaiting_broadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Please send a message to broadcast.")

        elif data == "cast_pbroadcast":
            await db.set_temp_state(chat_id, "awaiting_pbroadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Please send a message to broadcast and pin.")

        elif data == "cast_dbroadcast":
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_message")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=REPLY_ERROR,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Please send a message to broadcast with auto-delete.")

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
        logger.error(f"Failed to handle callback {data} for chat {chat_id}: {str(e)}")
        await client.send_message(
            chat_id=chat_id,
            text="Failed to process callback. Please try again.",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")

@Bot.on_message(filters.private & admin_only & filters.text & filters.create(dbroadcast_duration_filter), group=-1)
async def handle_dbroadcast_duration(client: Client, message: Message):
    chat_id = message.chat.id
    logger.info(f"Handling dbroadcast duration input for chat {chat_id}: message_text={message.text}")

    try:
        duration = int(message.text)
        logger.info(f"Parsed duration: {duration} seconds for chat {chat_id}")
        if duration <= 0:
            logger.error(f"Invalid duration input for chat {chat_id}: {message.text}")
            await message.reply("Please use a valid positive duration in seconds.")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        broadcast_msg_data = await db.get_temp_data(chat_id, "broadcast_message")
        if not broadcast_msg_data:
            logger.error(f"No broadcast message found for chat {chat_id}")
            await message.reply("Error: No message found to broadcast.")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        logger.info(f"Broadcast message data for chat {chat_id}: {broadcast_msg_data}")
        query = await db.full_userbase()
        logger.info(f"Userbase size for dbroadcast: {len(query)}")
        if not query:
            logger.error(f"No users found in userbase for chat {chat_id}")
            await message.reply("Error: No users found to broadcast.")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)
            return

        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply(f"<i>Processing your duration of {duration} seconds...</i>")
        for user_id in query:
            try:
                logger.info(f"Attempting to broadcast to user {user_id}")
                user = await client.get_users(user_id)
                if user.is_bot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                    continue

                # Simplified entity reconstruction
                entities = []
                for entity in broadcast_msg_data.get('entities', []):
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
                        else:
                            logger.warning(f"Unsupported entity type {entity_type_str} for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to process entity {entity['type']} for user {user_id}: {str(e)}")
                        continue

                if broadcast_msg_data.get('media'):
                    if broadcast_msg_data['media']['type'] == 'photo':
                        sent_msg = await client.send_photo(
                            chat_id=user_id,
                            photo=broadcast_msg_data['media']['file_id'],
                            caption=broadcast_msg_data.get('text'),
                            caption_entities=entities
                        )
                    elif broadcast_msg_data['media']['type'] == 'video':
                        sent_msg = await client.send_video(
                            chat_id=user_id,
                            video=broadcast_msg_data['media']['file_id'],
                            caption=broadcast_msg_data.get('text'),
                            caption_entities=entities
                        )
                else:
                    sent_msg = await client.send_message(
                        chat_id=user_id,
                        text=broadcast_msg_data.get('text'),
                        entities=entities
                    )
                logger.info(f"Sent message to user {user_id}, waiting {duration} seconds before deletion")
                await asyncio.sleep(duration)
                await sent_msg.delete()
                logger.info(f"Deleted message for user {user_id}")
                successful += 1
            except FloodWait as e:
                if e.value > 60:
                    logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.value)
                entities = []
                for entity in broadcast_msg_data.get('entities', []):
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
                        else:
                            logger.warning(f"Unsupported entity type {entity_type_str} for user {user_id}")
                    except Exception as e:
                        logger.warning(f"Failed to process entity {entity['type']} for user {user_id}: {str(e)}")
                        continue

                if broadcast_msg_data.get('media'):
                    if broadcast_msg_data['media']['type'] == 'photo':
                        sent_msg = await client.send_photo(
                            chat_id=user_id,
                            photo=broadcast_msg_data['media']['file_id'],
                            caption=broadcast_msg_data.get('text'),
                            caption_entities=entities
                        )
                    elif broadcast_msg_data['media']['type'] == 'video':
                        sent_msg = await client.send_video(
                            chat_id=user_id,
                            video=broadcast_msg_data['media']['file_id'],
                            caption=broadcast_msg_data.get('text'),
                            caption_entities=entities
                        )
                else:
                    sent_msg = await client.send_message(
                        chat_id=user_id,
                        text=broadcast_msg_data.get('text'),
                        entities=entities
                    )
                await asyncio.sleep(duration)
                await sent_msg.delete()
                logger.info(f"Deleted message for user {user_id}")
                successful += 1
            except UserIsBot:
                logger.info(f"Skipping bot user {user_id}")
                unsuccessful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
                logger.info(f"User {user_id} blocked, removed from database")
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
                logger.info(f"User {user_id} deactivated, removed from database")
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send or delete message to {user_id}: {str(e)}")
            total += 1

        status = f"""<b><u>Broadcast with auto-delete completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)
        await db.set_temp_state(chat_id, "")
        await db.set_temp_data(chat_id, "broadcast_message", None)
        await show_broadcast_settings(client, chat_id)
        logger.info(f"Broadcast completed for chat {chat_id}: {status}")

    except Exception as e:
        logger.error(f"Failed to process dbroadcast duration for chat {chat_id}: {str(e)}")
        await message.reply(f"Failed to process broadcast: {str(e)}")
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

@Bot.on_message(filters.private & admin_only & ~filters.command(["start", "link", "forcesub", "admin", "auto_delete", "fsettings", "premium_cmd", "broadcast_cmd", "cast", "pbroadcast", "dbroadcast"]))
async def handle_broadcast_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Handling broadcast input for chat {chat_id} with state {state}, message_text={message.text}")

    try:
        if state == "awaiting_broadcast_input":
            query = await db.full_userbase()
            logger.info(f"Userbase size for broadcast: {len(query)}")
            if not query:
                logger.error(f"No users found in userbase for chat {chat_id}")
                await message.reply("Error: No users found to broadcast.")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>")
            for user_id in query:
                try:
                    user = await client.get_users(user_id)
                    if user.is_bot:
                        logger.info(f"Skipping bot user {user_id}")
                        unsuccessful += 1
                        continue
                    await message.copy(user_id)
                    successful += 1
                except FloodWait as e:
                    if e.value > 60:
                        logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                        unsuccessful += 1
                        continue
                    await asyncio.sleep(e.value)
                    await message.copy(user_id)
                    successful += 1
                except UserIsBot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                    logger.info(f"User {user_id} blocked, removed from database")
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
                    logger.info(f"User {user_id} deactivated, removed from database")
                except PeerIdInvalid:
                    await db.del_user(user_id)
                    unsuccessful += 1
                    logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
                except Exception as e:
                    unsuccessful += 1
                    logger.error(f"Failed to send message to {user_id}: {str(e)}")
                total += 1

            status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

            await pls_wait.edit(status)
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_pbroadcast_input":
            query = await db.full_userbase()
            logger.info(f"Userbase size for pin broadcast: {len(query)}")
            if not query:
                logger.error(f"No users found in userbase for chat {chat_id}")
                await message.reply("Error: No users found to broadcast.")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>")
            for user_id in query:
                try:
                    user = await client.get_users(user_id)
                    if user.is_bot:
                        logger.info(f"Skipping bot user {user_id}")
                        unsuccessful += 1
                        continue
                    sent_msg = await message.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except FloodWait as e:
                    if e.value > 60:
                        logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                        unsuccessful += 1
                        continue
                    await asyncio.sleep(e.value)
                    sent_msg = await message.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except UserIsBot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                    logger.info(f"User {user_id} blocked, removed from database")
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
                    logger.info(f"User {user_id} deactivated, removed from database")
                except PeerIdInvalid:
                    await db.del_user(user_id)
                    unsuccessful += 1
                    logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
                except Exception as e:
                    unsuccessful += 1
                    logger.error(f"Failed to send or pin message to {user_id}: {str(e)}")
                total += 1

            status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

            await pls_wait.edit(status)
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_dbroadcast_message":
            message_data = {
                'chat_id': message.chat.id,
                'message_id': message.id,
                'text': message.text or message.caption,
                'entities': [
                    {
                        'type': str(entity.type).split('.')[-1],  # Convert enum to string
                        'offset': entity.offset,
                        'length': entity.length,
                        'url': getattr(entity, 'url', None),
                        'user': getattr(entity, 'user', None),
                        'language': getattr(entity, 'language', None),
                        'custom_emoji_id': getattr(entity, 'custom_emoji_id', None)
                    } for entity in (message.entities or message.caption_entities or [])
                ],
                'media': None
            }
            if message.photo:
                message_data['media'] = {'type': 'photo', 'file_id': message.photo.file_id}
            elif message.video:
                message_data['media'] = {'type': 'video', 'file_id': message.video.file_id}

            try:
                await db.set_temp_data(chat_id, "broadcast_message", message_data)
                await db.set_temp_state(chat_id, "awaiting_dbroadcast_duration")
                await message.reply(
                    "দয়া করে ডিউরেশন সেকেন্ডে দিন। উদাহরণ: 60 (১ মিনিটের জন্য) বা 300 (৫ মিনিটের জন্য)।",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Back", callback_data="cast_back"),
                            InlineKeyboardButton("Close", callback_data="cast_close")
                        ]
                    ])
                )
                logger.info(f"Prompted for duration input for chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to store message data for chat {chat_id}: {str(e)}")
                await message.reply(f"Error: Failed to process message: {str(e)}")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_dbroadcast_duration" and message.text and message.text.isdigit():
            # Fallback handler for duration input
            logger.warning(f"Fallback triggered for duration input in chat {chat_id}: message_text={message.text}")
            await handle_dbroadcast_duration(client, message)

    except Exception as e:
        logger.error(f"Failed to process broadcast input for chat {chat_id}: {str(e)}")
        await message.reply(f"Failed to process broadcast: {str(e)}")
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

@Bot.on_message(filters.private & filters.command('pbroadcast') & admin_only)
async def send_pin_text(client: Client, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        logger.info(f"Userbase size for pin broadcast: {len(query)}")
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast processing...</i>")
        for user_id in query:
            try:
                user = await client.get_users(user_id)
                if user.is_bot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                    continue
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                if e.value > 60:
                    logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBot:
                logger.info(f"Skipping bot user {user_id}")
                unsuccessful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
                logger.info(f"User {user_id} blocked, removed from database")
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
                logger.info(f"User {user_id} deactivated, removed from database")
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send or pin message to {user_id}: {str(e)}")
            total += 1

        status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

@Bot.on_message(filters.private & filters.command('broadcast') & admin_only)
async def send_text(client: Client, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast processing...</i>")
        for user_id in query:
            try:
                user = await client.get_users(user_id)
                if user.is_bot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                    continue
                await broadcast_msg.copy(user_id)
                successful += 1
            except FloodWait as e:
                if e.value > 60:
                    logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(user_id)
                successful += 1
            except UserIsBot:
                logger.info(f"Skipping bot user {user_id}")
                unsuccessful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
                logger.info(f"User {user_id} blocked, removed from database")
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
                logger.info(f"User {user_id} deactivated, removed from database")
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send message to {user_id}: {str(e)}")
            total += 1

        status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

@Bot.on_message(filters.private & filters.command('dbroadcast') & admin_only)
async def delete_broadcast(client: Client, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])
        except (IndexError, ValueError):
            await message.reply("Please use a valid duration in seconds. Usage: /dbroadcast {duration}")
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast with auto-delete processing...</i>")
        for user_id in query:
            try:
                user = await client.get_users(user_id)
                if user.is_bot:
                    logger.info(f"Skipping bot user {user_id}")
                    unsuccessful += 1
                    continue
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except FloodWait as e:
                if e.value > 60:
                    logger.warning(f"FloodWait too long for user {user_id}: {e.value} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBot:
                logger.info(f"Skipping bot user {user_id}")
                unsuccessful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
                logger.info(f"User {user_id} blocked, removed from database")
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
                logger.info(f"User {user_id} deactivated, removed from database")
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send or delete message to {user_id}: {str(e)}")
            total += 1

        status = f"""<b><u>Broadcast with auto-delete completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)

    else:
        msg = await message.reply("Please reply to a message to broadcast it with auto-delete.")
        await asyncio.sleep(8)
        await msg.delete()

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#
