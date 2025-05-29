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
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, PeerIdInvalid
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import *
from database.database import *

#=====================================================================================##

REPLY_ERROR = "<code>Please send a message to broadcast</code>"

#=====================================================================================##

# Function to show broadcast settings with buttons and message effects
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

    # Select random image and effect
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

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
        else:
            try:
                await client.send_photo(
                    chat_id=chat_id,
                    photo=selected_image,
                    caption=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    message_effect_id=selected_effect
                )
            except PeerIdInvalid:
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=selected_effect
                )
    except Exception as e:
        logger.error(f"Failed to show broadcast settings: {str(e)}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>Error: Failed to show broadcast settings. Please try again.</b>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

# Command to show broadcast settings
@Bot.on_message(filters.command('cast') & filters.private & admin)
async def cast_settings(client: Client, message: Message):
    await show_broadcast_settings(client, message.chat.id)

# Callback handler for broadcast settings buttons
@Bot.on_callback_query(filters.regex(r"^cast_"))
async def cast_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

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
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
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
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
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
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
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
        logger.error(f"Failed to handle callback {data}: {str(e)}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>Error: Failed to process callback. Please try again.</b>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")

# Handle broadcast input
@Bot.on_message(filters.private & admin & ~filters.command(["start", "link", "forcesub", "admin", "auto_delete", "fsettings", "premium_cmd", "broadcast_cmd", "cast", "pbroadcast", "dbroadcast"]))
async def handle_broadcast_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)

    try:
        if state == "awaiting_broadcast_input":
            query = await db.full_userbase()
            broadcast_msg = message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>")
            for user_id in query:
                try:
                    await client.get_users(user_id)  # Check if user is accessible
                    await broadcast_msg.copy(user_id)
                    successful += 1
                except FloodWait as e:
                    if e.x > 60:  # Limit wait time to 60 seconds
                        logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                        unsuccessful += 1
                        continue
                    await asyncio.sleep(e.x)
                    await broadcast_msg.copy(user_id)
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
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
            broadcast_msg = message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>")
            for user_id in query:
                try:
                    await client.get_users(user_id)  # Check if user is accessible
                    sent_msg = await broadcast_msg.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except FloodWait as e:
                    if e.x > 60:  # Limit wait time to 60 seconds
                        logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                        unsuccessful += 1
                        continue
                    await asyncio.sleep(e.x)
                    sent_msg = await broadcast_msg.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
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
            # Serialize message data for storage
            message_data = {
                'chat_id': message.chat.id,
                'message_id': message.id,
                'text': message.text or message.caption,
                'entities': [
                    {
                        'type': entity.type.value,
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
            # Add support for other media types if needed (e.g., document, audio)

            try:
                await db.set_temp_data(chat_id, "broadcast_message", message_data)
                await db.set_temp_state(chat_id, "awaiting_dbroadcast_duration")
                await message.reply(
                    "Give me the duration in seconds.",  # Removed HTML tags to avoid EntityBoundsInvalid
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Back", callback_data="cast_back"),
                            InlineKeyboardButton("Close", callback_data="cast_close")
                        ]
                    ])
                )
            except Exception as e:
                logger.error(f"Failed to store message data for chat {chat_id}: {str(e)}")
                await message.reply("Error: Failed to process message. Please try again.")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_dbroadcast_duration":
            try:
                duration = int(message.text)
            except ValueError:
                await message.reply("Please use a valid duration in seconds.")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            broadcast_msg_data = await db.get_temp_data(chat_id, "broadcast_message")
            if not broadcast_msg_data:
                await message.reply("Error: No message found to broadcast.")
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            query = await db.full_userbase()
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast with auto-delete processing...</i>")
            for user_id in query:
                try:
                    await client.get_users(user_id)  # Check if user is accessible
                    # Reconstruct message
                    if broadcast_msg_data.get('media'):
                        if broadcast_msg_data['media']['type'] == 'photo':
                            sent_msg = await client.send_photo(
                                chat_id=user_id,
                                photo=broadcast_msg_data['media']['file_id'],
                                caption=broadcast_msg_data.get('text'),
                                caption_entities=[
                                    pyrogram.types.MessageEntity(**entity)
                                    for entity in broadcast_msg_data.get('entities', [])
                                ]
                            )
                        elif broadcast_msg_data['media']['type'] == 'video':
                            sent_msg = await client.send_video(
                                chat_id=user_id,
                                video=broadcast_msg_data['media']['file_id'],
                                caption=broadcast_msg_data.get('text'),
                                caption_entities=[
                                    pyrogram.types.MessageEntity(**entity)
                                    for entity in broadcast_msg_data.get('entities', [])
                                ]
                            )
                    else:
                        sent_msg = await client.send_message(
                            chat_id=user_id,
                            text=broadcast_msg_data.get('text'),
                            entities=[
                                pyrogram.types.MessageEntity(**entity)
                                for entity in broadcast_msg_data.get('entities', [])
                            ]
                        )
                    await asyncio.sleep(duration)
                    await sent_msg.delete()
                    successful += 1
                except FloodWait as e:
                    if e.x > 60:  # Limit wait time to 60 seconds
                        logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                        unsuccessful += 1
                        continue
                    await asyncio.sleep(e.x)
                    if broadcast_msg_data.get('media'):
                        if broadcast_msg_data['media']['type'] == 'photo':
                            sent_msg = await client.send_photo(
                                chat_id=user_id,
                                photo=broadcast_msg_data['media']['file_id'],
                                caption=broadcast_msg_data.get('text'),
                                caption_entities=[
                                    pyrogram.types.MessageEntity(**entity)
                                    for entity in broadcast_msg_data.get('entities', [])
                                ]
                            )
                        elif broadcast_msg_data['media']['type'] == 'video':
                            sent_msg = await client.send_video(
                                chat_id=user_id,
                                video=broadcast_msg_data['media']['file_id'],
                                caption=broadcast_msg_data.get('text'),
                                caption_entities=[
                                    pyrogram.types.MessageEntity(**entity)
                                    for entity in broadcast_msg_data.get('entities', [])
                                ]
                            )
                    else:
                        sent_msg = await client.send_message(
                            chat_id=user_id,
                            text=broadcast_msg_data.get('text'),
                            entities=[
                                pyrogram.types.MessageEntity(**entity)
                                for entity in broadcast_msg_data.get('entities', [])
                            ]
                        )
                    await asyncio.sleep(duration)
                    await sent_msg.delete()
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
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

    except Exception as e:
        logger.error(f"Failed to process broadcast input: {str(e)}")
        await message.reply(
            f"Failed to process broadcast: {str(e)}",
            parse_mode=None  # Avoid EntityBoundsInvalid
        )
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

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

        pls_wait = await message.reply("<i>Broadcast processing...</i>")
        for user_id in query:
            try:
                await client.get_users(user_id)  # Check if user is accessible
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                if e.x > 60:  # Limit wait time to 60 seconds
                    logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
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

        pls_wait = await message.reply("<i>Broadcast processing...</i>")
        for user_id in query:
            try:
                await client.get_users(user_id)  # Check if user is accessible
                await broadcast_msg.copy(user_id)
                successful += 1
            except FloodWait as e:
                if e.x > 60:  # Limit wait time to 60 seconds
                    logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(user_id)
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
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

#=====================================================================================##

@Bot.on_message(filters.private & filters.command('dbroadcast') & admin)
async def delete_broadcast(client: Bot, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])  # Get the duration in seconds
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
                await client.get_users(user_id)  # Check if user is accessible
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except FloodWait as e:
                if e.x > 60:  # Limit wait time to 60 seconds
                    logger.warning(f"FloodWait too long for user {user_id}: {e.x} seconds")
                    unsuccessful += 1
                    continue
                await asyncio.sleep(e.x)
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
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
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
