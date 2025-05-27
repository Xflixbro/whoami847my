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
from pyrogram.errors import UserIsBot
from bot import Bot
from helper_func import encode, get_message_id, admin
import re
from typing import Dict
import logging
from config import OWNER_ID, RANDOM_IMAGES
import random
from database.database import db
from asyncio import TimeoutError

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

# Store user data for batch and flink commands
batch_user_data: Dict[int, Dict] = {}
flink_user_data: Dict[int, Dict] = {}

# Filter for batch command input
async def batch_state_filter(_, __, message: Message):
    """Filter to ensure messages are processed only when awaiting batch input."""
    chat_id = message.chat.id
    if chat_id not in batch_user_data:
        logger.info(f"batch_state_filter: No batch data for chat {chat_id}")
        return False
    state = batch_user_data[chat_id].get('state')
    logger.info(f"batch_state_filter for chat {chat_id}: state={state}, message_text={message.text}")
    return state in ['awaiting_first_message', 'awaiting_second_message'] and (message.forward_from_chat or re.match(r'^https?://t\.me/.*$', message.text or ''))

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_command(client: Client, message: Message):
    """Handle /link command to display a menu with buttons to trigger link generation commands."""
    logger.info(f"Link command triggered by user {message.from_user.id}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    # Prepare the message text
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>If you want to generate link for files then use those buttons according to your need.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    # Define the button layout
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• ʙᴀᴛᴄʜ •", callback_data="link_batch"),
            InlineKeyboardButton("• ɢᴇɴʟɪɴᴋ •", callback_data="link_genlink")
        ],
        [
            InlineKeyboardButton("• ᴄᴜsᴛᴏᴍ •", callback_data="link_custom_batch"),
            InlineKeyboardButton("• ꜰʟɪɴᴋ •", callback_data="link_flink")
        ],
        [
            InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="link_close")
        ]
    ])

    # Select a random image from RANDOM_IMAGES
    random_image = random.choice(RANDOM_IMAGES)

    # Send the message with the random image and buttons
    await message.reply_photo(
        photo=random_image,
        caption=text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex(r"^link_(batch|genlink|custom_batch|flink|close)$"))
async def link_callback_handler(client: Client, query: CallbackQuery):
    """Handle callback queries for /link command buttons."""
    logger.info(f"Link callback triggered by user {query.from_user.id} with action {query.data}, is_bot: {query.from_user.is_bot}")
    action = query.data.split("_")[-1]
    user_id = query.from_user.id

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    # Check if user is admin or owner
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if action == "batch":
        await batch(client, query.message)
        await query.answer(to_small_caps_with_html("Batch process started"))
    elif action == "genlink":
        await link_generator(client, query.message)
        await query.answer(to_small_caps_with_html("Genlink process started"))
    elif action == "custom_batch":
        await custom_batch(client, query.message)
        await query.answer(to_small_caps_with_html("Custom batch process started"))
    elif action == "flink":
        await flink_command(client, query.message)
        await query.answer(to_small_caps_with_html("Flink process started"))
    elif action == "close":
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    chat_id = message.from_user.id
    logger.info(f"Batch command triggered by user {chat_id}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    # Initialize batch user data
    batch_user_data[chat_id] = {
        'state': 'initial',
        'first_message_id': None,
        'menu_message': None
    }

    # Show the batch menu with Start Process button
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Batch Link Generator</b></blockquote>\n\n"
        "<blockquote><b>Click 'Start Process' to begin generating a batch link.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Forward the first message from db channel (with quotes).</b></blockquote>\n"
            "<blockquote><b>Or send the db channel post link</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
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
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            batch_user_data[chat_id]['first_message_id'] = f_msg_id
            batch_user_data[chat_id]['state'] = 'awaiting_second_message'
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_second_message':
            s_msg_id = await get_message_id(client, message)
            if not s_msg_id:
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            f_msg_id = batch_user_data[chat_id]['first_message_id']
            string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

            await message.reply_text(
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                quote=True,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

            # Clean up user data
            if chat_id in batch_user_data:
                del batch_user_data[chat_id]

    except TimeoutError:
        logger.error(to_small_caps_with_html(f"Timeout error waiting for batch input in state {state} for user {chat_id}"))
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in handle_batch_input for user {chat_id}: {e}"))
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    logger.info(f"Genlink command triggered by user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    while True:
        try:
            channel_message = await client.ask(
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward message from the db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except UserIsBot:
            logger.error(to_small_caps_with_html(f"UserIsBot error in link_generator for user {message.from_user.id}"))
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
        except TimeoutError:
            logger.error(to_small_caps_with_html(f"Timeout error waiting for message in genlink command for user {message.from_user.id}"))
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                quote=True,
                parse_mode=ParseMode.HTML
            )

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
        quote=True,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    """Handle /custom_batch command to collect and generate a batch link."""
    logger.info(f"Custom batch command triggered by user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["stop"]], resize_keyboard=True)

    await message.reply(
        to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send all messages you want to include in batch.</b></blockquote>\n\n<blockquote><b>Press Stop when you're done.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
        reply_markup=STOP_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for files/messages...</b></blockquote>\n<blockquote><b>Press Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except UserIsBot:
            logger.error(to_small_caps_with_html(f"UserIsBot error in custom_batch for user {message.from_user.id}"))
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            break
        except TimeoutError:
            logger.error(to_small_caps_with_html(f"Timeout error waiting for message in custom_batch command for user {message.from_user.id}"))
            break

        if user_msg.text and user_msg.text.strip().lower() == "stop":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            logger.error(to_small_caps_with_html(f"Error storing message in custom_batch for user {message.from_user.id}: {e}"))
            continue

    await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)

    if not collected:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No messages were added to batch.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://t.me/share/url?url={link}')]])
    await message.reply(
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & admin & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    logger.info(f"Flink command triggered by user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    user_id = message.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    # Initialize flink user data
    flink_user_data[user_id] = {
        'format': None,
        'links': {},
        'edit_data': {},
        'menu_message': None,
        'output_message': None,
        'caption_prompt': None,
        'awaiting_format': False,
        'awaiting_caption': False,
        'awaiting_db_post': False
    }

    try:
        await show_flink(client, message)
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Flink command error: {str(e)}"))
        await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def show_flink(client: Client, message: Message, edit: bool = True):
    """Show the main menu for the flink command."""
    try:
        user_id = message.from_user.id
        current_format = flink_user_data.get(user_id, {}).get('format', 'Not set')
        text = to_small_caps_with_html(
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>Formatted Link Generator</b>\n\n"
            "<blockquote><b>Current format:</b></blockquote>\n"
            f"<blockquote><code>{current_format}</code></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
        )

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
            await message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            msg = await message.reply(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            flink_user_data[user_id]['menu_message'] = msg
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in show_flink: {str(e)}"))
        await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle callback for setting format in flink command."""
    logger.info(f"Flink set format callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    flink_user_data[user_id]['awaiting_format'] = True
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Please enter your format in this pattern:</b></blockquote>\n\n"
        "<blockquote><b>Example format (do not copy, please type):</b></blockquote>\n"
        "<blockquote><code>360p = 2, 720p = 2, 1080p = 2, 4k = 2</code></blockquote>\n\n"
        "<blockquote><b>Explanation:</b></blockquote>\n"
        "<b>- 360p = 2 → 2 video files for 360p quality</b>\n"
        "<blockquote><b>- If stickers/gifs are included, they will be added to the link\n"
        "- Only these specified qualities will be created</b></blockquote>\n\n"
        "<b>Please send the format in the next message.</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="flink_back_to_menu")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Enter your format"))

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink command."""
    logger.info(f"Flink format input received from user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    user_id = message.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_format'):
        format_text = message.text.strip()
        flink_user_data[user_id]['format'] = format_text
        flink_user_data[user_id]['awaiting_format'] = False
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Format successfully saved:</b></blockquote>\n<code>{format_text}</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await show_flink(client, message)
    else:
        await message.reply(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<blockquote><b>❌ Please use the 'Set Format' option first and provide a valid format!</b></blockquote>\n\n"
                "<blockquote><b>Example format:</b>\n<code>360p = 2, 720p = 1</code></blockquote>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_start_process$"))
async def flink_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback query for starting the flink process."""
    logger.info(f"Flink start process callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if not flink_user_data.get(user_id, {}).get('format'):
        await query.answer(to_small_caps_with_html("❌ Please set format first!"), show_alert=True)
        return

    flink_user_data[user_id]['awaiting_db_post'] = True
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Please send the first post link from the db channel:</b></blockquote>\n\n"
        "<blockquote><b>Forward a message from the db channel or paste its direct link (e.g., <code>t.me/channel/123</code>).</b></blockquote>\n\n"
        "<blockquote><b>Ensure files are in sequence without gaps.</b></blockquote>\n\n"
        "<b>Please send the link or forwarded message in the next message.</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✖️ Cancel", callback_data="flink_cancel_process")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Please send db channel post"))

@Bot.on_message(filters.private & (filters.forwarded | filters.regex(r"^https?://t\.me/.*$")))
async def handle_db_post(client: Client, message: Message):
    """Handle database channel post input for flink command."""
    logger.info(f"Flink db post input received from user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    user_id = message.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_db_post'):
        await message.reply(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<blockquote><b>❌ Please start the process first and provide a valid forwarded message or link from the db channel!</b></blockquote>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )
        return

    msg_id = await get_message_id(client, message)
    if not msg_id:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Invalid db channel post!</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    format_str = flink_user_data[user_id]['format']
    format_parts = [part.strip() for part in format_str.split(',')]
    links = {}
    current_id = msg_id

    for part in format_parts:
        match = re.match(r"([a-zA-Z0-9]+)\s*=\s*(\d+)", part)
        if not match:
            await message.reply(
                to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>Invalid format part:</b>\n<code>{part}</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return
        quality, count = match.groups()
        quality = quality.strip().upper()
        count = int(count)

        valid_ids = []
        temp_id = current_id
        missing_files = 0
        while len(valid_ids) < count and temp_id < current_id + 100:  # Limit search to avoid infinite loops
            try:
                msg = await client.get_messages(client.db_channel.id, temp_id)
                if msg.video or msg.document:
                    valid_ids.append(temp_id)
                else:
                    missing_files += 1
                temp_id += 1
            except Exception:
                missing_files += 1
                temp_id += 1

        if len(valid_ids) < count:
            await message.reply(
                to_small_caps_with_html(
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    f"<blockquote><b>❌ Not enough valid media files for {quality}. Found {len(valid_ids)} files, but {count} required.</b></blockquote>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            return

        start_id = valid_ids[0]
        end_id = valid_ids[-1]
        additional_count = 0
        next_id = end_id + 1
        try:
            next_msg = await client.get_messages(client.db_channel.id, next_id)
            if next_msg.sticker or next_msg.animation:
                additional_count = 1
                end_id = next_id
        except Exception:
            pass

        links[quality] = {
            'start': start_id,
            'end': end_id,
            'count': count + additional_count
        }
        current_id = end_id + 1

    flink_user_data[user_id]['links'] = links
    flink_user_data[user_id]['awaiting_db_post'] = False
    await flink_generate_final_output(client, message)

async def flink_generate_final_output(client: Client, message: Message):
    """Generate the final output for flink command with download buttons."""
    logger.info(f"Generating final output for user {message.from_user.id}")

    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No links generated.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        buttons = []
        quality_list = list(links.keys())
        for i in range(0, len(quality_list), 2):
            row = []
            for quality in quality_list[i:i+2]:
                link = await create_link(client, links[quality])
                row.append(InlineKeyboardButton(f"🦋 {quality} 🦋", url=link))
            buttons.append(row)

        buttons.append([
            InlineKeyboardButton("◈ Edit ◈", callback_data="flink_edit_output"),
            InlineKeyboardButton("Done ◈", callback_data="flink_done_output")
        ])

        edit_data = flink_user_data[user_id].get('edit_data', {})
        caption = edit_data.get('caption', to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here are your generated download buttons:</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"))

        if edit_data.get('image'):
            output_msg = await message.reply_photo(
                photo=edit_data['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            output_msg = await message.reply(
                text=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )

        flink_user_data[user_id]['output_message'] = output_msg

    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_generate_final_output: {e}"))
        await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def create_link(client: Client, link_data: Dict) -> str:
    """Create a Telegram link for a range of message IDs."""
    start_id = link_data['start'] * abs(client.db_channel.id)
    end_id = link_data['end']
 * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    return f"https://t.me/{client.username}?start={base64_string}"

@Bot.on_callback_query(filters.regex(r"^flink_edit_output$"))
async def flink_edit_output_callback(client: Client, query: CallbackQuery):
    """Handle callback query for editing flink output."""
    logger.info(f"Flink edit output callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Add optional elements to the output:</b></blockquote>\n\n"
        "<blockquote><b>You can send an image or type a caption separately.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("◈ Image ◈", callback_data="flink_add_image"),
                InlineKeyboardButton("◈ Text ◈", callback_data="flink_add_caption")
            ],
            [
                InlineKeyboardButton("◄ Back", callback_data="flink_back_to_output"),
                InlineKeyboardButton("Done", callback_data="flink_done_output")
            ]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Edit your output"))

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding an image to flink output."""
    logger.info(f"Flink add image callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Please send the image for the output message.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="flink_edit_output")]
        ]),
        parse_mode=ParseMode.HTML
    )
    await query.answer(to_small_caps_with_html("Send the image"))

@Bot.on_message(filters.private & filters.photo)
async def handle_image_input(client: Client, message: Message):
    """Handle image input for flink command."""
    logger.info(f"Handle image input for user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    user_id = message.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        return

    if user_id in flink_user_data:
        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Image successfully saved.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    else:
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please start the 'Add Image' action first.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding a caption to flink output."""
    logger.info(f"Flink add caption callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    flink_user_data[user_id]['awaiting_caption'] = True
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Type your caption:</b></blockquote>\n\n"
        "<blockquote><b>Here’s an example:</b></blockquote>\n"
        "<blockquote><code>ᴛɪᴛʟᴇ- BLACK SCREEN\n\n"
        "Aᴜᴅɪ ᴛʀᴀᴄᴋ - Hɪɴᴅɪ Dᴜʙ\n\n"
        "Q - 360p, 720p, 1080p\n"
        "Eᴘɪsᴏᴅᴇ - 01 & S2\n\n"
        "ALL Q - QUALITY - ( HINDI DUBBED )\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        "CLICK HERE TO DOWNLOAD | EP - 01 & S2\n\n</code></blockquote>\n\n"
        "<b>Please reply to this message with your caption.</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
    )

    caption_prompt = await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="flink_edit_output")]
        ]),
        parse_mode=ParseMode.HTML
    )
    flink_user_data[user_id]['caption_prompt'] = caption_prompt
    await query.answer(to_small_caps_with_html("Type your caption"))

@Bot.on_message(filters.private & filters.text & filters.reply)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for flink command."""
    logger.info(f"Flink handle caption input for user {message.from_user.id}, is_bot: {message.from_user.is_bot}")

    # Check if user is a bot
    if message.from_user.is_bot:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ This command cannot be used by bots.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    user_id = message.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        return

    if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_caption'):
        caption_prompt = flink_user_data[user_id].get('caption_prompt')
        if message.reply_to_message and message.reply_to_message.id == caption_prompt.id:
            flink_user_data[user_id]['edit_data']['caption'] = message.text
            flink_user_data[user_id]['awaiting_caption'] = False
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Caption added successfully.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            await flink_generate_final_output(client, message)
        else:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the caption prompt message.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
    else:
        await message.reply(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                "<b>❌ Please use the 'Add Caption' option first.</b>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output_callback(client: Client, query: CallbackQuery):
    """Handle callback query for finalizing flink output."""
    logger.info(f"Flink done callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if user_id not in flink_user_data or not flink_user_data[user_id]['links']:
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ links found.</b>\n</b>Please start the process again.\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    links = flink_user_data[user_id]['links']
    edit_data = flink_user_data[user_id].get('edit_data', {})
    caption = edit_data.get('caption', to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here are your generated download buttons:</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"))

    buttons = []
    for i in range(0, len(quality_list), 2):
        row = []
        for quality in quality_list[i:i+2]:
            link = await create_link(client, links[quality])
            row.append(InlineKeyboardButton(f"🦋 {quality} �", url=link))
        buttons.append(row)

    if edit_data.get('image'):
        await query.message.delete()
        await query.message.reply_photo(
            photo=edit_data['image'],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    else:
        await query.message.delete()
        await query.message.reply(
            text=caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    if user_id in flink_user_data:
        del flink_user_data[user_id]

    await query.answer(to_small_caps_with_html("Process completed"))

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Handle callback query for refreshing flink menu."""
    logger.info(f"Flink refresh callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    await show_flink(client, query.message, edit=True)
    await query.answer(to_small_caps_with_html("Format status refreshed"))

@Bot.on_callback_query(filters.regex(r"^flink_(back_to_menu|cancel_process|close)$"))
async def flink_handle_back_buttons(client: Client, query: CallbackQuery):
    """Handle back, cancel, and close callbacks for flink command."""
    logger.info(f"Flink {query.data} callback triggered by user {query.from_user.id}, is_bot: {query.from_user.is_bot}")

    # Check if user is a bot
    if query.from_user.is_bot:
        await query.answer(to_small_caps_with_html("Bots cannot use this command!"), show_alert=True)
        return

    user_id = query.from_user.id
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    action = query.data.split('_')[1]
    if action == "back_to_menu":
        await show_flink(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Back to menu"))
    elif action == "cancel_process":
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in flink_user_data:
            del flink_user_data[user_id]
        await query.answer(to_small_caps_with_html("Process cancelled"))
    elif action == "close":
        await query.message.delete()
        if user_id in flink_user_data:
            del flink_user_data[user_id]
        await query.answer(to_small_caps_with_html("Closed"))

#
# Copyright © 2023 by AnimeLord-Bots@GitHub, <https://github.com/AnimeLord-Bots>.
#
# This file is part of <https://github.com/AnimeLord-Bots/FileStore> project,
# and is licensed under the MIT License.
#
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE>
#
# All rights reserved.
#
