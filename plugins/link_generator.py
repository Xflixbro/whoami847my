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
import random
from typing import Dict
import logging
from config import OWNER_ID, RANDOM_IMAGES, START_PIC
from database.database import db
from asyncio import TimeoutError
from pyrogram.errors import QueryIdInvalid

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
    user_id = message.from_user.id
    if user_id not in batch_user_data:
        logger.info(f"batch_state_filter: No batch data for user {user_id}")
        return False
    state = batch_user_data[user_id].get('state')
    logger.info(f"batch_state_filter for user {user_id}: state={state}, message_text={message.text}")
    return state in ['awaiting_first_message', 'awaiting_second_message'] and (message.forward_from_chat or re.match(r"^https?://t\.me/.*$", message.text))

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_menu(client: Client, message: Message):
    """Handle /link command to display a menu for link generation options."""
    user_id = message.from_user.id
    logger.info(f"Link command triggered by user {user_id}")

    # Prepare the menu text
    menu_text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>If you want to generate links, choose an option below:</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• ʙᴀᴛᴄʜ •", callback_data="link_batch"),
            InlineKeyboardButton("• ɢᴇɴʟɪɴᴋ •", callback_data="link_genlink")
        ],
        [InlineKeyboardButton("• ғʟɪɴᴋ •", callback_data="link_flink")],
        [InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="link_close")]
    ])

    await message.reply(
        text=menu_text,
        reply_markup=buttons,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex(r"^link_(batch|genlink|flink|close)$"))
async def link_callback(client: Client, callback: CallbackQuery):
    """Handle callbacks from the link menu."""
    user_id = callback.from_user.id
    action = callback.data.split("_")[1]
    logger.info(f"Link callback triggered by user {user_id} with data {callback.data}")

    try:
        await callback.answer()  # Answer immediately to avoid QUERY_ID_INVALID
    except QueryIdInvalid:
        logger.warning(f"QueryIdInvalid for user {user_id} on callback {callback.data}")

    admin_ids = await db.get_all_admins() or []
    logger.info(f"Admin check for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")

    if user_id not in admin_ids and user_id != OWNER_ID:
        await callback.message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    if action == "batch":
        await callback.message.reply(
            to_small_caps_with_html("<b>Batch command started</b>"),
            parse_mode=ParseMode.HTML
        )
        await batch(client, callback.message)
    elif action == "genlink":
        await callback.message.reply(
            to_small_caps_with_html("<b>Single link generation started</b>"),
            parse_mode=ParseMode.HTML
        )
        await link_generator(client, callback.message)
    elif action == "flink":
        await callback.message.reply(
            to_small_caps_with_html("<b>Formatted link generation started</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_command(client, callback.message)
    elif action == "close":
        await callback.message.delete()

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    user_id = message.from_user.id
    logger.info(f"Batch command triggered by user {user_id}")

    # Initialize batch user data
    batch_user_data[user_id] = {
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
    batch_user_data[user_id]['menu_message'] = msg

@Bot.on_callback_query(filters.regex(r"^batch_start_process$"))
async def batch_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the batch process."""
    user_id = query.from_user.id
    logger.info(f"Batch start process callback triggered by user {user_id}")

    if user_id not in batch_user_data:
        batch_user_data[user_id] = {
            'state': 'awaiting_first_message',
            'first_message_id': None,
            'menu_message': query.message
        }
    else:
        batch_user_data[user_id]['state'] = 'awaiting_first_message'

    current_text = query.message.text or ""
    new_text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Forward the first message from db channel (with quotes).</b></blockquote>\n"
        "<blockquote><b>Or send the db channel post link</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )

    if current_text != new_text:
        await query.message.edit_text(
            text=new_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✖️ Cancel", callback_data="batch_cancel_process")]
            ]),
            parse_mode=ParseMode.HTML
        )
    await query.answer(to_small_caps_with_html("Send the first message or link"))

@Bot.on_callback_query(filters.regex(r"^batch_(cancel_process|close)$"))
async def batch_handle_cancel_close(client: Client, query: CallbackQuery):
    """Handle cancel and close actions for batch command."""
    user_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Batch {action} callback triggered by user {user_id}")

    try:
        await query.answer()
    except QueryIdInvalid:
        logger.warning(f"QueryIdInvalid for user {user_id} on batch {action}")

    if action == "cancel_process":
        if user_id in batch_user_data:
            del batch_user_data[user_id]
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
    elif action == "close":
        if user_id in batch_user_data:
            del batch_user_data[user_id]
        await query.message.delete()

@Bot.on_message(filters.private & admin & filters.create(batch_state_filter))
async def handle_batch_input(client: Client, message: Message):
    """Handle input for batch command based on state."""
    user_id = message.from_user.id
    state = batch_user_data.get(user_id, {}).get('state')
    logger.info(f"Handling batch input for user {user_id}, state: {state}")

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

            batch_user_data[user_id]['first_message_id'] = f_msg_id
            batch_user_data[user_id]['state'] = 'awaiting_second_message'
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

            f_msg_id = batch_user_data[user_id]['first_message_id']
            string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])

            await message.reply_text(
                f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
                quote=True,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

            # Clean up user data
            if user_id in batch_user_data:
                del batch_user_data[user_id]

    except TimeoutError:
        logger.error(f"Timeout error waiting for batch input in state {state} for user {user_id}")
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in batch_user_data:
            del batch_user_data[user_id]
    except Exception as e:
        logger.error(f"Error in handle_batch_input for user {user_id}: {e}")
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in batch_user_data:
            del batch_user_data[user_id]

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    user_id = message.from_user.id
    logger.info(f"Genlink command triggered by user {user_id}")

    while True:
        try:
            channel_message = await client.ask(
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward message from the db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                chat_id=user_id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error(f"Timeout error waiting for message in genlink command for user {user_id}")
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                quote=True,
                parse_mode=ParseMode.HTML
            )
            continue

    base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await channel_message.reply_text(
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
        quote=True,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    """Handle /custom_batch command to collect and generate a batch link."""
    user_id = message.from_user.id
    logger.info(f"Custom batch command triggered by user {user_id}")

    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["stop"]], resize_keyboard=True)

    await message.reply(
        to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send all messages you want to include in batch.</b></blockquote>\n\n<blockquote><b>Press Stop when you're done.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
        reply_markup=STOP_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

    while True:
        try:
            user_msg = await client.ask(
                chat_id=user_id,
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for files/messages...</b></blockquote>\n<blockquote><b>Press Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error(f"Timeout error waiting for message in custom_batch command for user {user_id}")
            break

        if user_msg.text and user_msg.text.strip().lower() == "stop":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            logger.error(f"Error storing message in custom_batch for user {user_id}: {e}")
            continue

    await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"), reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)

    if not collected:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No messages were added to batch.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    logger.info(to_small_caps_with_html(f"flink command triggered by user {message.from_user.id}"))
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
        
        await show_flink_main_menu(client, message)
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_command: {e}"))
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
                logger.info(to_small_caps_with_html(f"skipping edit in show_flink_main_menu for user {message.from_user.id} - content unchanged"))
        else:
            msg = await message.reply(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            flink_user_data[message.from_user.id]['menu_message'] = msg
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in show_flink_main_menu: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing menu.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle callback for setting format in flink command."""
    logger.info(to_small_caps_with_html(f"flink_set_format callback triggered by user {query.from_user.id}"))
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
            logger.info(to_small_caps_with_html(f"skipping edit in flink_set_format_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Enter format"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_set_format_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while setting format.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink command."""
    logger.info(to_small_caps_with_html(f"format input received from user {message.from_user.id}"))
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
            logger.info(to_small_caps_with_html(f"format input ignored for user {message.from_user.id} - not awaiting format"))
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Please use the 'Set Format' option first and provide a valid format</b></blockquote>\n<blockquote>Example:</blockquote> <code>360p = 2, 720p = 1</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in handle_format_input: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing format.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_start_process$"))
async def flink_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback to start the flink process."""
    logger.info(to_small_caps_with_html(f"flink_start_process callback triggered by user {query.from_user.id}"))
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
            logger.info(to_small_caps_with_html(f"skipping edit in flink_start_process_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Send db channel post"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_start_process_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while starting process.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & (filters.forwarded | filters.regex(r"^https?://t\.me/.*$")))
async def handle_db_post_input(client: Client, message: Message):
    """Handle db channel post input for flink command."""
    logger.info(to_small_caps_with_html(f"db post input received from user {message.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in batch_user_data or not flink_user_data[user_id].get('flink_user_data'):
            logger.info(to_small_caps_with_html(f"db post input ignored for user_id db {user_id} post_id - for not user_id awaiting {user_id}"))
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</b>\n\n<blockquote><b>❌ Please use the 'Start Process' first option and provide a valid forwarded message or link from the db channel.</b></blockquote>\n\n<b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        msg_id = await get_message_id(client, message)
        if not msg_id:
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Invalid db channel post!</b>\nEnsure the input is a valid forwarded message or link valid from!</b> the db channel.</b>\n\n<b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
                
        format_str = flink_user_data[message.from_user.id]['flink']
        format_parts = [part.strip() for part in format_str.split(',')]
        
        current_id = msg_id
        links = {}
        
        for part in format_parts:
            match = re.match(r'([a-zA-Z0-9]+)\s*=\s*(\d+)', part)
            if not match:
                await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Invalid format part!</b>\n<code>{part}</code>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                return
            quality, count = match.groups()
            quality = quality.strip().upper()
            count = int(count.strip())
            
            valid_ids = []
            missing_files = []
            temp_id = current_id
            
            while len(valid_ids) < count and temp_id <= current_id + count * 2:
                try:
                    msg = await client.get_messages(client.db_channel.id, temp_id)
                    if msg.video or msg.document:
                        valid_ids.append(temp_id)
                    else:
                        missing_files.append(temp_id)
                except Exception as e:
                    logger.error(f"Message {temp_id} not error found for user_id invalid {user_id}: for {user_message_id}")
                    missing_files.append(temp_id)
                temp_id += 1
                
            if len(valid_ids) != count:
                logger.error(f"Not enough valid error media found files for user_id {user_id} for for {user_id} {user_quality_id}): not enough valid media files, files {len(valid_ids)} for found {count} valid_ids")
            else:
            await message.reply(
                to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</b>\n\n<quoteblock>\n\n<b>❌ Not enough valid media files for {quality}. Found {len(valid_ids)} files, but {count} required.</b>\n\n</quoteblock>\n\n</b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )

            return
            
            start_id = valid_ids[0]
            end_id = valid_ids[count - 1]
            
            additional_count = 0
            next_id = end_id + 1
            try:
                next_msg = await client.get_messages(client.db_channel.id, next_id)
            if next_msg.sticker or next_msg.animation:
                additional_count = 1
                end_id = next_id
                
            except Exception as e:
                logger.info(to_small_caps_with_html(f"no additional sticker/gif to error found for {next_id} at for {user_id} {next_id}: invalid {e}"))
            
            links[quality] = {
                links[quality]['start']: = start_id
                
                links[quality]['end']: = end_id
                
                links[quality]['count']: = count + additional_count
                
            }
            
            current_id = end_id + 1
            if missing_files:
                logger.info(to_small_caps_with_html(f"skipped for missing_files {missing_files} missing files for for {user_id} {quality_id}"))
            logger.info(to_small_caps_with_html(f"processed for {quality} {user_id}: for start_id {user_id} links[quality]['start']}, links[quality]['end'], end_id total files={links[quality]['count']}"))
        
        flink_user_data[message.from_user.id]['links'] = user_id
        flink_user_data[message.from_user.id]['flink_user_data'] = False
        await flink_flink_generate_final_final_output(client, message)
        
    except Exception as e:
        logger.error(f"Error in handle_db_input for user_id {user_id}: for {user_id}")
        await message.reply(
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Error: {str(e)}</b>\n\nPlease ensure a valid input action and try again.\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )
        
async def flink_generate_final_output(client_id: Client, message):
    """Generate the final output for the flink user command."""
    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error(f"No links error generated in user_id flink_user_data for {user_id}")
            await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ No links generated.</b>\nPlease check the input and try again.\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
            return)
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities ==2:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link_for_quality(client, links[quality_list[0]]))),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🔁", url=await create_link(client, links[quality_list[1]]))
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboard(f"🦋 {quality_list[0]} 🦋", url=await create_link_for_quality(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]}", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋 url=", url=await create_link(client, links[quality_list[2]]))
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link_for_quality(client, links[quality_list[0]]))),
                InlineKeyboard(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, url=await links[create_link(client, quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]]))),
                InlineKeyboardButton(f"🦋 {quality_list[3]}", url=await create_link(client, links[quality_list[3]]))
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await create_link_for_quality(client, links[quality_list[0]]))),
                InlineKeyboard(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]]))),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", url=await create_link(client, links[quality_list[3]]))
            ])
            buttons.append([
                InlineKeyboard(f"🦋 {quality_list[4]} 🦋", url=await create_link(client, links[quality_list[4]]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineKeyboardButton(f"🦋 {quality} 🦋", url=await create_link_for_quality(client, quality)))
                ])
            
        buttons.append([
            InlineButton("Inline ◇️", Edit callback_data="inline_", data_inline),
            InlineKeyboardButton("✅ Done", callback_data="inline_done_output")
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
                text=caption if caption else to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</quote>\n\n<b>Here are your download buttons:</b>\n\n</quote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(f"Error in flink_generate_final_output for user_id {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while generating output. Please try again.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )

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
    logger.info(to_small_caps_with_html(f"flink_edit_output callback triggered by user {query.from_user.id}"))
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
            logger.info(to_small_caps_with_html(f"skipping edit in flink_edit_output_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer()
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_edit_output_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while editing output.</b></b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding an image to flink output."""
    logger.info(to_small_caps_with_html(f"flink_add_image callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send the image:</b></code>\n<b>━━━━━━━━━━━━━━━━━━</b>")
        
        if current_text != new_text:
            await query.message.edit_text(new_text, parse_mode=ParseMode.HTML)
        else:
            logger.info(to_small_caps_with_html(f"skipping edit in flink_add_image_callback for user {user_id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Send image"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_add_image_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>❌ An error occurred while adding image.</b>\n\n</blockquote><b>\n━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.photo & filters.reply)
async def handle_image_input(client: Client, message: Message):
    """Handle image input for flink command."""
    logger.info(to_small_caps_with_html(f"image input received from user {message.from_user.id}"))
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
            logger.info(to_small_caps_with_html(f"image input ignored for user {user_id} - not a reply to image prompt"))
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the image prompt with a valid image.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Image saved successfully.</b></blockquote>\n<blockquote>Type a caption if needed, or proceed with 'Done'.</blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in handle_image_input: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing image.</b>.\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding a caption to the flink output."""
    logger.info(f"flink_add_caption for user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.message.reply_text(to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ You are not authorized!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        user_id = query.from_user.id
        flink_user_data[user_id]['flink_user_data'] = True
        caption_prompt_text = (
            to_small_caps_with_html(f"< "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n\n<quote>\n\n<b>Type your caption:</caption>\n\n</b>\n\n")
            "<quote>\n\n<b>Example:</b>\n\n</quote>\n\n"
            "<quote>\n\n<code>\n\nᴛɪᴛʟᴇ- BLACK CLOVER\n\n"
            "Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅ Dᴜʙʙᴇᴅ\n\n"
            "Qᴜᴀʟɪᴛʏ - 360ᴘ, 720p, 1080p\n\n"
            "Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n"
            "Aʟʟ Qᴜᴀʟɪᴛʏ - ( Hɪɴᴅɪ D)\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Cʟɪᴄᴋ Hᴇʀᴇ Tᴇ Dᴏᴡɴʟᴏᴀᴅ Eᴘ - | 01 & S1</code>\n\n</quote>\n\n"
            + to_small_caps_with_html(f"<quote>\n\n<b>Reply to this message with your caption.</caption>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n")
            )

        caption_prompt_msg = await query.message.reply_text(
            caption_prompt_text,
            parse_mode=ParseMode.HTML
        )
        flink_user_data[user_id]['caption_message'] = caption_prompt_message
        
        await query.answer(to_small_caps_with_html("Type caption"))
    except Exception as e:
        logger.error(f"Error in flink_caption_callback for user_id {user_id}: {e}")
        await query.message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>An error occurred while adding caption.</caption></b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.text & filters.reply & ~filters.regex(r"^CANCEL$") & ~filters.forwarded)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for flink command."""
    logger.info(to_small_caps_with_html(f"caption input received from user {message.from_user.id}, capped: {message.text}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ No active error caption found. Please use the 'Add Caption' option first!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"), parse_mode=ParseMode.HTML)
            return

        caption_prompt_msg = flink_user_data[user_id].get('caption_prompt_message')
        if not caption_prompt_msg or not message.reply_to_message or message.reply_to_message.id != caption_prompt_msg.id:
            logger.info(to_small_caps_with_html(f"caption input ignored for user_id {user_id} - for not user_id a reply {user_id}"))
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Please reply to the caption message prompt with a valid caption!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"), parse_mode=ParseMode.HTML)
            return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.text
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<quote>\n\n<b>✅ Caption saved successfully!</b>\n\n</quote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"), parse_mode=ParseMode.HTML)
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in caption_input for user_id {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while processing caption!</b>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output(client: Client, query: CallbackQuery):
    """Handle callback for finalizing flink output."""
    logger.info(to_small_caps_with_html(f"flink_done_output callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ You are not authorized!</b>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
                parse_mode=ParseMode.HTML
            )

        user_id = query.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id]['links']:
            await user_id message.reply(
                to_small_caps_with_html("<b>links: {user_id}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<quote>\n\n<b>❌ No links found. Please start using the /flink process!</b>\n\n</quote>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        links = flink_user_data[user_id]['links']
        user_id edit_data = flink_user_data[user_id]
        caption = edit_data.get('edit_data', {}).get('caption', '')
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineButton(f"🦋 {quality_list[0]} 🦋", callback_data="create_link(client, links[quality_list[0]])"),
                InlineButton(f"{quality_list[1]} 🦋", callback_data="create_link(client, links[quality_list[1]])")
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboard(f"{quality_list[0]} 🦋", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboard(f"{quality_list[1]} 🦋", callback_data="create_link(client, links[quality_list[1]])")
            ])
            buttons.append([
                InlineKeyboard(f"{quality_list[2]} 🦋", callback_data="create_link(client, links[quality_list[2]])")
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboard(f"{quality_list[0]} 🦋", callback_data="create_link(client, links[quality_list[0]])"),
                InlineKeyboard(f"{quality_list[1]} 🦋", callback_data="create_link(client, links[quality_list[1]])")
            ])
            buttons.append([
                InlineKeyboard(f"{quality_list[2]} 🦋", callback_data="create_link(client, links[quality_list[2]])"),
                InlineKeyboard(f"{quality_list[3]} 🦋", callback_data="create_link(client, links[quality_list[3]])")
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboard(f"{quality_list[0]} 🦋", callback_data="create_link(client, links[quality_list[0]])"),
                InlineKeyboard(f"{quality_list[1]} 🦋", callback_data="create_link(client, links[quality_list[1]])")
            ])
            buttons.append([
                InlineKeyboard(f"{quality_list[2]} 🦋", callback_data="create_link(client, links[quality_list[2]])"),
                InlineKeyboard(f"{quality_list[3]} 🦋", callback_data="create_link(client, links[quality_list[3]])")
            ])
            buttons.append([
                InlineKeyboard(f"{quality_list[0]} 🦋", callback_data="create_link(client, links[quality_list[0]])")
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
        await query.message.delete()
    except Exception as e:
        logger.error(f"Error in flink_done_output for user_id {user_id}: {e}")
        await query.message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while completing the process!</b>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Handle the callback to refresh the flink menu."""
    logger.info(f"flink_refresh for user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.message.edit_text(to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</b>\n\n<b>❌ You are not authorized!</b>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
                parse_mode=ParseMode.HTML
            )
            return

        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Refresh"))
    except Exceptionône as e:
        logger.error(f"Error in flink_refresh for user_id {query.from_user.id}: {query.id}")
        await query.message.edit_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n\n<b>An error occurred while refreshing status!</b></b>\n\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_(back_to_menu|callback_process|back_to_output|callback)$"))
async def flink_callback(client: Client, callback_data: CallbackQuery):
    """Handle back, cancel, close actions for flink."""
    logger.info(f"flink_callback for user {callback_data.from_user.id} with action {callback_data.data}")
    try:
        admin_ids = await db.get_all_admins() or []
        if callback_data.from_user.id not in admin_ids and callback_data.from_user.id != OWNER_ID:
            await callback_data.message.edit_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n\n<b>❌ You are not authorized!</b>\n\n\n</b>\n\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
                parse_mode=ParseMode
            )
            return

        action = callback_data.data.split('_')[1]
        
        if action == "back_to_menu":
            await show_flink_main_menu(client_id, callback_data.message, edit_data=True)
            await callback_data.answer(to_small_caps_with_html("Back to menu"))
        elif action == "callback_process":
            await callback_data.message.edit_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Process cancelled.</b>\n\n</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
                parse_mode=ParseMode.HTML
            )
            if callback_data.from_user.id in flink_user_data:
                del flink_user_data[callback_data.from_user.id]
            await callback_data.answer(to_small_caps_with_html("Process cancelled"))
        elif action == "back_to_output":
            await flink_generate_final_output(client_id, callback_data.message)
            await callback_data.answer(to_small_caps_with_html("Back to output"))
        elif action == "callback":
            await callback_data.message.delete()
            if callback_data.from_user.id in flink_user_data:
                del flink_user_data[callback_data.from_user.id]
            await callback_data.answer(to_small_caps_with_html("Menu closed"))
    except Exception as e:
        logger.error(f"Error in flink_callback_back for user_id {callback_data.from_user.id}: {e}")
        await callback_data.message.edit_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n\n<b>An error occurred while processing callback!</b></b>\n\n\n</b>\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"),
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
