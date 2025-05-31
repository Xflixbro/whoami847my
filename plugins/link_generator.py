#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, CallbackQuery
from pyrogram.enums import ParseMode
from bot import Bot
from helper_func import encode, decode, get_message_id, admin, to_small_caps_with_html
import re
import logging
import random
from config import OWNER_ID, RANDOM_IMAGES, START_PIC
from database.database import db
from asyncio import TimeoutError
from typing import Dict

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Filter for batch command input
async def batch_state_filter(_, __, message: Message):
    """Filter to ensure messages when awaiting batch input."""
    user_id = message.from_user.id
    state = await db.get_temp_state(user_id)
    is_valid = state in ['awaiting_first_message', 'awaiting_second_message']
    logger.info(f"Checking batch_state_filter for user {user_id}: state={state}, is_valid={is_valid}")
    return is_valid

@Bot.on_message(filters.private & admin & filters.command('link'))
async def link_menu(client: Client, message: Message):
    """Handle /link command to display a menu for link generation options."""
    user_id = message.from_user.id
    try:
        logger.info(f"Link command triggered by user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        logger.info(f"Admin check in link_menu for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        # Prepare the menu text
        menu_text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<blockquote><b>If you want to generate a link for files then use those buttons according to your needs.</b></blockquote>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
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

        # Select random background image
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
            logger.error(f"Failed to send link menu with photo for user {user_id}: {str(e)}")
            # Fallback to text-only message
            await client.send_message(
                chat_id=user_id,
                text=menu_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

    except Exception as e:
        logger.error(f"Error in link_menu for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^link_"))
async def link_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for the /link command menu."""
    user_id = callback.from_user.id
    data = callback.data
    try:
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
            await callback.answer(to_small_caps_with_html("Batch link generation started!"))
        elif data == "link_genlink":
            await link_generator(client, message)
            await callback.answer(to_small_caps_with_html("Single link generation started!"))
        elif data == "link_custom":
            await custom_batch(client, message)
            await callback.answer(to_small_caps_with_html("Custom batch link generation started!"))
        elif data == "link_flink":
            await flink_command(client, message)
            await callback.answer(to_small_caps_with_html("Formatted link generation started!"))
        elif data == "link_close":
            await callback.message.delete()
            await callback.answer(to_small_caps_with_html("Menu closed"))

    except Exception as e:
        logger.error(f"Error in link_callback for user {user_id}: {str(e)}")
        await callback.answer(f"Failed to process callback: {str(e)}", show_alert=True)

@Bot.on_message(filters.private & admin & filters.command('batch'))
async def batch(client: Client, message: Message):
    """Handle /batch command to generate a link for a range of messages."""
    user_id = message.from_user.id
    try:
        logger.info(f"Batch command triggered by user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        logger.info(f"Admin check in batch for user {user_id}: Admins={admin_ids}, OWNER_ID={OWNER_ID}")
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<b>❌ You are not authorized!</b>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                parse_mode=ParseMode.HTML
            )
            return

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

        await message.reply(
            text=text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error in batch for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^batch_"))
async def batch_callback(client: Client, query: CallbackQuery):
    """Handle callback queries for batch command."""
    user_id = query.from_user.id
    action = query.data
    try:
        logger.info(f"Batch callback triggered by user {user_id} with action {action}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        if action == "batch_start_process":
            await db.set_temp_state(user_id, 'awaiting_first_message')
            logger.info(f"Set state to awaiting_first_message for user {user_id}")
            await query.message.edit_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<blockquote><b>Forward the first message from db batch (with quotes).</b></blockquote>\n"
                    "<blockquote><b>Or send the db batch post link directly</b></blockquote>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖️ Cancel", callback_data="batch_cancel")]
                ]),
                parse_mode=ParseMode.HTML
            )
            await query.answer(to_small_caps_with_html("Send the first message or link!"))

        elif action == "batch_cancel":
            await db.set_temp_state(user_id, '')
            await query.message.edit_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process canceled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            await query.answer("Batch process canceled!")

        elif action == "batch_close":
            await db.set_temp_state(user_id, '')
            await query.message.delete()
            await query.answer("Menu closed!")

    except Exception as e:
        logger.error(f"Error in batch_callback for user {user_id}: {str(e)}")
        await query.answer(f"Failed to process action: {str(e)}", show_alert=True)

@Bot.on_message(filters.private & admin & filters.create(batch_state_filter))
async def handle_batch(client: Client, message: Message):
    """Handle batch input based on state."""
    user_id = message.from_user.id
    state = await db.get_temp_state(user_id)
    logger.info(f"Handling batch input for user {user_id}, state: {state}, message_text={message.text}")

    try:
        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        if state == 'awaiting_first_message':
            first_msg_id = await get_message_id(client, message)
            logger.info(f"First message ID for user {user_id}: {first_msg_id}")
            if not first_msg_id:
                logger.error(f"Invalid first message ID for user {user_id}")
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or batch link is invalid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            await db.set_temp_data(user_id, 'first_message_id', first_msg_id)
            await db.set_temp_state(user_id, 'awaiting_second_message')
            logger.info(f"Set state to awaiting_second_message for user {user_id}")
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward the last message from db batch (with quotes).</b></blockquote>\n<blockquote><b>Or send the db batch post link directly</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )

        elif state == 'awaiting_second_message':
            second_msg_id = await get_message_id(client, message)
            logger.info(f"Second message ID for user {user_id}: {second_msg_id}")
            if not second_msg_id:
                logger.error(f"Invalid second message ID for user {user_id}")
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or batch link is invalid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            first_msg_id = await db.get_temp_data(user_id, 'first_message_id')
            if first_msg_id > second_msg_id:
                logger.error(f"First message ID {first_msg_id} is greater than second message ID {second_msg_id} for user {user_id}")
                await message.reply(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: First message ID cannot be greater than second message ID.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                return

            # Generate batch link
            string = f"get-{first_msg_id * abs(client.db_channel.id)}-{second_msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://t.me/share/url?url={link}')]])

            await message.reply_text(
                to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                quote=True,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            await db.set_temp_state(user_id, '')  # Reset state
            await db.set_temp_data(user_id, 'first_message_id', None)  # Clear temp data

    except Exception as e:
        logger.error(f"Error in handle_batch for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(user_id, '')  # Reset state

@Bot.on_message(filters.private & admin & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    """Handle /genlink command to generate a link for a single message."""
    user_id = message.from_user.id
    try:
        logger.info(f"Genlink command triggered by user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        while True:
            try:
                channel_message = await client.ask(
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Forward a message from the db channel (with quotes).</b></blockquote>\n<blockquote><b>Or send the db channel post link directly</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    chat_id=user_id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                logger.error(f"Timeout error while waiting for message in genlink for user {user_id}")
                await message.reply_text(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Timeout: No response received.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    parse_mode=ParseMode.HTML
                )
                return
            msg_id = await get_message_id(client, channel_message)
            if msg_id:
                break
            else:
                await channel_message.reply_text(
                    to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or the link is invalid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    quote=True,
                    parse_mode=ParseMode.HTML
                )
                continue

        base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://t.me/share/url?url={link}')]])

        await channel_message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your generated link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            quote=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error in link_generator for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & admin & filters.command("custom_batch"))
async def custom_batch(client: Client, message: Message):
    """Handle /custom_batch command to collect and generate a batch link."""
    user_id = message.from_user.id
    try:
        logger.info(f"Custom batch command triggered by user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        collected = []
        STOP_KEYBOARD = ReplyKeyboardMarkup([["Stop"]], resize_keyboard=True)

        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Send all messages you want to include in the batch.</b></blockquote>\n<blockquote><b>Press Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            reply_markup=STOP_KEYBOARD,
            parse_mode=ParseMode.HTML
        )

        while True:
            try:
                user_msg = await client.ask(
                    chat_id=user_id,
                    text=to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Waiting for messages...</b></blockquote>\n<blockquote><b>Press Stop to finish.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    timeout=60,
                    parse_mode=ParseMode.HTML
                )
            except TimeoutError:
                logger.error(f"Timeout error waiting for message in custom_batch for user {user_id}")
                break

            if user_msg.text and user_msg.text.strip().lower() == "stop":
                break

            try:
                sent = await user_msg.copy(client.db_channel.id, disable_notification=True)
                collected.append(sent.id)
            except Exception as e:
                await message.reply_text(
                    to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Failed to store message:</b> {str(e)}</blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                    parse_mode=ParseMode.HTML
                )
                logger.error(f"Error storing message in custom_batch for user {user_id}: {str(e)}")
                continue

        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Batch collection completed.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML
        )

        if not collected:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No messages were added to the batch.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        start_id = collected[0] * abs(client.db_channel.id)
        end_id = collected[-1] * abs(client.db_channel.id)
        string = f"get-{start_id}-{end_id}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://t.me/share/url?url={link}')]])

        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your custom batch link:</b></blockquote>\n\n{link}\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error in custom_batch for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.private & admin & filters.command('flink'))
async def flink_command(client: Client, message: Message):
    """Handle /flink command for formatted link generation."""
    user_id = message.from_user.id
    try:
        logger.info(f"Flink command triggered by user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        await db.set_temp_state(user_id, '')
        await show_flink_main_menu(client, message)

    except Exception as e:
        logger.error(f"Error in flink_command for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred. Please try again.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

async def show_flink_main_menu(client: Client, message: Message, edit: bool = False):
    """Show the main menu for the flink command."""
    user_id = message.from_user.id
    try:
        current_format = await db.get_temp_data(user_id, 'flink_format') or "Not set yet"
        text = to_small_caps_with_html(
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b>Formatted Batch Link Generator</b>\n\n"
            "<blockquote><b>Current format:</b></blockquote>\n\n"
            f"<blockquote><code>{current_format}</code></blockquote>\n\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
        )

        buttons = [
            [
                InlineKeyboardButton("• Set Format •", callback_data="flink_set_format"),
                InlineKeyboardButton("• Start Process •", callback_data="flink_start_process")
            ],
            [
                InlineKeyboardButton("• Refresh •", callback_data="flink_refresh"),
                InlineKeyboardButton("• Close •", callback_data="flink_close")
            ]
        ]

        if edit:
            await message.edit_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply(
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logger.error(f"Error in show_flink_main_menu for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while showing the menu.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )

@Bot.on_callback_query(filters.regex(r"^flink_"))
async def flink_callback(client: Client, query: CallbackQuery):
    """Handle callback queries for flink command."""
    user_id = query.from_user.id
    action = query.data
    try:
        logger.info(f"Flink callback triggered by user {user_id} with action {action}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await query.answer("You are not authorized!", show_alert=True)
            return

        if action == "flink_set_format":
            await db.set_temp_state(user_id, 'awaiting_flink_format')
            logger.info(f"Set state to awaiting_flink_format for user {user_id}")
            await query.message.edit_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<b>Please send your batch format in this pattern:</b>\n\n"
                    "<blockquote><b>Example:</b></blockquote>\n"
                    "<blockquote><code>360p=2,720p=3,1080p=2,4k=1,HDR=1</code></blockquote>\n\n"
                    "<blockquote><b>Meaning:</b></blockquote>\n"
                    "<blockquote>- 360p=2 → 2 video files for 360p quality</blockquote>\n"
                    "<blockquote>- If stickers/gifs are present, they will be included in the link</blockquote>\n"
                    "<blockquote>- Only these qualities will be created</blockquote>\n\n"
                    "<blockquote><b>Send the format in the next message (no need to reply).</b></blockquote>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="flink_back_to_menu")]
                ]),
                parse_mode=ParseMode.HTML
            )
            await query.answer("Enter the format")

        elif action == "flink_start_process":
            format_text = await db.get_temp_data(user_id, 'flink_format')
            if not format_text:
                await query.answer("Please set a format first!", show_alert=True)
                return
            await db.set_temp_state(user_id, 'awaiting_flink_message')
            await query.message.edit_text(
                to_small_caps_with_html(
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                    "<blockquote><b>Forward the first message from db batch (with quotes).</b></blockquote>\n"
                    "<blockquote><b>Or send the db batch post link directly</b></blockquote>\n"
                    "<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✖️ Cancel", callback_data="flink_cancel")]
                ]),
                parse_mode=ParseMode.HTML
            )
            await query.answer("Send the first message or link!")

        elif action == "flink_back_to_menu":
            await db.set_temp_state(user_id, '')
            await show_flink_main_menu(client, query.message, edit=True)
            await query.answer("Back to menu!")

        elif action == "flink_refresh":
            await show_flink_main_menu(client, query.message, edit=True)
            await query.answer("Menu refreshed!")

        elif action == "flink_close":
            await db.set_temp_state(user_id, '')
            await query.message.delete()
            await query.answer("Menu closed!")

        elif action == "flink_cancel":
            await db.set_temp_state(user_id, '')
            await query.message.edit_text(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Process canceled.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            await query.answer("Process canceled!")

    except Exception as e:
        logger.error(f"Error in flink_callback for user {user_id}: {str(e)}")
        await query.answer(f"Failed to process action: {str(e)}", show_alert=True)

@Bot.on_message(filters.private & admin & filters.text & filters.regex(r"^[a-zA-Z0-9_]+\s*=\s*\d+(,\s*[a-zA-Z0-9_]+\s*=\s*\d+)*$") & filters.create(lambda _, __, m: asyncio.run_coroutine_threadsafe(db.get_temp_state(m.from_user.id), asyncio.get_event_loop()).result() == 'awaiting_flink_format'))
async def handle_format_input(client: Client, message: Message):
    """Handle format input for flink command."""
    user_id = message.from_user.id
    try:
        logger.info(f"Format input received from user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        format_text = message.text.strip()
        await db.set_temp_data(user_id, 'flink_format', format_text)
        await db.set_temp_state(user_id, '')
        logger.info(f"Saved format {format_text} for user {user_id}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>✅ Format saved successfully:</b></blockquote>\n\n<code>{format_text}</code>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await show_flink_main_menu(client, message)

    except Exception as e:
        logger.error(f"Error in handle_format_input for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ An error occurred while processing format.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(user_id, '')

@Bot.on_message(filters.private & admin & filters.create(lambda _, __, m: asyncio.run_coroutine_threadsafe(db.get_temp_state(m.from_user.id), asyncio.get_event_loop()).result() == 'awaiting_flink_message'))
async def handle_flink_message(client: Client, message: Message):
    """Handle message input for flink command."""
    user_id = message.from_user.id
    try:
        logger.info(f"Flink message input received from user {user_id}")

        # Verify admin access
        admin_ids = await db.get_all_admins() or []
        if user_id not in admin_ids and user_id != OWNER_ID:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ You are not authorized!</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            return

        msg_id = await get_message_id(client, message)
        if not msg_id:
            logger.error(f"Invalid message ID for user {user_id}")
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>❌ Error: This forwarded post is not from my db channel or the link is invalid.</b></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                quote=True,
                parse_mode=ParseMode.HTML
            )
            return

        format_text = await db.get_temp_data(user_id, 'flink_format')
        if not format_text:
            await message.reply(
                to_small_caps_with_html("<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ No format set. Please set a format first.</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
                parse_mode=ParseMode.HTML
            )
            await db.set_temp_state(user_id, '')
            await show_flink_main_menu(client, message)
            return

        # Parse format
        format_dict = {}
        for item in format_text.split(','):
            key, value = item.split('=')
            format_dict[key.strip()] = int(value.strip())

        # Calculate total messages needed
        total_messages = sum(format_dict.values())
        start_id = msg_id * abs(client.db_channel.id)
        end_id = (msg_id + total_messages - 1) * abs(client.db_channel.id)

        # Generate formatted link
        string = f"get-{start_id}-{end_id}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://t.me/share/url?url={link}')]])

        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<blockquote><b>Here is your formatted batch link:</b></blockquote>\n\n{link}\n\n<blockquote><b>Format used:</b> <code>{format_text}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            quote=True,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(user_id, '')
        await show_flink_main_menu(client, message)

    except Exception as e:
        logger.error(f"Error in handle_flink_message for user {user_id}: {str(e)}")
        await message.reply_text(
            to_small_caps_with_html(f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n<b>❌ Error: {str(e)}</b>\n<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"),
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(user_id, '')
        await show_flink_main_menu(client, message)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see <https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
