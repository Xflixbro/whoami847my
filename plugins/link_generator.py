#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.enums import ParseMode
from bot import Bot
from helper_func import encode, get_message_id, admin
import re
from typing import Dict
import logging
from config import OWNER_ID
from database.database import db
from asyncio import TimeoutError
import random  # Added for random image selection in /link command

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

# Store user data for batch, genlink, custom_batch, and flink commands
batch_user_data: Dict[int, Dict] = {}
genlink_user_data: Dict[int, Dict] = {}  # Added for /genlink command
custom_batch_user_data: Dict[int, Dict] = {}  # Added for /custom_batch command
flink_user_data: Dict[int, Dict] = {}

# List of image URLs for /link command (you can replace these with your own image URLs)
IMAGE_URLS = [
    "https://i.postimg.cc/JnJ32yfG/1813ee0c.jpg",
    "https://i.postimg.cc/0j0Y9T2v/28b1fa77.jpg",
    "https://i.postimg.cc/sxrPdjzK/169123a1.jpg",
    "https://i.postimg.cc/pTNzzWmx/6592fdce.jpg",
    "https://i.postimg.cc/Wbsm51X1/e6afff7a.jpg",
    "https://i.postimg.cc/8zV2KWxr/dc021327.jpg",
    "https://i.postimg.cc/Wb9ZS6d5/bca92b0b.jpg",
    "https://i.postimg.cc/9MtR9G3t/c4b45c9f.jpg",
    "https://i.postimg.cc/0yMzngRN/ce1ae80f.jpg",
    "https://i.postimg.cc/NFdKJBjK/f8ca42f6.jpg",
    "https://i.postimg.cc/5Njy9ctm/ec4acf97.jpg",
    "https://i.postimg.cc/Kj8zgwDx/04efc805.jpg",
    "https://i.postimg.cc/13jpRcP8/f2ce6fdf.jpg",
    "https://i.postimg.cc/L5JSSpVY/af94fb0f.jpg",
    "https://i.postimg.cc/YSQhc1SK/06dc3bf7.jpg",
    "https://i.postimg.cc/TwGhTpyy/99376c97.jpg",
    "https://i.postimg.cc/HxxD0gRZ/ae49a6f5.jpg",
    "https://i.postimg.cc/K8S26C3j/fdee09a7.jpg",
    "https://i.postimg.cc/90shFnxx/7963dd00.jpg",
    "https://i.postimg.cc/j5ZqKv09/1c847bb6.jpg",
]

# Filter for batch command input
async def batch_state_filter(_, __, message: Message):
    """Filter to ensure messages are processed only when awaiting batch input."""
    chat_id = message.chat.id
    if chat_id not in batch_user_data:
        logger.info(f"batch_state_filter: No batch data for chat {chat_id}")
        return False
    state = batch_user_data[chat_id].get('state')
    logger.info(f"batch_state_filter for chat {chat_id}: state={state}, message_text={message.text}")
    return state in ['awaiting_first_message', 'awaiting_second_message'] and (message.forward_from_chat or re.match(r"^https?://t\.me/.*$", message.text))

# Filter for genlink command input
async def genlink_state_filter(_, __, message: Message):
    """Filter to ensure messages are processed only when awaiting genlink input."""
    chat_id = message.chat.id
    if chat_id not in genlink_user_data:
        logger.info(f"genlink_state_filter: No genlink data for chat {chat_id}")
        return False
    state = genlink_user_data[chat_id].get('state')
    logger.info(f"genlink_state_filter for chat {chat_id}: state={state}, message_text={message.text}")
    return state == 'awaiting_message' and (message.forward_from_chat or re.match(r"^https?://t\.me/.*$", message.text))

# Filter for custom_batch command input
async def custom_batch_state_filter(_, __, message: Message):
    """Filter to ensure messages are processed only when awaiting custom_batch input."""
    chat_id = message.chat.id
    if chat_id not in custom_batch_user_data:
        logger.info(f"custom_batch_state_filter: No custom_batch data for chat {chat_id}")
        return False
    state = custom_batch_user_data[chat_id].get('state')
    logger.info(f"custom_batch_state_filter for chat {chat_id}: state={state}, message_text={message.text}")
    return state == 'collecting_messages'

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_command(client: Client, message: Message):
    """Handle /link command to show a menu with buttons to trigger other commands."""
    logger.info(f"Link command triggered by user {message.from_user.id}")
    
    # Select a random image from IMAGE_URLS
    random_image = random.choice(IMAGE_URLS)
    
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>If you want to generate link for files then use those buttons according to your need.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ʙᴀᴛᴄʜ", callback_data="batch_start_process"),
            InlineKeyboardButton("ɢᴇɴʟɪɴᴋ", callback_data="genlink_start_process")
        ],
        [
            InlineKeyboardButton("ᴄᴜsᴛᴏᴍ", callback_data="custom_batch_start_process"),
            InlineKeyboardButton("ꜰʟɪɴᴋ", callback_data="flink_start_process")
        ],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="link_close")]
    ])
    
    await message.reply_photo(
        photo=random_image,
        caption=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex(r"^link_(trigger_batch|trigger_genlink|trigger_custom|trigger_flink|close)$"))
async def link_handle_callbacks(client: Client, query: CallbackQuery):
    """Handle callbacks for /link command buttons."""
    chat_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Link {action} callback triggered by user {chat_id}")
    
    if action == "trigger_batch":
        await batch(client, query.message)
        await query.answer(to_small_caps_with_html("Batch command started"))
    elif action == "trigger_genlink":
        await link_generator(client, query.message)
        await query.answer(to_small_caps_with_html("Genlink command started"))
    elif action == "trigger_custom":
        await custom_batch(client, query.message)
        await query.answer(to_small_caps_with_html("Custom batch command started"))
    elif action == "trigger_flink":
        await flink_command(client, query.message)
        await query.answer(to_small_caps_with_html("Flink command started"))
    elif action == "close":
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    chat_id = message.from_user.id
    logger.info(f"Batch command triggered by user {chat_id}")

    # Initialize batch user data
    batch_user_data[chat_id] = {
        'state': 'initial',
        'first_message_id': None,
        'menu_message': None
    }

    # Show the batch menu with Start Process button
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Batch Link Generator</b></blockquote>\n\n"
        "<blockquote><b>Click 'Start Process' to begin generating a batch link.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• Start Process •", callback_data="batch_start_process")],
        [InlineKeyboardButton("• Close •", callback_data="batch_close")]
    ])

    msg = await message.reply(
        text=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )
    batch_user_data[chat_id]['menu_message'] = msg

@Bot.on_callback_query(filters.regex(r"^batch_start_process$"))
async def batch_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the batch process."""
    chat_id = query.from_user.id
    logger.info(f"Batch start process callback triggered by user {chat_id}")

    if chat_id not in batch_user_data:
        batch_user_data[chat_id] = {
            'state': 'awaiting_first_message',
            'first_message_id': None,
            'menu_message': query.message
        }
    else:
        batch_user_data[chat_id]['state'] = 'awaiting_first_message'

    await query.message.edit_text(
        to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Forward the first message from db channel (with quotes).</b></blockquote>\n"
            "<blockquote><b>Or send the db channel post link</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✖️ Cancel", callback_data="batch_cancel_process")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Send the first message or link"))

@Bot.on_callback_query(filters.regex(r"^batch_(cancel_process|close)$"))
async def batch_handle_cancel_close(client: Client, query: CallbackQuery):
    """Handle cancel and close actions for batch command."""
    chat_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Batch {action} callback triggered by user {chat_id}")

    if action == "cancel_process":
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await query.answer(to_small_caps_with_html("Process cancelled"))
    elif action == "close":
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.create(batch_state_filter))
async def handle_batch_input(client: Client, message: Message):
    """Handle input for batch command based on state."""
    chat_id = message.from_user.id
    state = batch_user_data.get(chat_id, {}).get('state')
    logger.info(f"Handling batch input for chat {chat_id}, state: {state}")

    try:
        if state == 'awaiting_first_message':
            f_msg_id = await get_message_id(client, message)
            if not f_msg_id:
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            batch_user_data[chat_id]['first_message_id'] = f_msg_id
            batch_user_data[chat_id]['state'] = 'awaiting_second_message'
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_second_message':
            s_msg_id = await get_message_id(client, message)
            if not s_msg_id:
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            f_msg_id = batch_user_data[chat_id]['first_message_id']
            string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

            # Modified: Removed small caps for the link output
            await message.reply_text(
                f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
                quote=True,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

            # Clean up user data
            if chat_id in batch_user_data:
                del batch_user_data[chat_id]

    except TimeoutError:
        logger.error(f"Timeout error waiting for batch input in state {state} for user {chat_id}")
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]
    except Exception as e:
        logger.error(f"Error in handle_batch_input for user {chat_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    chat_id = message.from_user.id
    logger.info(f"Genlink command triggered by user {chat_id}")

    # Added: Initialize genlink user data
    genlink_user_data[chat_id] = {
        'state': 'initial',
        'menu_message': None
    }

    # Added: Show the genlink menu with Start Process button
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Single Link Generator</b></blockquote>\n\n"
        "<blockquote><b>Click 'Start Process' to begin generating a single message link.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• Start Process •", callback_data="genlink_start_process")],
        [InlineKeyboardButton("• Close •", callback_data="genlink_close")]
    ])

    msg = await message.reply(
        text=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )
    genlink_user_data[chat_id]['menu_message'] = msg

@Bot.on_callback_query(filters.regex(r"^genlink_start_process$"))
async def genlink_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the genlink process."""
    chat_id = query.from_user.id
    logger.info(f"Genlink start process callback triggered by user {chat_id}")

    if chat_id not in genlink_user_data:
        genlink_user_data[chat_id] = {
            'state': 'awaiting_message',
            'menu_message': query.message
        }
    else:
        genlink_user_data[chat_id]['state'] = 'awaiting_message'

    await query.message.edit_text(
        to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Forward message from the db channel (with quotes).</b></blockquote>\n"
            "<blockquote><b>Or send the db channel post link</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✖️ Cancel", callback_data="genlink_cancel_process")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Send the message or link"))

@Bot.on_callback_query(filters.regex(r"^genlink_(cancel_process|close)$"))
async def genlink_handle_cancel_close(client: Client, query: CallbackQuery):
    """Handle cancel and close actions for genlink command."""
    chat_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Genlink {action} callback triggered by user {chat_id}")

    if action == "cancel_process":
        if chat_id in genlink_user_data:
            del genlink_user_data[chat_id]
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await query.answer(to_small_caps_with_html("Process cancelled"))
    elif action == "close":
        if chat_id in genlink_user_data:
            del genlink_user_data[chat_id]
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.create(genlink_state_filter))
async def handle_genlink_input(client: Client, message: Message):
    """Handle input for genlink command."""
    chat_id = message.from_user.id
    logger.info(f"Handling genlink input for chat {chat_id}")

    try:
        msg_id = await get_message_id(client, message)
        if not msg_id:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                quote=True,
                parse_mode=ParseMode.HTML
            )
            return

        base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

        # Modified: Removed small caps for the link output
        await message.reply_text(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
            quote=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        # Clean up user data
        if chat_id in genlink_user_data:
            del genlink_user_data[chat_id]

    except TimeoutError:
        logger.error(f"Timeout error waiting for genlink input for user {chat_id}")
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in genlink_user_data:
            del genlink_user_data[chat_id]
    except Exception as e:
        logger.error(f"Error in handle_genlink_input for user {chat_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in genlink_user_data:
            del genlink_user_data[chat_id]

@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    """Handle /custom_batch command to collect and generate a batch link."""
    chat_id = message.from_user.id
    logger.info(f"Custom batch command triggered by user {chat_id}")

    # Added: Initialize custom_batch user data
    custom_batch_user_data[chat_id] = {
        'state': 'initial',
        'menu_message': None,
        'collected': []
    }

    # Added: Show the custom_batch menu with Start Process button
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Custom Batch Link Generator</b></blockquote>\n\n"
        "<blockquote><b>Click 'Start Process' to begin collecting messages for a batch link.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("• Start Process •", callback_data="custom_batch_start_process")],
        [InlineKeyboardButton("• Close •", callback_data="custom_batch_close")]
    ])

    msg = await message.reply(
        text=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )
    custom_batch_user_data[chat_id]['menu_message'] = msg

@Bot.on_callback_query(filters.regex(r"^custom_batch_start_process$"))
async def custom_batch_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the custom_batch process."""
    chat_id = query.from_user.id
    logger.info(f"Custom batch start process callback triggered by user {chat_id}")

    if chat_id not in custom_batch_user_data:
        custom_batch_user_data[chat_id] = {
            'state': 'collecting_messages',
            'menu_message': query.message,
            'collected': []
        }
    else:
        custom_batch_user_data[chat_id]['state'] = 'collecting_messages'
        custom_batch_user_data[chat_id]['collected'] = []

    await query.message.edit_text(
        to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Send all messages you want to include in batch.</b></blockquote>\n\n"
            "<blockquote><b>Press Stop when you're done.</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        ),
        reply_markup=ReplyKeyboardMarkup([["stop"]], resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Start sending messages"))

@Bot.on_callback_query(filters.regex(r"^custom_batch_(cancel_process|close)$"))
async def custom_batch_handle_cancel_close(client: Client, query: CallbackQuery):
    """Handle cancel and close actions for custom_batch command."""
    chat_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Custom batch {action} callback triggered by user {chat_id}")

    if action == "cancel_process":
        if chat_id in custom_batch_user_data:
            del custom_batch_user_data[chat_id]
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await query.answer(to_small_caps_with_html("Process cancelled"))
    elif action == "close":
        if chat_id in custom_batch_user_data:
            del custom_batch_user_data[chat_id]
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.create(custom_batch_state_filter))
async def handle_custom_batch_input(client: Client, message: Message):
    """Handle input for custom_batch command."""
    chat_id = message.from_user.id
    logger.info(f"Handling custom batch input for chat {chat_id}")

    try:
        if message.text and message.text.strip().lower() == "stop":
            collected = custom_batch_user_data[chat_id]['collected']
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML
            )

            if not collected:
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No messages were added to batch.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    parse_mode=ParseMode.HTML
                )
                return

            start_id = collected[0] * abs(client.db_channel.id)
            end_id = collected[-1] * abs(client.db_channel.id)
            string = f"get-{start_id}-{end_id}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

            # Modified: Removed small caps for the link output
            await message.reply(
                f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

            # Clean up user data
            if chat_id in custom_batch_user_data:
                del custom_batch_user_data[chat_id]
            return

        try:
            sent = await message.copy(client.db_channel.id, disable_notification=True)
            custom_batch_user_data[chat_id]['collected'].append(sent.id)
        except Exception as e:
            await message.reply(
                to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            logger.error(f"Error storing message in custom_batch: {e}")
            return

    except TimeoutError:
        logger.error(f"Timeout error waiting for custom_batch input for user {chat_id}")
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in custom_batch_user_data:
            del custom_batch_user_data[chat_id]
    except Exception as e:
        logger.error(f"Error in handle_custom_batch_input for user {chat_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in custom_batch_user_data:
            del custom_batch_user_data[chat_id]

@Bot.on_message(filters.private & admin & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    logger.info(f"Flink command triggered by user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        flink_user_data[message.from_user.id] = {
            'format': None,
            'links': {},
            'edit_data': {},
            'menu_message': None,
            'output_message': None,
            'caption_prompt_message': None,
            'awaiting_format': False,
            'awaiting_caption': False,
            'awaiting_db_post': False
        }
        
        # Modified: Show the flink menu with Start Process button
        text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Formatted Link Generator</b></blockquote>\n\n"
            "<blockquote><b>Click 'Start Process' to begin generating formatted links.</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("• Start Process •", callback_data="flink_start_process")],
            [InlineKeyboardButton("• Close •", callback_data="flink_close")]
        ])

        msg = await message.reply(
            text=text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
        flink_user_data[message.from_user.id]['menu_message'] = msg
    except Exception as e:
        logger.error(f"Error in flink_command: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    """Show the main menu for the flink command."""
    try:
        current_format = flink_user_data[message.from_user.id]['format'] or "Not set"
        text = to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Formatted Link Generator</b>\n\n<blockquote><b>Current format:</b></blockquote>\n<blockquote><code>{current_format}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>")
        
        buttons = [
            [
                InlineKeyboardButton("• sᴇᴛ ғᴏʀᴍᴀᴛ •", callback_data="flink_set_format"),
                InlineKeyboardButton("• sᴛᴀʀᴛ ᴘʀᴏᴄᴇss •", callback_data="flink_start_process")
            ],
            [
                InlineKeyboardButton("• ʀᴇғʀᴇsʜ •", callback_data="flink_refresh"),
                InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="flink_close")
            ]
        ]
        
        if edit:
            if message.text != text or message.reply_markup != InlineKeyboardMarkup(buttons):
                msg = await message.edit_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML
                )
                flink_user_data[message.from_user.id]['menu_message'] = msg
            else:
                logger.info(f"Skipping edit in show_flink_main_menu for user {message.from_user.id} - content unchanged")
        else:
            msg = await message.reply(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            flink_user_data[message.from_user.id]['menu_message'] = msg
    except Exception as e:
        logger.error(f"Error in show_flink_main_menu: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing menu.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle callback for setting format in flink command."""
    logger.info(f"Flink_set_format callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        flink_user_data[query.from_user.id]['awaiting_format'] = True
        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Please send your format in this pattern:</b></blockquote>\n\n"
            "<blockquote>Example</blockquote>:\n\n"
            "<blockquote>don't copy this. please type</blockquote>:\n"
            "<blockquote><code>360p = 2, 720p = 2, 1080p = 2, 4k = 2, HDRIP = 2</code></blockquote>\n\n"
            "<blockquote><b>Meaning:</b></blockquote>\n"
            "<b>- 360p = 2 → 2 video files for 360p quality</b>\n"
            "<blockquote><b>- If stickers/gifs follow, they will be included in the link\n"
            "- Only these qualities will be created</b></blockquote>\n\n"
            "<b>Send the format in the next message (no need to reply).</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="flink_back_to_menu")]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in flink_set_format_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Enter format"))
    except Exception as e:
        logger.error(f"Error in flink_set_format_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while setting format.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink command."""
    logger.info(f"Format input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_format'):
            format_text = message.text.strip()
            flink_user_data[user_id]['format'] = format_text
            flink_user_data[user_id]['awaiting_format'] = False
            await message.reply_text(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Format saved successfully:</b></blockquote>\n<code>{format_text}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            await show_flink_main_menu(client, message)
        else:
            logger.info(f"Format input ignored for user {message.from_user.id} - not awaiting format")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Please use the 'Set Format' option first and provide a valid format</b></blockquote>\n<blockquote>Example:</blockquote> <code>360p = 2, 720p = 1</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in handle_format_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing format.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_start_process$"))
async def flink_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the flink process."""
    logger.info(f"Flink_start_process callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        if not flink_user_data[query.from_user.id]['format']:
            await query.answer(to_small_caps_with_html("❌ Please set format first!"), show_alert=True)
            return
        
        flink_user_data[query.from_user.id]['awaiting_db_post'] = True
        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Send the first post link from db channel:</b></blockquote>\n"
            "<blockquote><b>Forward a message from the db channel or send its direct link (e.g., <code>t.me/channel/123</code>).</b></blockquote>\n\n"
            "<blockquote><b>Ensure files are in sequence without gaps.</b></blockquote>\n\n"
            "<b>Send the link or forwarded message in the next message (no need to reply).</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖️ Cancel", callback_data="flink_cancel_process")]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in flink_start_process_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Send db channel post"))
    except Exception as e:
        logger.error(f"Error in flink_start_process_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while starting process.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & (filters.forwarded | filters.regex(r"^https?://t\.me/.*$")))
async def handle_db_post_input(client: Client, message: Message):
    """Handle db channel post input for flink command."""
    logger.info(f"DB post input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_db_post'):
            logger.info(f"DB post input ignored for user {user_id} - not awaiting db channel input")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Please use the 'Start Process' option first and provide a valid forwarded message or link from the db channel.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        msg_id = await get_message_id(client, message)
        if not msg_id:
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Invalid db channel post! Ensure it's a valid forwarded message or link from the db channel.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
                
        format_str = flink_user_data[message.from_user.id]['format']
        format_parts = [part.strip() for part in format_str.split(",")]
        
        current_id = msg_id
        links = {}
        
        for part in format_parts:
            match = re.match(r"([a-zA-Z0-9]+)\s*=\s*(\d+)", part)
            if not match:
                await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Invalid format part:</b> <code>{part}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                return
            quality, count = match.groups()
            quality = quality.strip().upper()
            count = int(count.strip())
            
            # Modified: Handle missing IDs by finding the next available ID
            valid_ids = []
            temp_id = current_id
            ids_checked = 0
            while len(valid_ids) < count and ids_checked < count * 2:  # Limit checks to prevent infinite loops
                try:
                    msg = await client.get_messages(client.db_channel.id, temp_id)
                    if msg.video or msg.document:
                        valid_ids.append(temp_id)
                    temp_id += 1
                    ids_checked += 1
                except Exception as e:
                    logger.info(f"Skipping missing message ID {temp_id}: {e}")
                    temp_id += 1
                    ids_checked += 1
            
            if len(valid_ids) < count:
                logger.error(f"Not enough valid media files found for {quality}: required {count}, found {len(valid_ids)}")
                await message.reply(
                    to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Not enough valid media files for {quality}: required {count}, found {len(valid_ids)}</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    parse_mode=ParseMode.HTML
                )
                return
            
            end_id = valid_ids[-1]
            
            additional_count = 0
            next_id = end_id + 1
            try:
                next_msg = await client.get_messages(client.db_channel.id, next_id)
                if next_msg.sticker or next_msg.animation:
                    additional_count = 1
                    end_id = next_id
            except Exception as e:
                logger.info(f"No additional sticker/gif found at id {next_id}: {e}")
            
            links[quality] = {
                'start': valid_ids[0],
                'end': end_id,
                'count': len(valid_ids) + additional_count
            }
            
            current_id = end_id + 1
            logger.info(f"Processed {quality}: start={links[quality]['start']}, end={links[quality]['end']}, total files={links[quality]['count']}")
        
        flink_user_data[message.from_user.id]['links'] = links
        flink_user_data[message.from_user.id]['awaiting_db_post'] = False
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_db_post_input: {e}")
        await message.reply_text(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\nPlease ensure the input is valid and try again.\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def flink_generate_final_output(client: Client, message: Message):
    """Generate the final output for flink command with download buttons."""
    logger.info(f"Generating final output for user {message.from_user.id}")
    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error("No links generated in flink_user_data")
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No links generated. Please check the input and try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]]))
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", url=await create_link(client, links[quality_list[3]]))
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", url=await create_link(client, links[quality_list[3]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[4]} 🦋", url=await create_link(client, links[quality_list[4]]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineKeyboardButton(f"🦋 {quality} 🦋", url=await create_link(client, links[quality]))
                ])
        
        buttons.append([
            InlineKeyboardButton("◈ Edit ◈", callback_data="flink_edit_output"),
            InlineKeyboardButton("✅ Done", callback_data="flink_done_output")
        ])
        
        edit_data = flink_user_data[user_id].get('edit_data', {})
        caption = edit_data.get('caption', '')
        
        if edit_data.get('image'):
            output_msg = await message.reply_photo(
                photo=edit_data['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            output_msg = await message.reply(
                text=caption if caption else to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n</blockquote><b>Here are your download buttons:</blockquote></b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(f"Error in flink_generate_final_output: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while generating output. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def create_link(client: Client, link_data: Dict) -> str:
    """Create a Telegram link for a range of message IDs."""
    start_id = link_data['start'] * abs(client.db_channel.id)
    end_id = link_data['end'] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    return f"https://t.me/{client.username}?start={base64_string}"

@Bot.on_callback_query(filters.regex(r"^flink_edit_output$"))
async def flink_edit_output_callback(client: Client, query: CallbackQuery):
    """Handle callback for editing flink output."""
    logger.info(f"Flink_edit_output callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>Add optional elements to the output:</b>\n\n"
            "Send an image or type a caption separately.\n"
            "<b>━━━━━━━━━━━━━━━━━━</b>"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("◈ Image ◈", callback_data="flink_add_image"),
                        InlineKeyboardButton("◈ Caption ◈", callback_data="flink_add_caption")
                    ],
                    [
                        InlineKeyboardButton("✔️ Finish setup 🦋", callback_data="flink_done_output")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in flink_edit_output_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer()
    except Exception as e:
        logger.error(f"Error in flink_edit_output_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while editing output.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding an image to flink output."""
    logger.info(f"Flink_add_image callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send the image:</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>")
        
        if current_text != new_text:
            await query.message.edit_text(new_text, parse_mode=ParseMode.HTML)
        else:
            logger.info(f"Skipping edit in flink_add_image_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Send image"))
    except Exception as e:
        logger.error(f"Error in flink_add_image_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ An error occurred while adding image.</blockquote></b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.photo & filters.reply)
async def handle_image_input(client: Client, message: Message):
    """Handle image input for flink output."""
    logger.info(f"Image input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data:
            flink_user_data[user_id] = {
                'format': None,
                'links': {},
                'edit_data': {},
                'menu_message': None,
                'output_message': None,
                'caption_prompt_message': None,
                'awaiting_format': False,
                'awaiting_caption': False,
                'awaiting_db_post': False
            }
        elif 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}

        if not (message.reply_to_message and to_small_caps_with_html("send the image:") in message.reply_to_message.text.lower()):
            logger.info(f"Image input ignored for user {user_id} - not a reply to image prompt")
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the image prompt with a valid image.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Image saved successfully.</b></blockquote>\n<blockquote>Type a caption if needed, or proceed with 'Done'.</blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_image_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing image.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding a caption to flink output."""
    logger.info(f"Flink_add_caption callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        flink_user_data[user_id]['awaiting_caption'] = True
        caption_prompt_text = (
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Type your caption:</b></blockquote>\n\n")
            + "<blockquote><b>Example:</b></blockquote>\n\n"
            "<blockquote><code>ᴛɪᴛʟᴇ- BLACK CLOVER\n"
            "Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅɪ Dᴜʙʙᴇᴅ\n\n"
            "Qᴜᴀʟɪᴛʏ - 360ᴘ, 720�禄, 1080ᴘ\n\n"
            "Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n"
            "Aʟʟ Qᴜᴀʟɪᴛʏ - ( Hɪɴᴅɪ Dᴜʙʙᴇᴅ )\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Cʟɪᴄᴋ Hᴇʀᴇ Tᴏ Dᴏᴡɴʟᴏᴀᴅ | Eᴘ - 01 & S1</code></blockquote>\n\n"
            + to_small_caps_with_html("<blockquote><b>Reply to this message with your caption.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>")
        )
        
        caption_prompt_msg = await query.message.reply_text(caption_prompt_text, parse_mode=ParseMode.HTML)
        flink_user_data[user_id]['caption_prompt_message'] = caption_prompt_msg
        
        await query.answer(to_small_caps_with_html("Type caption"))
    except Exception as e:
        logger.error(f"Error in flink_add_caption_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while adding caption.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.reply & ~filters.regex(r"^CANCEL$") & ~filters.forwarded)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for flink command."""
    logger.info(f"Caption input received from user {message.from_user.id}, text: {message.text}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No active caption prompt found. Please use the 'Add Caption' option first.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        caption_prompt_msg = flink_user_data[user_id].get('caption_prompt_message')
        if not caption_prompt_msg or not message.reply_to_message or message.reply_to_message.id != caption_prompt_msg.id:
            logger.info(f"Caption input ignored for user {message.from_user.id} - not a reply to caption prompt")
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the caption prompt message with your caption.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.text
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Caption saved successfully.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_caption_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing caption.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output_callback(client: Client, query: CallbackQuery):
    """Handle callback for finalizing flink output."""
    logger.info(f"Flink_done_output callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id not in flink_user_data or 'links' not in flink_user_data[user_id]:
            await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ No links found. Please start the process again using /flink.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        links = flink_user_data[user_id]['links']
        edit_data = flink_user_data[user_id].get('edit_data', {})
        caption = edit_data.get('caption', '')
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]]))
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", url=await create_link(client, links[quality_list[3]]))
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", url=await create_link(client, links[quality_list[3]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[4]} 🦋", url=await create_link(client, links[quality_list[4]]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineKeyboardButton(f"🦋 {quality} 🦋", url=await create_link(client, links[quality]))
                ])
        
        if edit_data.get('image'):
            await query.message.reply_photo(
                photo=edit_data['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await query.message.reply(
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        if user_id in flink_user_data:
            del flink_user_data[user_id]
        await query.answer(to_small_caps_with_html("Process completed"))
    except Exception as e:
        logger.error(f"Error in flink_done_output_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while completing process.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Handle callback to refresh flink menu."""
    logger.info(f"Flink_refresh callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Format status refreshed"))
    except Exception as e:
        logger.error(f"Error in flink_refresh_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while refreshing status.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_(back_to_menu|cancel_process|back_to_output|close)$"))
async def flink_handle_back_buttons(client: Client, query: CallbackQuery):
    """Handle back, cancel, and close actions for flink command."""
    logger.info(f"Flink back/cancel/close callback triggered by user {query.from_user.id} with action {query.data}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        action = query.data.split("_")[-1]
        
        if action == "back_to_menu":
            await show_flink_main_menu(client, query.message, edit=True)
            await query.answer(to_small_caps_with_html("Back to menu"))
        elif action == "cancel_process":
            await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            if query.from_user.id in flink_user_data:
                del flink_user_data[query.from_user.id]
            await query.answer(to_small_caps_with_html("Process cancelled"))
        elif action == "back_to_output":
            await flink_generate_final_output(client, query.message)
            await query.answer(to_small_caps_with_html("Back to output"))
        elif action == "close":
            await query.message.delete()
            if query.from_user.id in flink_user_data:
                del flink_user_data[query.from_user.id]
            await query.answer(to_small_caps_with_html("Menu closed"))
    except Exception as e:
        logger.error(f"Error in flink_handle_back_buttons: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing action.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
