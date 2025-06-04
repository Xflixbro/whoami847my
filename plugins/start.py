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
import os
import random
import time
import logging
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from helper_func import *
from database.database import db
from database.db_premium import is_premium_user

logger = logging.getLogger(__name__)

MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

@Bot.on_message(filters.command('start') & filters.private & ~filters.forwarded)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    logger.info(f"Received /start command from user {user_id} in chat {chat_id}")

    # Check if user is banned
    if await db.ban_user_exist(user_id):
        logger.info(f"User {user_id} is banned, ignoring /start")
        await message.reply("<b>❌ You are banned from using this bot.</b>")
        return

    # Add user to database if not present
    if not await db.present_user(user_id):
        await db.add_user(user_id)
        logger.info(f"Added new user {user_id} to database")

    # Check if user is premium or owner for force-sub bypass
    if user_id == OWNER_ID or await is_premium_user(user_id):
        logger.debug(f"User {user_id} is Owner or Premium, bypassing force-sub")
        start_text = (
            f"<b>Hello {message.from_user.mention}!</b>\n\n"
            f"<b>I am {client.me.first_name}, a file-sharing bot.</b>\n"
            "<i>Send me any file, and I will provide you with a shareable link.</i>\n\n"
            "<b>Premium User:</b> You have full access to all features! 🎉"
        )
        selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
        selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

        try:
            await message.reply_photo(
                photo=selected_image,
                caption=start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                    [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
                ]),
                message_effect_id=selected_effect
            )
            logger.info(f"Sent start message with photo to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send photo start message to user {user_id}: {e}")
            await message.reply_text(
                text=start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                    [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
                ])
            )
            logger.info(f"Sent text-only start message to user {user_id} as fallback")
        return

    # Check force-subscription
    if not await subscribed(client, user_id):
        channels = await db.show_channels()
        buttons = []
        settings_text = "<b>❌ You need to join the following channel(s) to use this bot:</b>\n\n"

        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                if mode == "on":
                    link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                    settings_text += f"<blockquote><b>› <a href='{link}'>{chat.title}</a></b></blockquote>\n"
                    buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=link)])
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id} for force-sub: {e}")
                settings_text += f"<blockquote><b>› Channel ID: <code>{ch_id}</code> (Unavailable)</b></blockquote>\n"

        buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_fsub")])

        try:
            await message.reply_text(
                text=settings_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
            logger.info(f"Sent force-sub prompt to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send force-sub prompt to user {user_id}: {e}")
            await message.reply_text(
                text="<b>❌ Please join the required channels and try again.</b>",
                parse_mode=ParseMode.HTML
            )
        return

    # Send start message for subscribed users
    start_text = (
        f"<b>Hello {message.from_user.mention}!</b>\n\n"
        f"<b>I am {client.me.first_name}, a file-sharing bot.</b>\n"
        "<i>Send me any file, and I will provide you with a shareable link.</i>\n\n"
        "<b>Enjoy using the bot!</b> 😊"
    )
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

    try:
        await message.reply_photo(
            photo=selected_image,
            caption=start_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
            ]),
            message_effect_id=selected_effect
        )
        logger.info(f"Sent start message with photo to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send photo start message to user {user_id}: {e}")
        await message.reply_text(
            text=start_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
            ])
        )
        logger.info(f"Sent text-only start message to user {user_id} as fallback")

@Bot.on_callback_query(filters.regex(r"^check_fsub"))
async def check_fsub_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    logger.info(f"Received check_fsub callback from user {user_id}")

    if await subscribed(client, user_id):
        start_text = (
            f"<b>Hello {callback.from_user.mention}!</b>\n\n"
            f"<b>I am {client.me.first_name}, a file-sharing bot.</b>\n"
            "<i>Send me any file, and I will provide you with a shareable link.</i>\n\n"
            "<b>Enjoy using the bot!</b> 😊"
        )
        try:
            await callback.message.edit_text(
                text=start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                    [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
                ])
            )
            logger.info(f"User {user_id} passed force-sub check, sent start message")
        except Exception as e:
            logger.error(f"Failed to edit message for user {user_id}: {e}")
            await callback.message.reply_text(
                text=start_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Support", url=SUPPORT_LINK)],
                    [InlineKeyboardButton("Channel", url=CHANNEL_LINK)]
                ])
            )
        await callback.answer("Welcome! You can now use the bot.")
    else:
        channels = await db.show_channels()
        buttons = []
        settings_text = "<b>❌ You still need to join the following channel(s):</b>\n\n"

        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                if mode == "on":
                    link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                    settings_text += f"<blockquote><b>› <a href='{link}'>{chat.title}</a></b></blockquote>\n"
                    buttons.append([InlineKeyboardButton(f"Join {chat.title}", url=link)])
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id} for force-sub: {e}")
                settings_text += f"<blockquote><b>› Channel ID: <code>{ch_id}</code> (Unavailable)</b></blockquote>\n"

        buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_fsub")])

        try:
            await callback.message.edit_text(
                text=settings_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons),
                disable_web_page_preview=True
            )
            logger.info(f"User {user_id} still not subscribed, updated force-sub prompt")
        except Exception as e:
            logger.error(f"Failed to edit force-sub prompt for user {user_id}: {e}")
            await callback.message.reply_text(
                text="<b>❌ Please join the required channels and try again.</b>",
                parse_mode=ParseMode.HTML
            )
        await callback.answer("Please join the channels and try again.")

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#
