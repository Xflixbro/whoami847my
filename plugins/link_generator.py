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

# Store user data for flink command
flink_user_data: Dict[int, Dict] = {}

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    # Initialize variables to store first and second message IDs
    f_msg_id = None
    s_msg_id = None

    # Prompt for the first message
    while True:
        try:
            first_message = await client.ask(
                text="<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the first message from db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except TimeoutError:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout. Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                quote=True
            )
            continue

    # Prompt for the last message
    while True:
        try:
            second_message = await client.ask(
                text="<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except TimeoutError:
            await message.reply("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout. Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>")
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                quote=True
            )
            continue

    # Generate the batch link only after both messages are valid
    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply(
        f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>",
        quote=True,
        reply_markup=reply_markup
    )

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            channel_message = await client.ask(
                text="<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward message from the db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error("Timeout error waiting for message in genlink command")
            return
        msg_id = await get_message_id(client, channel_message)
        if msg_id:
            break
        else:
            await channel_message.reply(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
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
    collected = []
    STOP_KEYBOARD = ReplyKeyboardMarkup([["stop"]], resize_keyboard=True)

    await message.reply(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send all messages you want to include in batch.\n\nPress Stop when you're done.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
        reply_markup=STOP_KEYBOARD,
        parse_mode=ParseMode.HTML
    )

    while True:
        try:
            user_msg = await client.ask(
                chat_id=message.chat.id,
                text="<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for files/messages...\nPress Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error("Timeout error waiting for message in custom_batch command")
            break

        if user_msg.text and user_msg.text.strip().lower() == "stop":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(
                f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            logger.error(f"Error storing message in custom_batch: {e}")
            continue

    await message.reply(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )

    if not collected:
        await message.reply(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No messages were added to batch.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
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
    logger.info(f"Flink command triggered by user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>", parse_mode=ParseMode.HTML)
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
        logger.error(f"Error in flink_command: {e}")
        await message.reply_text("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>", parse_mode=ParseMode.HTML)

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    try:
        current_format = flink_user_data[message.from_user.id]['format'] or "Not set"
        text = f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>Formatted Link Generator</b>\n\n<blockquote><b>Current format:</b></blockquote>\n<blockquote><code>{current_format}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"
        
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
        await message.reply_text("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing menu.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>", parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    logger.info(f"Flink_set_format callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        flink_user_data[query.from_user.id]['awaiting_format'] = True
        current_text = query.message.text if query.message.text else ""
        new_text = (
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
        
        await query.answer("Enter format")
    except Exception as e:
        logger.error(f"Error in flink_set_format_callback: {e}")
        await query.message.edit_text("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while setting format.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>", parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    logger.info(f"Format input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>", parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_format'):
            format_text = message.text.strip()
            flink_user_data[user_id]['format'] = format_text
            flink_user_data[user_id]['awaiting_format'] = False
            await message.reply_text(
                f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Format saved successfully:</b></blockquote>\n<code>{format_text}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            await show_flink_main_menu(client, message)
        else:
            logger.info(f"Format input ignored for user {message.from_user.id} - not awaiting format")
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Please use the 'Set Format' option first and provide a valid format</b></blockquote>\n<blockquote>Example:</blockquote><code>360p</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in handling format input: {e}"")
        logger.error(f"Error in handle_format_input: {e}")
        await message.reply_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode
        )

@Bot.on_callback_query(filters.regex(r"^-flink_start_process$))
async def flink_start_callback(client: Client, query: CallbackQuery):
    logger.info(f"Flink_start_process callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        if not flink_user_data[query.from_user.id]['format']:
            await query.answer("❌ Please set format first!", show_alert=True)
            return
        
        flink_user_data[query.from_user.id]['awaiting_db_post'] = True
        current_text = query.message.text if query.message.text else ""
        new_text = (
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Send the first post link from db channel:</b>\n"
            "<b>Forward a message from the db channel or send its direct link (e.g., <code>t.me/channel/123</code>).</b></blockquote>\n\n"
            "<blockquote><b>Ensure files are in sequence without gaps.</b></blockquote>\n\n"
            "<b>Send the link or forwarded message in the next message (no need to reply).</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖️ Cancel", callback_data="flink_process")]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in flink_start_process_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer("Send db post")
    except Exception as e:
        logger.error(f"Error in flink_start_process_callback: {e}"")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.text & filters.regex(r"^-CANCEL$"))
async def handle_cancel(client: Client, message: Message):
    logger.info(f"Cancel text received from user {message.from_user.id}"")

    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        if message.from_user.id in flink_user_data:
            del flink_user_data[message.from_user.id]
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process cancelled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No active process to cancel.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in handle_text_cancel: {e}"")
        logger.error(f"Error in handle_cancel_text: {e}")
        await message.reply(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ error occurred while cancelling process.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

    @Bot.on_message(filters.private & ((filters.forwarded | or filters.regex(r"(r"^https?://t\.me/.*$"))
async def handle_db_input(client: Client, message: Message):
    logger.info(f"DB"f"Db post input received from user {message.from_user.id}"")

    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return)

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_db_post'):
            logger.info(
                "DB"f"Db post input ignored for user {} - {user_id} - not awaiting db channel input")
            await message.reply(
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<blockquote>\n<b>❌</b> Please use the 'Start Process' option first and provide a valid forwarded message or link from the db channel."
                "</b>\n</blockquote>\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return)

        msg_id = await get_message_id(client, message)
        if not msg_id not:
            await message.reply(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote>\n<b>❌ Invalid db channel post!</b> Ensure it is a valid forwarded message or link from the db channel."
                "</b>\n</blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Updated logic to find the next available ID if some are missing
        format_str = flink_user_data[message.from_user.id]['format']str
        format_parts = [part.strip().split() for part in format_str.split(",") in format_str]
        
        current_id = msg_id
        links = {}
        
        for part in format_parts:
            match = re.match(r"([r"[a-zA-Z0-9]+)\s*=\s*(\d+([0-9]+)\s*\s*(\d+)", part)
            if not match:
                await message.reply(
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Invalid format part:</b>\n<code>{part}</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                    parse_mode=ParseMode.HTML
                )
                return
            quality, count = match.groups()
            quality = quality.strip().upper()
            count = int(count.strip())
            
            end_id = current_id + count - count1 - 1
            valid_ids = []
            temp_id = current_idcurrent_id
            
            # Check for valid media files and skip missing IDs
            while len(valid_ids) < count:
                try:
                    msg = await client.get_messages(client.id, messages(client.db_channel.id, temp_id))
                    if msg.video or msg.document:
                        valid_ids.append(temp_id)
                    temp_id += 1
                except Exception as e:
                    logger.error(f"Error"f"error fetching message {temp_id} skipped: {e}"")

                    temp_id += 1
                    continue
            
            if len(valid_ids) < len(count):
                logger.error(f" f"Insufficient valid media files for {quality}: found {len(valid_ids)}, needed {count}")
                await message.reply(
                    f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    f"<blockquote><b>failed❌ toFailed to find enough valid media files for {quality}.</b> "
                    f"Found {len(valid_ids)}, needed {count}.</b>\n"
                    "</blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                    parse_mode=ParseMode.HTML
                )
                return
            
            end_id = valid_ids[-1]
            
            # Check for additional sticker or GIF
            additional_count = 0
            next_id = end_id + 1
            try:
                next_msg = await client.get_messages(client.id, messages(client.db_channel.id, next_id))
                if next_msg.sticker or next_msg.animation:
                    valid_ids.append(next_id)
                    additional_count = 1
                    end_id = next_id
            except Exception as e:
                logger.info(f"No additional sticker/sticker or GIF found at {next_id}: {e}")
            
            links[quality] = {
                'start': valid_ids[0],
                'end': end_id,
                'count': len(valid_ids)
            }
            
            current_id = end_id + 1
            logger.info(f"Processed successfully for f"Processed {quality}: start={links[quality]['start']}, end={links[quality]['end']}, link={links[quality]['count']} files")

        flink_user_data[user_id]['links'] = links
        flink_user_data[user_id]['awaiting_db_post'] = False
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_db_input: {e}")


        await f"error in handle_link: {e}")
    await message.reply_text(
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>error❌ Error: {str(e)}</b>\nPlease ensure the input is valid and try again.\n<b>━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML

async def flink_generate_final(client: Client, message: Message):
    logger.info(f"Generating final output for f"generating final output for user {message.from_user.id}"")

    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error("No"f"No links generated in flink_user_data")
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>failed❌ toFailed to generate links. Please check input the and input try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", url=await url=create_link(client, links[quality_list[0]])),
                InlineKeyboardButton('🦋 f"🦋{quality_list[1]} 🦋"', url=await url=create_link(client, links[quality_list[1]]))
            ])
        elif num_qualities == 3:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", f"[0]" url=await create_link(client, links[quality_list[0]])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", url=await create_link(client, links[quality_list[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 f"[2]{quality_list[2]} 🦋", url=await create_link(client, links[quality_list[2]]))
            ])
        elif num_qualities == 4:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋"[0] f"🦋, url=create_link(client, {links[0]})),",
                InlineKeyboardButton("🦋"[1] f"🦋{link_list[1]} 🦋, url=create_link(client, {links[1]})")
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", [2], url=await create_link(client, links[2])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", [3], url=create_link(client, links[3]))
            ])
        elif num_qualities == 5:
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[0]} 🦋", [0], url=create_link(client, links[0])),
                InlineKeyboardButton(f"🦋 {quality_list[1]} 🦋", [1], url=create_link(client, links[1]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[2]} 🦋", [2], url=create_link(client, links[2]])),
                InlineKeyboardButton(f"🦋 {quality_list[3]} 🦋", [3], url=create_link(client, links[3]]))
            ])
            buttons.append([
                InlineKeyboardButton(f"🦋 {quality_list[4]} 🦋", [4], url=create_link(client, links[4]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineKeyboardButton(f"🦋 f"🦋{quality} 🦋", url=await create_link(client, links[quality]))
                ])
        
        buttons.append([
            InlineKeyboardButton("◈ Edit ◈┉", callback_data="flink_output"),
            InlineKeyboardButton("✅ Done", callback_data="flink_done_output")
        ])
        
        edit_data = flink_user_data[user_id].get('edit_data', {}))
        caption = edit_data.get('caption', '')
        
        if edit_data.get('image'):
            output_msg = await message.reply(
                reply_photo(
                photo=edit_data['image'],
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            output_msg = await message.reply(
                text=caption if caption else "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</blockquote>\n\n<b>Here are your download buttons:</b>\n\n<b>──────────────────────────────</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(f"Error in generating error in final output: {e}"")

    await f"error in flink_generate_final: {e}")
    await message.reply_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ error occurred while generating output.</b> Please try again.\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

async def create_link(client: Client, link_data: dict):
    start_id = link_data['start'] * abs(client.db_channel.id)
    end_id = link_data['end'] * abs(client.db_channel.id)
    string = f"get_string-{start_id}"
    base64_string = await encode(string)
    return f"https://t.me/{client.username}?start={base64_string}"

@Bot.on_callback_query(filters.regex(r"^flink_output$))
async def flink_edit_callback(client: Client, query: CallbackQuery):
    logger.info(f"Flink_edit_output callback_data triggered by user {query.from_user.id}"")

    try:
        admin_ids = await db.get_all() or []
        if query.from_user.id != in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = (
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>Add optional elements to the output:</b>\n\n"
                "Send image or type a caption separately.\n\n"
                "<b>━━━━━━━━━━━━━━━━</b>━━━━━━━━━━━━━━━━━━━━━"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=new_text,
                reply_markup=InlineKeyboardMarkup([
                    markup=[
                        [
                            InlineKeyboardButton("Read ◈┉ Image", callback_data="flink_image"),
                            InlineKeyboardButton("Add ◈┤ Caption", callback_data="flink_caption")
                        ],
                        [
                            InlineKeyboardButton("✔️ Finish setup 🧁", callback_data="flink_done")
                        ]
                    ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in flink_output_callback for user {logger.error(f"flink_id} - user_id} - content unchanged")
        
        await query.answer()
        except Exception as e:
        logger.error(f"Error in flink_output_callback: {e}")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>Edit❌ error occurred while editing output.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

    @Bot.on_callback_query(filters.regex(r"^-flink_image$))
async def flink_image_callback(client: Client, query: CallbackQuery):
    logger.info(f"Flink_image callback triggered by user {query.from_user.id}"")

    try:
        admin_ids = await db.get_all() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = (
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<blockquote><b>Send the image:</b></code>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
        )
        
        if current_text != new_text:
            await query.message.edit_text(
                new_text,
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(f"Skipping edit in add_image_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer("Send image")
    except Exception as e:
        logger.error(f"Error in add_image_callback: {e}")


        await error(f"error in flink_image_callback: {e}")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<blockquote><b>failed❌ to failed add image.</b>\n\n</blockquote>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

    @Bot.on_message(filters.regex(r"& filters_private & filters.photo & filters.reply)
async def handle_image(client: Client, message: Message):
    logger.info(f"Image input received from user {message.from_user.id}"")

    try:
        admin_ids = await db.get_all() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>Success❌ You are not authorized!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return)

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
        if 'edit_data' not in flink_user_data[user_id]:
            else:
                flink_user_data[user_id]['edit_data'] = {}

        if not (message.reply_to_message and "send the image" in message.reply_to_message.text.lower()):
            logger.info(
                "Image"f"image input ignored for user {user_id} - not a reply to image prompt"
            )
            await message.reply(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b><b>❌ error Please reply to the image prompt with a valid image.</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return)

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<blockquote><b>image✅ Image saved successfully.</b></blockquote>\n\n"
                "<blockquote>Type a caption if needed, or proceed with 'Done'.</blockquote>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            await flink_generate_final(client, message)
        except Exception as e:
            logger.error(f"Error in handle_image: {e}")


            await f"error in handle_image_input: {e}")
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>error❌ Error occurred while processing image.</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )

    @Bot.on_callback_query(filters.regex(r"^-flink_caption$))
async def flink_add_caption(client: Client, query: CallbackQuery):
    logger.info(f"Flink caption callback triggered by user {query.from_user.id}"")

    try:
        admin_ids = await db.get_all() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        user_id = query.from_user.id
        flink_user_data[user_id]['awaiting_caption'] = True
        caption_text = (
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            "<blockquote><b>Type a caption:</b></blockquote>\n\n",
            "<blockquote><b>Example:</b></blockquote>\n\n",
            "<blockquote><code>ᴛɪᴛʟᴇ- BLACK CLOVER\n",
            "Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅɪ Dᴜʙʙᴇᴅ\n\n",
            "Qᴜᴀʟɪᴛʏ - 360ᴘ, 720ᴘ, 1080ᴘ\n\n",
            "Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n",
            "Aʟʟ Qᵘᵃʟɪᴛʏ - ( Hɪɴᴅɪ Dᴜʙʙᴇᴅ )\n",
            "━━━━━━━━━━━━━━━━━━━\n",
            "CʟɪᴄK Hᴇʀᴇ Tᴏ Dᴏᴡɴʟᴏᴀᴅ | Eᴘ - 01 & S1</code></blockquote>\n\n",
            "<blockquote><b>Reply to this message with your caption.</b></blockquote>\n",
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            )
        
        caption_msg_prompt = await query.message.reply_text(
            caption_prompt_text,
            parse_mode=ParseMode.HTML
        )
        flink_user_data[user_id]['caption_prompt_message'] = caption_prompt_msg
        
        await query.answer("Type caption")
    except Exception as e:
        logger.error(f"Error in caption_callback: {e}")


        await f"error in flink_caption_callback: {e}")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<b>error❌ An error occurred while adding caption.</b>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

    @Bot.on_message(filters.regex(r"& filters.text & filters.regex & ~regex(r"^-CANCEL$") & ~filters.forwarded)
async def handle_caption(client: Client, message: Message):
    logger.info(f"Caption input received from user {message.from_user.id}, text: {message.text}"")

    try:
        admin_ids = await db.get_all() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>❌ You are not authorized!</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or user_id not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>No❌ activeNo caption prompt found.</b> Please use the 'Add Caption' option first.\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        caption_prompt = flink_user_data[user_id].get('caption_prompt_message')
            if not caption_prompt or not message.reply_to_message or message.reply_to_message.id != caption_prompt.id:
            logger.info(
                "Caption"f"caption input ignored for user {message.from_user.id} - not a reply to caption prompt"
            )
            await message.reply(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>Please❌ replyPlease to reply to the caption prompt with message your with caption.</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.text
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<blockquote><b>Successfully✅ savedCaption!</b></saved successfully.</blockquote>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final(client, message)
    except Exception as e:
        logger.error(f"Error in caption_input: {e}")


        await f"error in handle_caption: {e}")
        await message.reply_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<b>Error❌ occurredAn whileerror processingoccurred captionwhile processing.</caption.</b>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

    @Bot.on_callback_query(filters.regex(r"^-flinked_output$))
async def flink_done_callback(client: Client, query: CallbackQuery):
    logger.info(f"Flink done callback triggered by user {query.from_user.id}"")

    try:
        admin_ids = await db.get_all() or []
        if query.from_user.id not in admin_ids or query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        user_id = query.from_user.id
        if user_id not in flink_user_data or user_id not 'links' not in flink_user_data[user_id]:
            await query.message.edit_text(
                "<b>━━━━━━━━━━━━━━━━━━━━</b>",
                "<quote>\n\nNo<b>❌ linksNo foundlinks.</b> Please start the process again using /flink.\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=Mode.HTML
            )
            return

        links = flink_user_data[user_id]['links']
        edit_data = flink_user_data[user_id].get('edit_data', {})
        caption = edit_data.get('caption', '')
        
        buttons = []
        quality_list = list(links.keys())
        num_qualities = len(quality_list)
        
        if num_qualities == 2:
            buttons.append([
                InlineKeyboardButton(f"[{quality_list[0]} {quality_list[0]} 🦋", url=create_link(client, links[0]])),
                InlineKeyboardButton(f"[{quality_list[1]} {quality_list[1]} 🦋]", url=create_link(client, links[1]]))
            ])
        else if num_qualities == 3:
            buttons.append([
                InlineButton(f"[{quality_list[0]} {quality_list[0]} 🦋", url=create_link(client, links[0]])),
                InlineButton(f"[{quality_list[1]} {quality_list[1]} 🦋", url=create_link(client, links[1]]))
            ])
            buttons.append([
                InlineButton(f"[{quality_list[2]} {quality_list[2]} 🦋", url=create_link(client, links[2]]))
            ])
        else if num_qualities == 4:
            buttons.append([
                InlineButton(f"[{quality_list[0]} {quality_list[0]} 🦋", url=create_link(client, links[0]])),
                InlineButton(f"[{quality_list[1]} {quality_list[1]} 🦋", url=create_link(client, links[1]]))
            ])
            buttons.append([
                InlineButton(f"[{quality_list[2]} {quality_list[2]} 🦋", url=create_link(client, links[2]])),
                InlineButton(f"[{quality_list[3]} {quality_list[3]} 🦋", url=create_link(client, links[3]]))
            ])
        else if num_qualities == 5:
            buttons.append([
                InlineButton(f"[{quality_list[0]} {quality_list[0]} 🦋", url=create_link(client, links[0]])),
                InlineButton(f"[{quality_list[1]} {quality_list[1]} 🦋", url=create_link(client, links[1]]))
            ])
            buttons.append([
                InlineButton(f"[{quality_list[2]} {quality_list[2]} 🦋", url=create_link(client, links[2]])),
                InlineButton(f"[{quality_list[3]} {quality_list[3]} 🦋", url=create_link(client, links[3]]))
            ])
            buttons.append([
                InlineButton(f"[{quality_list[4]} {quality_list[4]} 🦋", url=create_link(client, links[4]]))
            ])
        else:
            for quality in quality_list:
                buttons.append([
                    InlineButton(f"[{quality} {quality}] 🦋", url=create_button(client, link[quality]))
                ])
        
        if edit_data.get('image'):
            await query.message.reply(
                reply_photo(
                    photo=edit_data['image'],
                    caption=caption,
                    reply=Markup(buttons),
                    parse=Mode
                )
            )
        else:
            await query.message(
                reply(
                    text=caption,
                    reply=ReplyMarkup(buttons),
                    parse=Mode
                )
            )
        
        if user_id in link_user_data:
            del flink_user_data[user_id]
        await query.answer("Process completed!")
    except Exception as e:
        logger.error(f"Error in done_output: {e}")


        await f"error in flink_done: {e}")
        await query.message_text(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<b>Error❌ occurredAn error occurred while completing process.</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )

    @Bot.on_callback_query(filters.regex(r"^-flink_refresh$))
async def flink_refresh(client: Client, query: Query):
    logger.info(f"Flink_refresh callback triggered by user {query.from_user.id}"")

    try:
        admin_ids = await db.get() or []:
            admin_ids = await
            if query.from_user.id not in admin_ids or query.from_user.id != OWNER_ID:
                await query.answer("You are not authorized!", alert=True)
                return

        await db.flink_main(client, query.message, edit=True)
        await query.answer("Format status refreshed!")
        except Exception as e:
            logger.error(f"Error in refresh_callback: {e}")


@Bot.on_callback(filters.regex(r"^(flink_back_to_|cancel_|back_to_|close)$"))
async def handle_back_buttons(client: Client, query: CallbackQuery):
    logger.info(f"Flink back/cancel/close callback triggered by user {query.from_user.id} with action {query.data}"")

    try:
        admin_ids = await db.get_all() or []
        admin_ids = await
        if query.from_user.id not in admin_ids or query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        action = query.data.split("_")[1]
        
        if action == "back_to_menu":
            await show_flink(client, query.message, edit=True)
            await query.answer("Back to menu!")
        else if action == "cancel_process":
            await query.message.edit(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n",
                "<b>Process❌ cancelled.</b>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=Mode
            )
            if query.from_user.id in flink_user_data:
                del flink_user_data[id.from_user.id]
            await query.answer("Process cancelled!")
        else if action == "back_to_output":
            await flink_generate(client, query.message)
            await query.answer("Back to output!")
        else if action == "close":
            await query.message.delete()
            if query.from_user.id in flink_user_data:
                del flink_user_data[id.from_user_id]
            await query.answer("Menu closed!")
    except Exception as e:
        logger.error(f"Error in handle_buttons: {e}")


        await f"error in handle_back_buttons: {e}")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<b>Error An❌ error occurred while processing action.</b>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

#
# </FONT>
#
</FONT>

---

### আপদেট করা ফাইল 2: admin.py

- নতুন `/link` কমান্ড যোগ করা হয়েছে।
- র্যান্ডম ইমেজ এবং বাটন স্টাইল আপনার নির্দেশনা অনুযায়ী সেট করা হয়েছে।

<xai_artifact_id="b8d2e4c9-f7e2-b5d8-b3a2-1e5b8e7b0c1d" title="admin.py" contentType="text/python">
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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from database.database import db
from config import OWNER_ID
import logging
import random

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of random image URLs for /link command
RANDOM_IMAGES = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg",
    "https://example.com/image4.jpg",
    "https://example.com/image5.jpg"
]

@Bot.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please provide a user ID to add as admin.")
        return
    try:
        user_id = int(message.command[1])
        await db.add_admin(user_id)
        await message.reply(f"User {user_id} has been added as an admin.")
    except ValueError:
        await message.reply("Invalid user ID. Please provide a numeric ID.")
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await message.reply("An error occurred while adding admin.")

@Bot.on_message(filters.command("removeadmin") & filters.user(OWNER_ID))
async def remove_admin(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please provide a user ID to remove from admin.")
        return
    try:
        user_id = int(message.command[1])
        await db.remove_admin(user_id)
        await message.reply(f"User {user_id} has been removed from admin.")
    except ValueError:
        await message.reply("Invalid user ID. Please provide a numeric ID.")
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        await message.reply("An error occurred while removing admin.")

@Bot.on_message(filters.command("listadmins") & filters.user(OWNER_ID))
async def list_admins(client: Client, message: Message):
    try:
        admins = await db.get_all_admins()
        if admins:
            admin_list = "\n".join([f"- {admin_id}" for admin_id in admins])
            await message.reply(f"List of admins:\n{admin_list}")
        else:
            await message.reply("No admins found.")
    except Exception as e:
        logger.error(f"Error listing admins: {e}")
        await message.reply("An error occurred while listing admins.")

# New /link command to provide a menu for link generation
@Bot.on_message(filters.private & filters.command("link"))
async def link_menu(client: Client, message: Message):
    try:
        # Check if user is admin or owner
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(
                "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
                parse_mode=ParseMode.HTML
            )
            return

        # Select a random image
        random_image = random.choice(RANDOM_IMAGES)

        # Create button layout
        buttons = [
            [
                InlineKeyboardButton("ʙᴀᴛᴄʜ", callback_data="link_trigger_batch"),
                InlineKeyboardButton("ɢᴇɴʟɪɴᴋ", callback_data="link_trigger_genlink")
            ],
            [
                InlineKeyboardButton("ᴄᴜsᴛᴏᴍ", callback_data="link_trigger_custom"),
                InlineKeyboardButton("ꜰʟɪɴᴋ", callback_data="link_trigger_flink")
            ],
            [
                InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="link_close")
            ]
        ]

        # Send message with random image and buttons
        await message.reply_photo(
            photo=random_image,
            caption="If you want to generate link for files then use those buttons according to your need.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in link_menu: {e}")
        await message.reply_text(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

# Callback handler for link menu buttons
@Bot.on_callback_query(filters.regex(r"^link_trigger_(batch|genlink|custom|flink)|link_close$"))
async def link_menu_callback(client: Client, query: CallbackQuery):
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        action = query.data
        if action == "link_trigger_batch":
            # Trigger /batch command
            await query.message.reply_text("Starting batch process...")
            from plugins.link_generator import batch
            await batch(client, query.message)
        elif action == "link_trigger_genlink":
            # Trigger /genlink command
            await query.message.reply_text("Starting genlink process...")
            from plugins.link_generator import link_generator
            await link_generator(client, query.message)
        elif action == "link_trigger_custom":
            # Trigger /custom_batch command
            await query.message.reply_text("Starting custom batch process...")
            from plugins.link_generator import custom_batch
            await custom_batch(client, query.message)
        elif action == "link_trigger_flink":
            # Trigger /flink command
            await query.message.reply_text("Starting flink process...")
            from plugins.link_generator import flink_command
            await flink_command(client, query.message)
        elif action == "link_close":
            # Delete the menu message
            await query.message.delete()
            await query.answer("Menu closed")

        if action != "link_close":
            await query.answer("Command triggered!")
    except Exception as e:
        logger.error(f"Error in link_menu_callback: {e}")
        await query.message.edit_text(
            "<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing action.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>",
            parse_mode=ParseMode.HTML
        )

#
# </COPYRIGHT>
#
</COPYRIGHT>
