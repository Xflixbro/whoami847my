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
    return state in ['awaiting_first_message', 'awaiting_second_message'] and (message.forward_from_chat or re.match(r"^https?://t\.me/.*$", message.text))

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_menu(client: Client, message: Message):
    """Handle /link command to display a menu for link generation options."""
    chat_id = message.from_user.id
    logger.info(f"Link command triggered by user {chat_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if chat_id not in admin_ids and chat_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    # Prepare the menu text
    menu_text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>If you want to generate link for files then use those buttons according to your need.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )

    # Define buttons for the menu
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• ʙᴀᴛᴄʜ •", callback_data="link_batch"),
            InlineKeyboardButton("• ɢᴇɴʟɪɴᴋ •", callback_data="link_genlink")
        ],
        [
            InlineKeyboardButton("• ᴄᴜsᴛᴏᴍ •", callback_data="link_custom"),
            InlineKeyboardButton("• ꜰʟɪɴᴋ •", callback_data="link_flink")
        ],
        [
            InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="link_close")
        ]
    ])

    # Select random image
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        # Send the menu with a random image
        await client.send_photo(
            chat_id=chat_id,
            photo=selected_image,
            caption=menu_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send link menu with photo for user {chat_id}: {e}")
        # Fallback to text-only message
        await client.send_message(
            chat_id=chat_id,
            text=menu_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

@Bot.on_callback_query(filters.regex(r"^link_"))
async def link_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for the /link command menu."""
    data = callback.data
    user_id = callback.from_user.id
    logger.info(f"Link callback triggered by user {user_id} with data {data}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await callback.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if data == "link_batch":
        await batch(client, callback.message)
        await callback.answer(to_small_caps_with_html("Batch link generation started"))
    elif data == "link_genlink":
        await link_generator(client, callback.message)
        await callback.answer(to_small_caps_with_html("Single link generation started"))
    elif data == "link_custom":
        await custom_batch(client, callback.message)
        await callback.answer(to_small_caps_with_html("Custom batch link generation started"))
    elif data == "link_flink":
        await flink_command(client, callback.message)
        await callback.answer(to_small_caps_with_html("Formatted link generation started"))
    elif data == "link_close":
        await callback.message.delete()
        await callback.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    chat_id = message.from_user.id
    logger.info(f"Batch command triggered by user {chat_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if chat_id not in admin_ids and chat_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

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
    user_id = query.from_user.id
    logger.info(f"Batch start process callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if user_id not in batch_user_data:
        batch_user_data[user_id] = {
            'state': 'awaiting_first_message',
            'first_message_id': None,
            'menu_message': query.message
        }
    else:
        batch_user_data[user_id]['state'] = 'awaiting_first_message'

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
    user_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.info(f"Batch {action} callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    if action == "cancel_process":
        if user_id in batch_user_data:
            del batch_user_data[user_id]
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await query.answer(to_small_caps_with_html("Process cancelled"))
    elif action == "close":
        if user_id in batch_user_data:
            del batch_user_data[user_id]
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.create(batch_state_filter))
async def handle_batch_input(client: Client, message: Message):
    """Handle input for batch command based on state."""
    user_id = message.from_user.id
    state = batch_user_data.get(user_id, {}).get('state')
    logger.info(f"Handling batch input for user {user_id}, state: {state}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
        if state == 'awaiting_first_message':
            f_msg_id = await get_message_id(client, message)
            if not f_msg_id:
                await message.reply_text(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            batch_user_data[user_id]['first_message_id'] = f_msg_id
            batch_user_data[user_id]['state'] = 'awaiting_second_message'
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_second_message':
            s_msg_id = await get_message_id(client, message)
            if not s_msg_id:
                await message.reply_text(
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
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if user_id in batch_user_data:
            del batch_user_data[user_id]
    except Exception as e:
        logger.error(f"Error in handle_batch_input for user {user_id}: {e}")
        await message.reply_text(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        if user_id in batch_user_data:
            del batch_user_data[user_id]

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    user_id = message.from_user.id
    logger.info(f"Genlink command triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

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
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply_text(
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

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["stop"]], resize_keyboard=True)

    await message.reply_text(
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
            await message.reply_text(
                to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            logger.error(f"Error storing message in custom_batch for user {user_id}: {e}")
            continue

    await message.reply_text(
        to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )

    if not collected:
        await message.reply_text(
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
    await message.reply_text(
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & admin & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    user_id = message.from_user.id
    logger.info(f"Flink command triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
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
        
        await show_flink_main_menu(client, message)
    except Exception as e:
        logger.error(f"Error in flink_command for user {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    """Show the main menu for the flink command."""
    user_id = message.from_user.id
    logger.info(f"Showing flink main menu for user {user_id}, edit={edit}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
        current_format = flink_user_data[user_id]['format'] or "Not set"
        text = to_small_caps_with_html(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Formatted Link Generator</b>\n\n<blockquote><b>Current format:</b></blockquote>\n<blockquote><code>{current_format}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"
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
            if message.text != text or message.reply_markup != InlineKeyboardMarkup(buttons):
                msg = await message.edit_text(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML
                )
                flink_user_data[user_id]['menu_message'] = msg
            else:
                logger.info(f"Skipping edit in show_flink_main_menu for user {user_id} - content unchanged")
        else:
            msg = await message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            flink_user_data[user_id]['menu_message'] = msg
    except Exception as e:
        logger.error(f"Error in show_flink_main_menu for user {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing menu.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle callback for setting format in flink command."""
    user_id = query.from_user.id
    logger.info(f"Flink set format callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        flink_user_data[user_id]['awaiting_format'] = True
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
            logger.info(f"Skipping edit in flink_set_format_callback for user {user_id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Enter format"))
    except Exception as e:
        logger.error(f"Error in flink_set_format_callback for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>ERROR error occurred while setting format.</b>"),
            parse_mode=ParseMode.HTML
        )

async def flink_generate_final_output(client: Client, message: Message) -> None:
    """Generate the final output for flink command with download buttons."""
    user_id = message.from_user.id
    logger.debug(f"Generating final output for user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error(f"No links generated for user {user_id}")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No links generated. Please try again</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineKeyboardButton(f"{quality_list[0]}", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"{quality_list[1]}", url=await create_link(client, links[quality_list[1]]))
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboardButton(f"{quality_list[0]}", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"{quality_list[1]}", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"{quality_list[2]}", url=await create_link(client, links[quality_list[2]]))
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboardButton(f"{quality_list[0]}", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"{quality_list[1]}", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"{quality_list[2]}", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"{quality_list[3]}", url=await create_link(client, links[quality_list[3]]))
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboardButton(f"{quality_list[0]}", url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"{quality_list[1]}", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"{quality_list[2]}", url=await create_link(client, links[quality_list[2]])),
                InlineKeyboardButton(f"{quality_list[3]}", url=await create_link(client, links[quality_list[3]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"{quality_list[4]}", url=await create_link(client, links[quality_list[4]]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineKeyboardButton(f"{quality}", url=await create_link(client, links[quality]))
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
                text=caption if caption else to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here are your download buttons:</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(f"Error in generating final output for user {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while generating output.</b>\n<b>Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━</b>"),
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
    user_id = query.from_user.id
    logger.debug(f"Flink edit output callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>Add optional elements to the output:</b>\n\n"
            "<b>Send an image or type a caption separately.</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━</b>"
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
                        InlineKeyboardButton("✔️ Finish setup", callback_data="flink_done_output")
                    ]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.debug(f"Skipping edit in flink_edit_output_callback for user {user_id} - content unchanged")
        
        await query.answer()
    except Exception as e:
        logger.error(f"Error in flink_edit_output_callback for user {user_id}: {str(e)}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while editing output.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding an image to the flink output."""
    user_id = query.from_user.id
    logger.debug(f"Flink add_image callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send the image:</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━</b>")
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                parse_mode=ParseMode.HTML
            )
        else:
            logger.debug(f"Skipping edit in flink_add_image_callback for user {user_id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Send image"))
    except Exception as e:
        logger.error(f"Error in flink_add_image_callback for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ An error occurred while adding image.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.photo & filters.reply)
async def handle_image_input(client: Client, message: Message):
    """Handle user image input for flink output."""
    user_id = message.from_user.id
    logger.debug(f"Handling image input for user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
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

        if not (message.reply_to_message and to_small_caps_with_html("<b>Send the image:</b>") in message.reply_to_message.text.lower()):
            logger.warning(f"Ignoring image input for user {user_id} - not a reply to an image prompt")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the image prompt with a valid image.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Image successfully saved.</b></blockquote>\n<blockquote>Type a caption if needed, or proceed with 'Done'.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_image_input for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing image.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding a caption to flink output."""
    user_id = query.from_user.id
    logger.debug(f"Flink add caption callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        flink_user_data[user_id]['awaiting_caption'] = True
        caption_prompt_text = (
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Type your caption:</b></blockquote>\n\n") +
            "<blockquote><b>Example</b></blockquote>\n\n" +
            "<blockquote><code>ᴛɪᴛʟᴇ- BLACK CLOVER\n" +
            "<b>Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅɪ Dᴜʙʙᴇᴅ\n\n" +
            "<b>Qᴜᴀʟɪᴛʏ - 360ᴘ, 720P, 1080ᴘ\n\n" +
            "<b>Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n" +
            "<b>Aʟʟ Qᴜᴀʟɪᴛʏ - ( Hɪɴᴅɪ Dᴜʙʙᴇᴅ )\n" +
            "━━━━━━━━━━━━━━━━━━━\n" +
            "Cʟɪᴄᴋ Hᴇʀᴇ Tᴏ Dᴏᴡɴʟᴏᴀᴅ | Eᴘ - 01 & S1</code></blockquote>\n\n" +
            to_small_caps_with_html("<b>Reply to this message with your caption.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>")
        )
        
        caption_prompt_msg = await query.message.reply(
            text=caption_prompt_text,
            parse_mode=ParseMode.HTML
        )
        flink_user_data[user_id]['caption_prompt_message'] = caption_prompt_msg
        
        await query.answer(to_small_caps_with_html("Type caption"))
    except Exception as e:
        logger.error(f"Error in flink_add_caption_callback for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while adding caption.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.text & filters.reply & ~filters.regex(r"^CANCEL$", flags=re.IGNORECASE) & ~filters.forwarded)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for the flink command."""
    user_id = message.from_user.id
    logger.debug(f"Caption input received from user {user_id}, text: {message.text}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

    try:
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No active caption prompt found.</b>\n<b>Please use the 'Add Caption' option first.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        caption_prompt_msg = flink_user_data[user_id].get('caption_prompt_message')
        if not caption_prompt_msg or not message.reply_to_message or message.reply_to_message.id != caption_prompt_msg.id:
            logger.info(f"Caption input ignored for user {user_id} - not a reply to caption prompt")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Please reply to the caption prompt message with your caption.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.text
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Caption saved successfully.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_caption_input for user {user_id}: {e}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing caption.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output_callback(client: Client, query: CallbackQuery):
    """Handle callback for finalizing flink output."""
    user_id = query.from_user.id
    logger.debug(f"Flink done output callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        if user_id not in flink_user_data or 'links' not in flink_user_data[user_id]:
            await query.message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No links found.</b>\n<b>Please start the process again using /link.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        # Generate the final output and send a new message
        await flink_generate_final_output(client, query.message)
        
        # Clean up user data
        if user_id in flink_user_data:
            del flink_user_data[user_id]
        
        # Delete the original menu message
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Process completed"))
    except Exception as e:
        logger.error(f"Error in flink_done_output_callback for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while completing process.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Handle callback to refresh flink menu."""
    user_id = query.from_user.id
    logger.debug(f"Flink refresh callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Format status refreshed"))
    except Exception as e:
        logger.error(f"Error in flink_refresh_callback for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while refreshing status.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^(flink_(back_to_menu|cancel_process|back_to_output|close))$"))
async def flink_handle_back_buttons(client: Client, query: CallbackQuery):
    """Handle back, cancel, and close actions for flink command."""
    user_id = query.from_user.id
    action = query.data.split("_")[-1]
    logger.debug(f"Flink {action} callback triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    try:
        if action == "back_to_menu":
            await show_flink_main_menu(client, query.message, edit=True)
            await query.answer(to_small_caps_with_html("Back to menu"))
        elif action == "cancel_process":
            await query.message.edit_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            if user_id in flink_user_data:
                del flink_user_data[user_id]
            await query.answer(to_small_caps_with_html("Process cancelled"))
        elif action == "back_to_output":
            await flink_generate_final_output(client, query.message)
            await query.answer(to_small_caps_with_html("Back to output"))
        elif action == "close":
            await query.message.delete()
            if user_id in flink_user_data:
                del flink_user_data[user_id]
            await query.answer(to_small_caps_with_html("Menu closed"))
    except Exception as e:
        logger.error(f"Error in flink_handle_back_buttons for user {user_id}: {e}")
        await query.message.edit_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing action.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
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
