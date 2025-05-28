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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from pyrogram.enums import ParseMode
from bot import Bot
from helper_func import encode, get_message_id, admin
import re
import random
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

# Store user data for batch command
batch_user_data = {}

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

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    logger.info(f"Admin check in link_menu for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
    if user_id not in admin_ids and user_id != OWNER_ID:
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
            InlineKeyboardButton("• ᴄᴜsᴛᴏᴍ •", callback_data="link_custom")
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
            chat_id=user_id,
            photo=selected_image,
            caption=menu_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Failed to send link menu with photo for user {user_id}: {e}")
        # Fallback to text-only message
        await client.send_message(
            chat_id=user_id,
            text=menu_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

@Bot.on_callback_query(filters.regex(r"^link_"))
async def link_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for the /link command menu."""
    user_id = callback.from_user.id
    data = callback.data
    logger.info(f"Link callback triggered by user {user_id} with data {data}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    logger.info(f"Admin check in link_callback for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
    if user_id not in admin_ids and user_id != OWNER_ID:
        await callback.answer(to_small_caps_with_html("You are not authorized!"), show_alert=True)
        return

    # Create a new message object with the correct user_id
    message = callback.message
    message.from_user = callback.from_user  # Ensure the message object has the correct user

    if data == "link_batch":
        await batch(client, message)
        await callback.answer(to_small_caps_with_html("Batch link generation started"))
    elif data == "link_genlink":
        await link_generator(client, message)
        await callback.answer(to_small_caps_with_html("Single link generation started"))
    elif data == "link_custom":
        await custom_batch(client, message)
        await callback.answer(to_small_caps_with_html("Custom batch link generation started"))
    elif data == "link_close":
        await callback.message.delete()
        await callback.answer(to_small_caps_with_html("Menu closed"))

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    user_id = message.from_user.id
    logger.info(f"Batch command triggered by user {user_id}")

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    logger.info(f"Admin check in batch for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
    if user_id not in admin_ids and user_id != OWNER_ID:
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        return

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

    # Verify admin access
    admin_ids = await db.get_all_admins() or []
    logger.info(f"Admin check in batch_start_process for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
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
    logger.info(f"Admin check in batch_handle_cancel_close for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
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
    logger.info(f"Admin check in handle_batch_input for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
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
    logger.info(f"Admin check in link_generator for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
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
    logger.info(f"Admin check in custom_batch for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
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

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
