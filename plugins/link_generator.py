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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.enums import ParseMode
from bot import Bot
from helper_func import encode, get_message_id, admin
import re
from typing import Dict
import logging
from config import OWNER_ID, RANDOM_IMAGES
from database.database import db
from asyncio import TimeoutError
import random

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

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_menu(client: Client, message: Message):
    """Display a menu with buttons to trigger link generation commands."""
    random_image = random.choice(RANDOM_IMAGES)
    text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ ꜰᴏʀ ꜰɪʟᴇs, ᴛʜᴇɴ ᴜsᴇ ᴛʜᴇsᴇ ʙᴜᴛᴛᴏɴs ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ʏᴏᴜʀ ɴᴇᴇᴅ.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )
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
    await message.reply_photo(
        photo=random_image,
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex(r"^link_trigger_(batch|genlink|custom|flink)$"))
async def link_trigger_callback(client: Client, query: CallbackQuery):
    """Handle callback queries for triggering link generation commands."""
    command = query.data.split("_")[-1]
    await query.message.delete()
    
    # Create a mock message object to simulate command execution
    mock_message = Message(
        message_id=query.message.id,
        chat=query.message.chat,
        from_user=query.from_user,
        date=query.message.date,
        text=f"/{command}",
        client=client
    )
    
    # Call the appropriate command handler
    try:
        if command == "batch":
            await batch(client, mock_message)
        elif command == "genlink":
            await link_generator(client, mock_message)
        elif command == "custom":
            await custom_batch(client, mock_message)
        elif command == "flink":
            await flink_command(client, mock_message)
        await query.answer(to_small_caps_with_html(f"{command.capitalize()} command triggered"))
    except Exception as e:
        logger.error(f"Error in link_trigger_callback for command {command}: {e}")
        await client.send_message(
            chat_id=query.from_user.id,
            text=to_small_caps_with_html(f"<b>❌ Error executing {command} command: {str(e)}</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^link_close$"))
async def link_close_callback(client: Client, query: CallbackQuery):
    """Handle callback query for closing the link menu."""
    try:
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Menu closed"))
    except Exception as e:
        logger.error(f"Error in link_close_callback: {e}")

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Generate a batch link for a range of messages from the db channel."""
    try:
        # Wait for the first message
        while True:
            try:
                first_message = await client.ask(
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the first message from db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>"),
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout error waiting for first message.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                return
            f_msg_id = await get_message_id(client, first_message)
            if f_msg_id:
                break
            else:
                await first_message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                continue

        # Wait for the last message
        while True:
            try:
                second_message = await client.ask(
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>"),
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout error waiting for last message.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                return
            s_msg_id = await get_message_id(client, second_message)
            if s_msg_id:
                break
            else:
                await second_message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or this link is not valid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                continue

        # Generate the batch link
        string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(to_small_caps_with_html("🔁 Share URL"), url=f'https://telegram.me/share/url?url={link}')]])
        await second_message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            quote=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in batch command: {e}")
        await message.reply_text(to_small_caps_with_html(f"<b>❌ Error: {str(e)}</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Generate a link for a single message from the db channel."""
    try:
        while True:
            try:
                channel_message = await client.ask(
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward message from the db channel (with quotes).\nOr send the db channel post link\n</b></blockquote><b>━━━━━━━━━━━━━━━━━━</b>"),
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout error waiting for message.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(to_small_caps_with_html("🔁 Share URL"), url=f'https://telegram.me/share/url?url={link}')]])
        await channel_message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            quote=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in genlink command: {e}")
        await message.reply_text(to_small_caps_with_html(f"<b>❌ Error: {str(e)}</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    """Generate a custom batch link by collecting messages."""
    try:
        collected = []
        STOP_KEYBOARD = ReplyKeyboardMarkup([["stop"]], resize_keyboard=True)

        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send all messages you want to include in batch.\n\nPress Stop when you're done.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            reply_markup=STOP_KEYBOARD,
            parse_mode=ParseMode.HTML
        )

        while True:
            try:
                user_msg = await client.ask(
                    chat_id=message.chat.id,
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for files/messages...\nPress Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout error waiting for message.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                break

            if user_msg.text and user_msg.text.strip().lower() == "stop":
                break

            try:
                sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
                collected.append(sent.id)
            except Exception as e:
                await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                logger.error(f"Error storing message in custom_batch: {e}")
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

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(to_small_caps_with_html("🔁 Share URL"), url=f'https://telegram.me/share/url?url={link}')]])
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error in custom_batch command: {e}")
        await message.reply_text(to_small_caps_with_html(f"<b>❌ Error: {str(e)}</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & admin & filters.command("flink"))
async def flink_command(client: Client, message: Message):
    """Start the formatted link generation process."""
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
        
        await show_flink_main_menu(client, message)
    except Exception as e:
        logger.error(f"Error in flink_command: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred. Please try again.</b>"), parse_mode=ParseMode.HTML)

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    """Show the main menu for the flink command."""
    try:
        current_format = flink_user_data[message.from_user.id]['format'] or "Not set"
        text = to_small_caps_with_html(
            f"<b>━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>Formatted Link Generator</b>\n\n"
            f"<blockquote><b>Current format:</b></blockquote>\n"
            f"<blockquote><code>{current_format}</code></blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━━</b>"
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
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while showing menu.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle setting the format for flink."""
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
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while setting format.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink."""
    logger.info(f"Format input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>❌ You are not authorized!</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_format'):
            format_text = message.text.strip()
            flink_user_data[user_id]['format'] = format_text
            flink_user_data[user_id]['awaiting_format'] = False
            await message.reply_text(to_small_caps_with_html(f"<b>✅ Format saved successfully:</b>\n<code>{format_text}</code>"), parse_mode=ParseMode.HTML)
            await show_flink_main_menu(client, message)
        else:
            logger.info(f"Format input ignored for user {message.from_user.id} - not awaiting format")
            await message.reply_text(
                to_small_caps_with_html(
                    "<b>❌ Please use the 'Set Format' option first and provide a valid format</b>\n"
                    "<blockquote>Example:</blockquote> <code>360p = 2, 720p = 1</code>"
                ),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error in handle_format_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while processing format.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_start_process$"))
async def flink_start_process_callback(client: Client, query: CallbackQuery):
    """Start the process of collecting db channel post for flink."""
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
            "<blockquote><b>Send the first post link from db channel:</b>\n"
            "<b>Forward a message from the db channel or send its direct link (e.g., <code>t.me/channel/123</code>).</b></blockquote>\n\n"
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
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while starting process.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^CANCEL$"))
async def handle_cancel_text(client: Client, message: Message):
    """Handle cancellation of flink process."""
    logger.info(f"Cancel text received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>❌ You are not authorized!</b>"), parse_mode=ParseMode.HTML)
            return

        if message.from_user.id in flink_user_data:
            del flink_user_data[message.from_user.id]
            await message.reply_text(to_small_caps_with_html("<b>❌ Process cancelled.</b>"), parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(to_small_caps_with_html("<b>❌ No active process to cancel.</b>"), parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error in handle_cancel_text: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while cancelling process.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & (filters.forwarded | filters.regex(r"^https?://t\.me/.*$")))
async def handle_db_post_input(client: Client, message: Message):
    """Handle db channel post input for flink."""
    logger.info(f"Db post input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>❌ You are not authorized!</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_db_post'):
            logger.info(f"Db post input ignored for user {user_id} - not awaiting db channel input")
            await message.reply_text(
                to_small_caps_with_html(
                    "<b>❌ Please use the 'Start Process' option first and provide a valid forwarded message or link from the db channel.</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            return

        msg_id = await get_message_id(client, message)
        if not msg_id:
            await message.reply(to_small_caps_with_html("<b>❌ Invalid db channel post! Ensure it's a valid forwarded message or link from the db channel.</b>"), parse_mode=ParseMode.HTML)
            return
                
        format_str = flink_user_data[message.from_user.id]['format']
        format_parts = [part.strip() for part in format_str.split(",")]
        
        current_id = msg_id
        links = {}
        skipped_ids = []
        
        for part in format_parts:
            match = re.match(r"([a-zA-Z0-9]+)\s*=\s*(\d+)", part)
            if not match:
                await message.reply(to_small_caps_with_html(f"<b>❌ Invalid format part:</b> <code>{part}</code>"), parse_mode=ParseMode.HTML)
                return
            quality, count = match.groups()
            quality = quality.strip().upper()
            count = int(count.strip())
            
            valid_files = []
            temp_id = current_id
            max_attempts = 100  # Maximum number of IDs to check
            attempts = 0
            
            # Collect required number of valid files
            while len(valid_files) < count and attempts < max_attempts:
                try:
                    msg = await client.get_messages(client.db_channel.id, temp_id)
                    if msg.video or msg.document:
                        valid_files.append(temp_id)
                    else:
                        skipped_ids.append(temp_id)
                    temp_id += 1
                    attempts += 1
                except Exception as e:
                    logger.error(f"Error fetching message {temp_id}: {e}")
                    skipped_ids.append(temp_id)
                    temp_id += 1
                    attempts += 1
            
            if len(valid_files) < count:
                await message.reply(
                    to_small_caps_with_html(
                        f"<b>❌ Not enough valid media files for {quality}. Required: {count}, Found: {len(valid_files)}.</b>"
                    ),
                    parse_mode=ParseMode.HTML
                )
                return
            
            start_id = valid_files[0]
            end_id = valid_files[-1]
            
            # Check for sticker or GIF
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
                'start': start_id,
                'end': end_id,
                'count': count + additional_count
            }
            
            current_id = end_id + 1
            logger.info(f"Processed {quality}: start={links[quality]['start']}, end={links[quality]['end']}, total files={links[quality]['count']}")
        
        # Inform user about skipped IDs
        if skipped_ids:
            await message.reply(
                to_small_caps_with_html(
                    f"<b>⚠️ Skipped non-media message IDs: {', '.join(map(str, skipped_ids))}</b>"
                ),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[message.from_user.id]['links'] = links
        flink_user_data[message.from_user.id]['awaiting_db_post'] = False
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_db_post_input: {e}")
        await message.reply_text(to_small_caps_with_html(f"<b>❌ Error: {str(e)}</b>\nPlease ensure the input is valid and try again."), parse_mode=ParseMode.HTML)

async def flink_generate_final_output(client: Client, message: Message):
    """Generate the final output for flink with download buttons."""
    logger.info(f"Generating final output for user {message.from_user.id}")
    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error("No links generated in flink_user_data")
            await message.reply_text(to_small_caps_with_html("<b>❌ No links generated. Please check the input and try again.</b>"), parse_mode=ParseMode.HTML)
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
                text=caption if caption else to_small_caps_with_html("<b>Here are your download buttons:</b>"),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(f"Error in flink_generate_final_output: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while generating output. Please try again.</b>"), parse_mode=ParseMode.HTML)

async def create_link(client: Client, link_data: Dict) -> str:
    """Create a Telegram link for a range of message IDs."""
    start_id = link_data['start'] * abs(client.db_channel.id)
    end_id = link_data['end'] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    return f"https://t.me/{client.username}?start={base64_string}"

@Bot.on_callback_query(filters.regex(r"^flink_edit_output$"))
async def flink_edit_output_callback(client: Client, query: CallbackQuery):
    """Handle editing the flink output."""
    logger.info(f"Flink_edit_output callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>Add optional elements to the output:</b>\n\n"
            "Send an image or type a caption separately."
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
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while editing output.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Prompt for adding an image to flink output."""
    logger.info(f"Flink_add_image callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html("<b>Send the image:</b>")
        
        if current_text != new_text:
            await query.message.edit_text(new_text, parse_mode=ParseMode.HTML)
        else:
            logger.info(f"Skipping edit in flink_add_image_callback for user {query.from_user.id} - content unchanged")
        
        await query.answer(to_small_caps_with_html("Send image"))
    except Exception as e:
        logger.error(f"Error in flink_add_image_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while adding image.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.photo & filters.reply)
async def handle_image_input(client: Client, message: Message):
    """Handle image input for flink output."""
    logger.info(f"Image input received from user {message.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>❌ You are not authorized!</b>"), parse_mode=ParseMode.HTML)
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
            await message.reply_text(to_small_caps_with_html("<b>❌ Please reply to the image prompt with a valid image.</b>"), parse_mode=ParseMode.HTML)
            return

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply_text(
            to_small_caps_with_html("<b>✅ Image saved successfully.</b>\nType a caption if needed, or proceed with 'Done'."),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_image_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while processing image.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Prompt for adding a caption to flink output."""
    logger.info(f"Flink_add_caption callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        flink_user_data[user_id]['awaiting_caption'] = True
        caption_prompt_text = (
            to_small_caps_with_html("<b>Type your caption:</b>\n\n") +
            "<blockquote><b>Example:</b></blockquote>\n\n"
            "<blockquote><code>ᴛɪᴛʟᴇ- BLACK CLOVER\n"
            "Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅɪ Dᴜʙʙᴇᴅ\n\n"
            "Qᴜᴀʟɪᴛʏ - 360ᴘ, 720ᴘ, 1080ᴘ\n\n"
            "Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n"
            "Aʟʟ Qᴜᴀʟɪᴛʏ - ( Hɪɴᴅɪ Dᴜʙʙᴇᴅ )\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Cʟɪᴄᴋ Hᴇʀᴇ Tᴏ Dᴏᴡɴʟᴏᴀᴅ | Eᴘ - 01 & S1</code></blockquote>\n\n"
            + to_small_caps_with_html("<b>Reply to this message with your caption.</b>")
        )
        
        caption_prompt_msg = await query.message.reply_text(caption_prompt_text, parse_mode=ParseMode.HTML)
        flink_user_data[user_id]['caption_prompt_message'] = caption_prompt_msg
        
        await query.answer(to_small_caps_with_html("Type caption"))
    except Exception as e:
        logger.error(f"Error in flink_add_caption_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while adding caption.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.reply & ~filters.regex(r"^CANCEL$") & ~filters.forwarded)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for flink output."""
    logger.info(f"Caption input received from user {message.from_user.id}, text: {message.text}")
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>❌ You are not authorized!</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(to_small_caps_with_html("<b>❌ No active caption prompt found. Please use the 'Add Caption' option first.</b>"), parse_mode=ParseMode.HTML)
            return

        caption_prompt_msg = flink_user_data[user_id].get('caption_prompt_message')
        if not caption_prompt_msg or not message.reply_to_message or message.reply_to_message.id != caption_prompt_msg.id:
            logger.info(f"Caption input ignored for user {message.from_user.id} - not a reply to caption prompt")
            await message.reply_text(to_small_caps_with_html("<b>❌ Please reply to the caption prompt message with your caption.</b>"), parse_mode=ParseMode.HTML)
            return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.text
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply_text(to_small_caps_with_html("<b>✅ Caption saved successfully.</b>"), parse_mode=ParseMode.HTML)
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(f"Error in handle_caption_input: {e}")
        await message.reply_text(to_small_caps_with_html("<b>❌ An error occurred while processing caption.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output_callback(client: Client, query: CallbackQuery):
    """Finalize the flink output."""
    logger.info(f"Flink_done_output callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id not in flink_user_data or 'links' not in flink_user_data[user_id]:
            await query.message.edit_text(to_small_caps_with_html("<b>❌ No links found. Please start the process again using /flink.</b>"), parse_mode=ParseMode.HTML)
            return

        await query.message.edit_text(to_small_caps_with_html("<b>✅ Process completed.</b>"), parse_mode=ParseMode.HTML)
        del flink_user_data[user_id]
        await query.answer(to_small_caps_with_html("Done"))
    except Exception as e:
        logger.error(f"Error in flink_done_output_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while finalizing output.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_back_to_menu$"))
async def flink_back_to_menu_callback(client: Client, query: CallbackQuery):
    """Return to the flink main menu."""
    logger.info(f"Flink_back_to_menu callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id in flink_user_data:
            flink_user_data[user_id]['awaiting_format'] = False
            flink_user_data[user_id]['awaiting_db_post'] = False
            flink_user_data[user_id]['awaiting_caption'] = False
        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Back to menu"))
    except Exception as e:
        logger.error(f"Error in flink_back_to_menu_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while returning to menu.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Refresh the flink main menu."""
    logger.info(f"Flink_refresh callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Refreshed"))
    except Exception as e:
        logger.error(f"Error in flink_refresh_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while refreshing menu.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_close$"))
async def flink_close_callback(client: Client, query: CallbackQuery):
    """Close the flink menu."""
    logger.info(f"Flink_close callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id in flink_user_data:
            del flink_user_data[user_id]
        await query.message.delete()
        await query.answer(to_small_caps_with_html("Closed"))
    except Exception as e:
        logger.error(f"Error in flink_close_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while closing menu.</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_cancel_process$"))
async def flink_cancel_process_callback(client: Client, query: CallbackQuery):
    """Cancel the flink process."""
    logger.info(f"Flink_cancel_process callback triggered by user {query.from_user.id}")
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id in flink_user_data:
            flink_user_data[user_id]['awaiting_db_post'] = False
        await query.message.edit_text(to_small_caps_with_html("<b>❌ Process cancelled.</b>"), parse_mode=ParseMode.HTML)
        await show_flink_main_menu(client, query.message)
        await query.answer(to_small_caps_with_html("Cancelled"))
    except Exception as e:
        logger.error(f"Error in flink_cancel_process_callback: {e}")
        await query.message.edit_text(to_small_caps_with_html("<b>❌ An error occurred while cancelling process.</b>"), parse_mode=ParseMode.HTML)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
