#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#

import asyncio
import random
import logging
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from helper_func import *
from database.database import *
from config import OWNER_ID, RANDOM_IMAGES, START_PIC, START_MESSAGE, BOT_NAME

# Set up logging for this module
logger = logging.getLogger(__name__)

# Define message effect IDs
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"Received /start command from user {user_id} in chat {chat_id}")

    # Add user to database if not already present
    if not await db.present_user(user_id):
        await db.add_user(user_id)

    # Check if force subscription is required
    if not await is_subscribed(client, user_id):
        channels = await db.show_channels()
        settings = await db.get_settings()
        if not settings.get('FORCE_SUB_ENABLED', True) or not channels:
            # If force sub is disabled or no channels, proceed to main menu
            await send_start_message(client, message)
            return

        # Prepare the channel list for force subscription
        text = "<b>⚠️ You need to join the following channel(s) to use this bot:</b>\n\n"
        buttons = []
        for ch_id in channels:
            if await db.get_channel_temp_off(ch_id):
                continue  # Skip channels that are temporarily off
            try:
                chat = await client.get_chat(ch_id)
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code></b></blockquote>\n"
                buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=link)])
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

        buttons.append([InlineKeyboardButton("✅ Check Again", callback_data="check_sub")])

        # Select random image and effect
        selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
        selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
                message_effect_id=selected_effect
            )
            logger.info(f"Sent force-sub message with image {selected_image} and effect {selected_effect} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send photo message: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=selected_effect
            )
            logger.info(f"Sent force-sub text-only message with effect {selected_effect} to user {user_id}")
        return

    # If user is subscribed or force-sub is not required, show the main start message
    await send_start_message(client, message)

async def send_start_message(client: Client, message: Message):
    """Send the main start message with bot details."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "None"

    # Prepare the start message
    start_text = START_MESSAGE.format(
        first_name=first_name,
        username=username,
        bot_name=BOT_NAME,
        pyrogram_version=__version__
    )
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/AnimeLord_Bots"),
                InlineKeyboardButton("🛠 Support", url="https://t.me/AnimeLord_support")
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
                InlineKeyboardButton("🔙 Close", callback_data="close")
            ]
        ]
    )

    # Select random image and effect
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

    try:
        await client.send_photo(
            chat_id=chat_id,
            photo=selected_image,
            caption=start_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            message_effect_id=selected_effect
        )
        logger.info(f"Sent start message with image {selected_image} and effect {selected_effect} to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send start photo message: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=start_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            message_effect_id=selected_effect
        )
        logger.info(f"Sent start text-only message with effect {selected_effect} to user {user_id}")

@Bot.on_callback_query(filters.regex(r"^(check_sub|about|close)$"))
async def start_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for start command."""
    data = callback.data
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    message_id = callback.message.id

    logger.info(f"Received callback query with data: {data} from user {user_id} in chat {chat_id}")

    if data == "check_sub":
        if await is_subscribed(client, user_id):
            await callback.message.delete()
            await send_start_message(client, callback.message)
            await callback.answer("You are now subscribed! Welcome!")
        else:
            channels = await db.show_channels()
            text = "<b>⚠️ You still need to join the following channel(s):</b>\n\n"
            buttons = []
            for ch_id in channels:
                if await db.get_channel_temp_off(ch_id):
                    continue
                try:
                    chat = await client.get_chat(ch_id)
                    link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                    text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code></b></blockquote>\n"
                    buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=link)])
                except Exception as e:
                    logger.error(f"Failed to fetch chat {ch_id}: {e}")
                    text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

            buttons.append([InlineKeyboardButton("✅ Check Again", callback_data="check_sub")])

            try:
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await callback.answer("Please join the required channels!")
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
                await callback.answer("Error updating message. Try again!")

    elif data == "about":
        about_text = (
            f"<b>🤖 Bot Name:</b> {BOT_NAME}\n"
            f"<b>🛠 Creator:</b> <a href='https://t.me/MehediYT69'>MehediYT69</a>\n"
            f"<b>📢 Updates:</b> <a href='https://t.me/AnimeLord_Bots'>AnimeLord_Bots</a>\n"
            f"<b>🛠 Support:</b> <a href='https://t.me/AnimeLord_support'>AnimeLord_support</a>\n"
            f"<b>🔗 Source:</b> <a href='https://github.com/AnimeLord-Bots/FileStore'>GitHub</a>\n"
            f"<b>📜 License:</b> MIT License\n"
            f"<b>🔄 Pyrogram:</b> v{__version__}"
        )
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔙 Back", callback_data="back_to_start"),
                    InlineKeyboardButton("🔙 Close", callback_dataروف

System: "close")
                ]
            ]
        )

        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=about_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("Showing about info!")
        except Exception as e:
            logger.error(f"Failed to edit message with about info: {e}")
            await callback.answer("Error showing about info!")

    elif data == "close":
        await callback.message.delete()
        await callback.answer("Closed!")

    elif data == "back_to_start":
        await callback.message.delete()
        await send_start_message(client, callback.message)
        await callback.answer("Back to start!")

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#
