#
# Copyright (C) 2025 by AnimeLord-Bots@Github, <https://github.com/AnimeLord-Bots>.
#
# This file is part of <https://github.com/AnimeLord-Bots/FileStore> project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot import Bot
from database.database import db
import logging
from config import OWNER_ID
from asyncio import TimeoutError
import re
import asyncio

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Small caps conversion dictionary
SMALL_CAPS = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ',
    'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
    'q': 'Q', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ'
}

def to_small_caps_with_html(text: str) -> str:
    """Convert text to small caps font style while preserving HTML tags."""
    result = ""
    i = 0
    while i < len(text):
        if text[i] == '<':
            j = i + 1
            while j < len(text) and text[j] != '>':
                j += 1
            if j < len(text):
                result += text[i:j+1]
                i = j + 1
            else:
                result += text[i]
                i += 1
        else:
            result += SMALL_CAPS.get(text[i].lower(), text[i])
            i += 1
    return result

# Store user data for broadcast and delete states
cast_user_data = {}

# Filter for cast input
async def cast_input_filter(_: None, __: None, message: Message) -> bool:
    """Filter to ensure messages are processed when awaiting cast input."""
    user_id = message.from_user.id
    if user_id not in cast_user_data:
        logger.info(f"cast_input_filter: No cast data for user {user_id}")
        return False
    state = cast_user_data[user_id].get('state', '')
    is_valid = state == 'awaiting_cast_message'
    logger.info(f"cast_input_filter for user {user_id}: state={state}, message_text={message.text or 'None'}, is_valid={is_valid}")
    return is_valid

# Filter for delete duration input
async def delete_duration_filter(_: None, __: None, message: Message) -> bool:
    """Filter to ensure messages are processed when awaiting delete duration."""
    user_id = message.from_user.id
    if user_id not in cast_user_data:
        logger.info(f"delete_duration_filter: No cast data for user {user_id}")
        return False
    state = cast_user_data[user_id].get('state', '')
    is_valid = state == 'awaiting_delete_duration' and re.match(r"^\d+$", message.text or "")
    logger.info(f"delete_duration_filter for user {user_id}: state={state}, message_text={message.text or 'None'}, is_valid={is_valid}")
    return is_valid

@Bot.on_message(filters.private & filters.command('cast') & filters.user(OWNER_ID))
async def cast_command(client: Client, message: Message):
    """Handle /cast command to start a broadcast."""
    user_id = message.from_user.id
    logger.info(f"Received /cast command from user {user_id}")

    cast_user_data[user_id] = {
        'state': 'awaiting_cast_message',
        'menu_message': None,
        'broadcast_message': None,
        'delete_duration': None
    }

    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Please send the message you want to broadcast.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )
    msg = await message.reply(
        text=text,
        parse_mode=ParseMode.HTML
    )
    cast_user_data[user_id]['menu_message'] = msg

@Bot.on_message(filters.create(cast_input_filter))
async def handle_cast_input(client: Client, message: Message):
    """Handle the message to be broadcasted."""
    user_id = message.from_user.id
    logger.info(f"Handling cast input for user {user_id}")

    try:
        if user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❖ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        # Store the message to broadcast
        cast_user_data[user_id]['broadcast_message'] = message
        cast_user_data[user_id]['state'] = 'awaiting_cast_confirmation'

        # Create buttons for confirmation
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("• Send Now •", callback_data="cast_send"),
                InlineKeyboardButton("• Delete After •", callback_data="cast_delete")
            ],
            [
                InlineKeyboardButton("• Cancel •", callback_data="cast_cancel")
            ]
        ])

        await message.reply(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<blockquote><b>Confirm the broadcast message.</b></blockquote>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )

        # Delete the menu message
        if cast_user_data[user_id]['menu_message']:
            await cast_user_data[user_id]['menu_message'].delete()

    except Exception as e:
        logger.error(f"Error in handle_cast_input for user {user_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❖ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in cast_user_data:
            del cast_user_data[user_id]

@Bot.on_callback_query(filters.regex(r"^cast_"))
async def cast_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for cast command."""
    user_id = callback.from_user.id
    data = callback.data
    logger.info(f"Received cast callback query with data: {data} in chat {user_id}")

    try:
        if user_id != OWNER_ID:
            await callback.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        if data == "cast_send":
            if user_id not in cast_user_data or 'broadcast_message' not in cast_user_data[user_id]:
                await callback.answer(to_small_caps_with_html("No message to broadcast!"), show_alert=True)
                return

            # Perform the broadcast
            broadcast_message = cast_user_data[user_id]['broadcast_message']
            users = await db.get_all_users()  # Assuming db.get_all_users() retrieves user IDs
            success_count = 0
            failed_count = 0

            for user in users:
                try:
                    await broadcast_message.copy(chat_id=user['id'])
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send broadcast to user {user['id']}: {e}")
                    failed_count += 1

            await callback.message.edit_text(
                to_small_caps_with_html(
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    f"<blockquote><b>Broadcast completed!</b></blockquote>\n"
                    f"<b>Success: {success_count} users</b>\n"
                    f"<b>Failed: {failed_count} users</b>\n"
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            if user_id in cast_user_data:
                del cast_user_data[user_id]
            await callback.answer(to_small_caps_with_html("Broadcast sent!"))

        elif data == "cast_delete":
            cast_user_data[user_id]['state'] = 'awaiting_delete_duration'
            await db.set_temp_state(user_id, 'awaiting_delete_duration')  # Store state in database
            await callback.message.edit_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<blockquote><b>Please send the duration (in minutes) after which the broadcast message should be deleted.</b></blockquote>\n"
                    "<b>Example: 20</b>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• Cancel •", callback_data="cast_cancel")]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer(to_small_caps_with_html("Enter duration in minutes"))

        elif data == "cast_cancel":
            if user_id in cast_user_data:
                await db.clear_temp_state(user_id)
                del cast_user_data[user_id]
            await callback.message.edit_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<b>❌ Broadcast cancelled!</b>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            await callback.answer(to_small_caps_with_html("Broadcast cancelled"))

    except Exception as e:
        logger.error(f"Error in cast_callback for user {user_id}: {e}")
        await callback.message.edit_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❖ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in cast_user_data:
            await db.clear_temp_state(user_id)
            del cast_user_data[user_id]

@Bot.on_message(filters.create(delete_duration_filter))
async def handle_delete_duration_input(client: Client, message: Message):
    """Handle the duration input for deleting broadcast messages."""
    user_id = message.from_user.id
    logger.info(f"Handling delete duration input for user {user_id}, input: {message.text}")

    try:
        if user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❖ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        duration = int(message.text)
        if duration <= 0:
            await message.reply(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<blockquote><b>Please send a valid duration (greater than 0).</b></blockquote>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            return

        # Store the duration
        cast_user_data[user_id]['delete_duration'] = duration
        cast_user_data[user_id]['state'] = 'awaiting_cast_confirmation'

        # Perform the broadcast with delete option
        broadcast_message = cast_user_data[user_id]['broadcast_message']
        users = await db.get_all_users()
        success_count = 0
        failed_count = 0
        message_ids = []

        for user in users:
            try:
                sent_message = await broadcast_message.copy(chat_id=user['id'])
                message_ids.append((user['id'], sent_message.id))
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user['id']}: {e}")
                failed_count += 1

        # Send confirmation
        await message.reply(
            to_small_caps_with_html(
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                f"<blockquote><b>Broadcast completed with auto-delete after {duration} minutes!</b></blockquote>\n"
                f"<b>Success: {success_count} users</b>\n"
                f"<b>Failed: {failed_count} users</b>\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )

        # Schedule deletion
        await asyncio.sleep(duration * 60)  # Convert minutes to seconds
        for chat_id, msg_id in message_ids:
            try:
                await client.delete_messages(chat_id=chat_id, message_ids=msg_id)
                logger.info(f"Deleted message {msg_id} in chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to delete message {msg_id} in chat {chat_id}: {e}")

        # Clean up user data
        if user_id in cast_user_data:
            await db.clear_temp_state(user_id)
            del cast_user_data[user_id]

    except ValueError:
        await message.reply(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<blockquote><b>Please send a valid number for duration.</b></blockquote>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in handle_delete_duration_input for user {user_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❖ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in cast_user_data:
            await db.clear_temp_state(user_id)
            del cast_user_data[user_id]

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, <https://github.com/AnimeLord-Bots>.
#
# This file is part of <https://github.com/AnimeLord-Bots/FileStore> project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#
