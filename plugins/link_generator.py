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
from config import OWNER_ID, RANDOM_IMAGES, START_PIC, MESSAGE_EFFECT_IDS
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

# Function to show link generator settings with buttons
async def show_link_settings(client: Client, chat_id: int, message_id: int = None):
    """Show the link generator menu with buttons and random image."""
    settings_text = to_small_caps_with_html(
        "<b>━━━━━━━━━━━━━━━━━━</b>\n"
        "<blockquote><b>Iꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ ꜰᴏʀ ꜰɪʟᴇꜱ ᴛʜᴇɴ ᴜꜱᴇ ᴛʜᴏꜱᴇ ʙᴜᴛᴛᴏɴꜱ ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ʏᴏᴜʀ ɴᴇᴇᴅ.</b></blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━━</b>"
    )

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ʙᴀᴛᴄʜ", callback_data="link_batch"),
                InlineKeyboardButton("ɢᴇɴʟɪɴᴋ", callback_data="link_genlink")
            ],
            [
                InlineKeyboardButton("ᴄᴜsᴛᴏᴍ", callback_data="link_custom"),
                InlineKeyboardButton("ꜰʟɪɴᴋ", callback_data="link_flink")
            ],
            [
                InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="link_close")
            ]
        ]
    )

    # Select random image and effect
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

    if message_id:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Failed to edit link settings message: {e}")
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
        except Exception as e:
            logger.error(f"Failed to send link settings with photo: {e}")
            # Fallback to text-only message
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=selected_effect
            )

# Command to show link settings
@Bot.on_message(filters.command('link') & filters.private & admin)
async def link_settings(client: Client, message: Message):
    """Handle /link command to show link generator menu."""
    logger.info(f"Link command triggered by user {message.from_user.id}")
    await show_link_settings(client, message.chat.id)

# Callback handler for link settings buttons
@Bot.on_callback_query(filters.regex(r"^link_"))
async def link_callback(client: Client, callback: CallbackQuery):
    """Handle callbacks for link settings buttons."""
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id
    user_id = callback.from_user.id
    logger.info(f"Link callback {data} triggered by user {user_id}")

    admin_ids = await db.get_all_admins() or []
    if user_id not in admin_ids and user_id != OWNER_ID:
        await callback.answer(to_small_caps_with_html("Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ!"), show_alert=True)
        return

    try:
        if data == "link_batch":
            # Simulate /batch command
            await batch(client, callback.message)
            await callback.answer(to_small_caps_with_html("Sᴛᴀʀᴛɪɴɢ ʙᴀᴛᴄʜ ᴘʀᴏᴄᴇss"))

        elif data == "link_genlink":
            # Simulate /genlink command
            await link_generator(client, callback.message)
            await callback.answer(to_small_caps_with_html("Sᴛᴀʀᴛɪɴɢ ɢᴇɴʟɪɴᴋ ᴘʀᴏᴄᴇss"))

        elif data == "link_custom":
            # Simulate /custom_batch command
            await custom_batch(client, callback.message)
            await callback.answer(to_small_caps_with_html("Sᴛᴀʀᴛɪɴɢ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ᴘʀᴏᴄᴇss"))

        elif data == "link_flink":
            # Simulate /flink command
            await flink_command(client, callback.message)
            await callback.answer(to_small_caps_with_html("Sᴛᴀʀᴛɪɴɢ ꜰʟɪɴᴋ ᴘʀᴏᴄᴇss"))

        elif data == "link_close":
            await callback.message.delete()
            await callback.answer(to_small_caps_with_html("Mᴇɴᴜ ᴄʟᴏsᴇᴅ"))

    except Exception as e:
        logger.error(f"Error in link callback {data} for user {user_id}: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Eʀʀᴏʀ: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

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
        logger.error(to_small_caps_with_html(f"Timeout error waiting for batch input in state {state} for user {chat_id}"))
        await message.reply(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in handle_batch_input for user {chat_id}: {e}"))
        await message.reply(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        if chat_id in batch_user_data:
            del batch_user_data[chat_id]

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    while True:
        try:
            channel_message = await client.ask(
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward message from the db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error(to_small_caps_with_html(f"Timeout error waiting for message in genlink command"))
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
                chat_id=message.chat.id,
                text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for files/messages...</b></blockquote>\n<blockquote><b>Press Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
                timeout=60,
                parse_mode=ParseMode.HTML
            )
        except TimeoutError:
            logger.error(to_small_caps_with_html(f"Timeout error waiting for message in custom_batch command"))
            break

        if user_msg.text and user_msg.text.strip().lower() == "stop":
            break

        try:
            sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
            collected.append(sent.id)
        except Exception as e:
            await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store a message:</b></blockquote>\n<code>{e}</code>\n<b>━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            logger.error(to_small_caps_with_html(f"Error storing message in custom_batch: {e}"))
            continue

    await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection complete.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━</b>"), reply_markup=ReplyKeyboardRemove())

    if not collected:
        await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌️ No messages were added to batch.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        return

    start_id = collected[0] * abs(client.db_channel.id)
    end_id = collected[-1] * abs(client.db_channel.id)
    string = f"get-{start_id}-{end_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await message.reply(
        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.private & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    logger.info(to_small_caps_with_html(f"Flink command triggered by user {message.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌️ You are unauthorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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
        logger.error(to_small_caps_with_html(f"Error in flink_command: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    """Show the main menu for the flink command."""
    try:
        current_format = flink_user_data[message.from_user.id]['format'] or "Notable"
        text = to_small_caps_with_html(
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>Formatted Link Generator</b>\n\n"
            f"<blockquote><b>Current format:</b></blockquote>\n"
            f"<blockquote><code>{current_format}</code></blockquote>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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
                logger.info(to_small_caps_with_html(f"Skipping edit in show_flink_main_menu for user {message.from_user.id} - content unchanged"))
        else:
            msg = await message.reply(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            flink_user_data[message.from_user.id]['menu_message'] = msg
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in show_flink_main_menu: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing menu.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_set_format$"))
async def flink_set_format_callback(client: Client, query: CallbackQuery):
    """Handle callback for setting format in flink command."""
    logger.info(to_small_caps_with_html(f"Flink_set_format callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        flink_user_data[query.from_user.id]['awaiting_format'] = True
        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>Please send your format in this pattern:</b></blockquote>\n\n"
            "<blockquote>Example</blockquote>:\n\n"
            "<blockquote>don't copy this. please type</blockquote>:\n"
            "<blockquote><code>360p = 2, 720p = 2, 1080p = 2, 4k = 2, HDRIP = 2</code></blockquote>\n\n"
            "<blockquote><b>Meaning:</b></blockquote>\n"
            "<b>- 360p = 2 → 2 video files for 360p quality</b>\n"
            "<blockquote><b>- If stickers/gifs follow, they will be included in the link\n"
            "- Only these qualities will be created</b></blockquote>\n\n"
            "<b>Send the format in the next message (no need to reply).</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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
            logger.info(to_small_caps_with_html(f"Skipping edit in flink_set_format_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Enter format"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_set_format_callback: {e}"))
        await query.message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\b>❌ An error occurred while setting format.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.regex(r"^[a-zA-Z0-9]+\s*=\s*\d+(,\s*[a-zA-Z0-9]+\s*=\s*\d+)*$"))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink command."""
    logger.info(to_small_caps_with_html(f"Format input received from user {message.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n\b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id in flink_user_data and flink_user_data[user_id].get('awaiting_format'):
            format_text = message.text.strip()
            flink_user_data[user_id]['format'] = format_text
            flink_user_data[user_id]['awaiting_format'] = False
            await message.reply_text(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>✅ Format saved successfully:</b></blockquote>\n\n<code>{format_text}</code>\n\n<b>━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            await show_flink_main_menu(client, message)
        else:
            logger.info(to_small_caps_with_html(f"Format input ignored for user {user_id} - not awaiting format"))
            await message.reply_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    "<blockquote><b>❌ Please use the 'Set Format' option first and provide a valid format</b></blockquote>\n\n"
                    "<blockquote>Example:</blockquote> <code>360p = 2, 720p = 1</code>\n\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML

            )
        
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in handle_format_input: {e}"))        
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while processing format.</b>\n\n<b>━━━━━━━━━━━━━━━━</b>"), 
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_start_process$"))
async def flink_start_process_callback(client: Client, query: CallbackQuery):
    """Handle callback for starting the flink process."""
    logger.info(to_small_caps_with_html(f"Flink_start_process callback triggered by user {query.from_user.id}"))
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
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<blockquote><b>Send the first post link from db channel:</b></blockquote>\n\n"
            "<blockquote><b>Forward a message from the db channel or send its direct link (e.g., <code>t.me/channel/123</code>).</blockquote>\n\n"
            "<blockquote><b>Ensure files are in sequence without gaps.</b></blockquote>\n\n"
            "<b>Send the link or forwarded message in the next message (no need to reply).</b>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
 )
        
        if current_text != new_text:
            await query.message.edit_text(
                text=text_new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖️ Cancel", callback_data="flink_cancel_process")]
                ]),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.info(to_small_caps_with_html(f"Skipping edit in flink_start_process_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Send db channel post"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"error in flink_start_process_callback: {e}"))
        await query.message.edit_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while starting process.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), 
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & (filters.forwarded | filters.regex(r"^https?://t\.me/.*$")))
async def handle_db_post(client: Client, message: Message):
    """Handle db channel post input for flink command."""
    logger.info(to_small_caps_with_html(f"DB post input received from user {message.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids or message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ You are not authorized!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_db_post'):
            logger.info(to_small_caps_with_html(f"DB post input ignored for user {user_id} - not awaiting db channel input"))
            await message.reply_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                    "<blockquote><b>❌ Please use the 'Start Process' option first and provide a valid forwarded message or link from the db channel.</b></blockquote>\n\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            return

        msg_id = await get_message_id(client, message)
        if not msg_id:
            await message.reply(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>❌ Invalid db channel post! Ensure it's a valid forwarded message or link from the db channel.</b></blockquote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return
                
        format_str = flink_user_data[message.from_user.id]['format']
        format_parts = [part.strip() for part in format_str.split(",")]
        
        current_id = msg_id
        links = {}
        
        for part in format_parts:
            match = re.match(r"([a-zA-Z0-9]+)\s*=\s*(\d+)", part)
            if not match:
                await message.reply(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Invalid format part:</b> <code>{part}</code>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
                return
            quality, count = match.groups()
            quality = quality.strip().upper()
            count = int(count.strip())
            
            valid_ids = []
            missing_files = []
            temp_id = current_id
            
            # Collect valid message IDs, skipping missing ones
            while len(valid_ids) < count and temp_id <= current_id + count * 2:  # Limit search to avoid infinite loops
                try:
                    msg = await client.get_messages(client.db_channel.id, temp_id)
                    if msg.video or msg.document:
                        valid_ids.append(temp_id)
                    else:
                        missing_files.append(temp_id)
                except Exception as e:
                    logger.info(to_small_caps_with_html(f"Message {temp_id} not found or invalid: {e}"))
                    missing_files.append(temp_id)
                temp_id += 1
            
            if len(valid_ids) < count:
                logger.error(to_small_caps_with_html(f"Not enough valid media files for {quality}: found {len(valid_ids)}, required {count}"))
                await message.reply(
                    to_small_caps_with_html(
                        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                        f"<blockquote><b>❌ Not enough valid media files for {quality}. Found {len(valid_ids)} files, but {count} required.</b></blockquote>\n\n"
                        f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                    ),
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
                logger.info(to_small_caps_with_html(f"No additional sticker/gif found at id {next_id}: {e}"))
            
            links[quality] = {
                'start': start_id,
                'end': end_id,
                'count': count + additional_count
            }
            
            current_id = end_id + 1
            if missing_files:
                logger.info(to_small_caps_with_html(f"Skipped missing files for {quality}: {missing_files}"))
            
            logger.info(to_small_caps_with_html(f"Processed {quality}: start={links[quality]['start']}, end={links[quality]['end']}, total files={links[quality]['count']}"))
        
        flink_user_data[message.from_user.id]['links'] = links
        flink_user_data[message.from_user.id]['awaiting_db_post'] = False
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in handle_db_post_input: {e}"))
        await message.reply_text(to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Error: {str(e)}</b>\n\nPlease ensure the input is valid and try again.\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def flink_generate_final_output(client: Client, message: Message):
    """Generate the final output for flink command with download buttons."""
    logger.info(to_small_caps_with_html(f"Generating final output for user {message.from_user.id}"))
    try:
        user_id = message.from_user.id
        links = flink_user_data[user_id]['links']
        if not links:
            logger.error(to_small_caps_with_html("No links generated in flink_user_data"))
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ No links generated. Please check the input and try again.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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
                text=caption if caption else to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</blockquote><b>Here are your download buttons:</b></blockquote>\n\n<b>━━━━━━━━━━━━━━━━</b>"),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        
        flink_user_data[user_id]['output_message'] = output_msg
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_generate_final_output: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while generating output. Please try again.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

async def create_link(client: Client, link_data: Dict) -> str:
    """Create a Telegram link for a range of message IDs."""
    start_id = link_data['start'] * abs(client.db_channel.id)
    end_id = link_data['end'] * abs(client.db_channel.id)
    string = f"{get--{start_id}--{end_id}"
    base64_string = await encode(string)
    return f"https://t.me/{client.username}/?start={base64_string}"

@Bot.on_callback_query(filters.regex(r"^flink_edit_output$"))
async def flink_edit_output_callback(client: Client, query: CallbackQuery):
    """Handle callback for editing flink output."""
    logger.info(to_small_caps_with_html(f"Flink_edit_output callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<b>Add optional elements to the output:</b>\n\n"
            "Send an image or type a caption separately.\n\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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
            logger.info(to_small_caps_with_html(f"Skipping edit in flink_edit_output_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer()
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_edit_output_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while editing output.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_image$"))
async def flink_add_image_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding an image to flink output."""
    logger.info(to_small_caps_with_html(f"Flink_add_image callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        current_text = query.message.text if query.message.text else ""
        new_text = to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>Send the image:</b></blockquote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>")
        
        if current_text != new_text:
            await query.message.edit_text(new_text, parse_mode=ParseMode.HTML)
        else:
            logger.info(to_small_caps_with_html(f"Skipping edit in flink_add_image_callback for user {query.from_user.id} - content unchanged"))
        
        await query.answer(to_small_caps_with_html("Send image"))
    except Exception accusing e:
        logger.error(to_small_caps_with_html(f"Error in flink_add_image_callback: {e}"))
        await query.message.edit_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            "<blockquote>\n</b>❌ An error occurred while adding image.</b>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), 
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & filters.photo & filters.reply)
async def handle_image_input(client: Client, message: Message):
    """Handle image input for flink output."""
    logger.info(to_small_caps_with_html(f"Image input received from user {message.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ You are not authorized!</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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

        if not (message.reply_to_message and to_small_caps_with_html("send the image"): in message.reply_to_message.text.lower()):
            logger.info(to_small_caps_with_html(f"Image input ignored for user {user_id} - not a reply to image prompt"))
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Please reply to the image prompt with a valid image.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        flink_user_data[user_id]['edit_data']['image'] = message.photo.file_id
        await message.reply_text(
            to_small_caps_with_html(
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                "<blockquote><b>✅ Image saved successfully.</b></blockquote>\n\n"
                "<blockquote><b>Type a caption if needed, or proceed with 'Done'.</b></blockquote>\n\n"
                "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ),
            parse_mode=ParseMode.HTML
        )
        await flink_generate_final_output(client, message)
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in handle_image_input: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while processing image.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_add_caption$"))
async def flink_add_caption_callback(client: Client, query: CallbackQuery):
    """Handle callback for adding a caption to flink output."""
    logger.info(to_small_caps_with_html(f"Flink_add_caption callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        flink_user_data[user_id]['awaiting_caption'] = True
        caption_prompt_text = (
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>Type your caption:</b></blockquote>\n\n") +
            "<blockquote><b>Example:</b></blockquote>\n\n" +
            "<blockquote><code>ᴛɪᴛʟᴇ- BLACK CLOVER\n" +
            "Aᴜᴅɪᴏ TʀᴀᴄK- Hɪɴᴅɪ Dᴜʙʙᴇᴅ\n\n" +
            "Qᴜᴀʟɪᴛʏ - 360ᴘ, 720ᴘ, 1080ᴘ\n\n" +
            "Eᴘɪsᴏᴅᴇ - 01 & S1 Uᴘʟᴏᴀᴅᴇᴅ\n\n" +
            "Aʟʟ Qᴜᴀʟɪᴛʏ - ( Hɪɴᴅɪ Dᴜʙʙᴇᴅ )\n" +
            "━━━━━━━━━━━━━━━━━━━\n" +
            "Cʟɪᴄ Kʜᴇʀᴇ Tᴏ Dᴏᴡɴʟᴏᴀᴅ | Eᴘ - 01 & S1</code></blockquote>\n\n" +
            to_small_caps_with_html("<blockquote><b>Reply to this message with your caption.</b></blockquote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>")
        )
        
        caption_prompt_msg = await query.message.reply_text(caption_prompt_text, parse_mode=ParseMode.HTML)
        flink_user_data[user_id]['caption_prompt_message'] = caption_prompt_msg
        
        await query.answer(to_small_caps_with_html("Type caption"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_add_caption_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while adding caption.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_message(filters.private & filters.text & filters.reply & ~filters.regex(r"^CANCEL$") & ~filters.forwarded)
async def handle_caption_input(client: Client, message: Message):
    """Handle caption input for flink command."""
    logger.info(to_small_caps_with_html(f"Caption input received from user {message.from_user.id}, text: {message.text}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if message.from_user.id not in admin_ids and message.from_user.id != OWNER_ID:
            continue
        return

        user_id = message.from_user.id
        if user_id not in flink_user_data or not flink_user_data[user_id].get('awaiting_caption'):
            await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ No active caption prompt found. Please use the 'Add Caption' option first.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
            return

        caption_prompt_msg = flink_user_data[user_id].get('caption_prompt_message')
        if not caption_prompt_msg or not message.reply_to_message or message.reply_to_message.id != caption_prompt_msg.message_id:
            logger.info(to_small_caps_with_html(f"Caption input ignored for user {message.from_user.id} - not a reply to caption prompt"))
            continue
        return

        if 'edit_data' not in flink_user_data[user_id]:
            flink_user_data[user_id]['edit_data'] = {}
        flink_user_data[user_id]['edit_data']['caption'] = message.txt
        flink_user_data[user_id]['awaiting_caption'] = False
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<blockquote><b>✅ Caption saved successfully.</b></blockquote>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
        await flink_generate_final_output(client, message)
        
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in handle_caption_input: {e}"))
        await message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while processing caption.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_done_output$"))
async def flink_done_output_callback(client: Client, query: CallbackQuery):
    """Handle callback for finalizing flink output."""
    logger.info(to_small_caps_with_html(f"Flink_done_output callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            await query.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
            return

        user_id = query.from_user.id
        if user_id not in flink_user_data or 'links' not in flink_user_data[user_id]:
            await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n</blockquote><b>❌ No links found. Please start the process again using /flink.</b></center>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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
        logger.error(to_small_caps_with_html(f"Error in flink_done_output_callback: {e}"))
        await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while completing process.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_refresh$"))
async def flink_refresh_callback(client: Client, query: CallbackQuery):
    """Handle callback to refresh flink menu."""
    logger.info(to_small_caps_with_html(f"Flink_refresh callback triggered by user {query.from_user.id}"))
    try:
        admin_ids = await db.get_all_admins() or []
        if query.from_user.id not in admin_ids and query.from_user.id != OWNER_ID:
            continue
        await show_flink_main_menu(client, query.message, edit=True)
        await query.answer(to_small_caps_with_html("Format status refreshed"))
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_refresh_callback: {e}"))
        await query.message.reply_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ An error occurred while refreshing status.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)

@Bot.on_callback_query(filters.regex(r"^flink_(back_to_menu|cancel_process|back_to_output|close)$"))
async def flink_handle_callback_buttons(client: Client, query: CallbackQuery):
    """Handle callback for back, cancel, and closed actions for flink command."""
    logger.info(to_small_caps_with_html(f"Flink callback action {query.data} triggered by user {query.from_user.id}"))
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
            await query.message.edit_text(to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n<b>❌ Process cancelled.</b>\n\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"), parse_mode=ParseMode.HTML)
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
        )
    except Exception as e:
        logger.error(to_small_caps_with_html(f"Error in flink_handle_back_buttons: {e}"))
        await query.message.edit_text(
            to_small_caps_with_html(
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
                f"<b>❌ An error occurred while processing action.</b>\n\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            ), 
            parse_mode=ParseMode.HTML
        )

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of the < https://github.com/AnimeLord-Bots > /FileStore > project,
#
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/blob/master/LICENSE.txt>
#
# All rights reserved.
#
