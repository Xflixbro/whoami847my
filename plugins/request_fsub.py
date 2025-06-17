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
import sys
import time
import logging
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatMemberUpdated, ChatPermissions, InputMediaPhoto
from bot import Bot
from helper_func import *
from database.database import *
from config import OWNER_ID, RANDOM_IMAGES, START_PIC

# Set up logging for this module
logger = logging.getLogger(__name__)

# Function to show force-sub settings with channels list and buttons
async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    """Show the force-sub settings menu with channel list and controls."""
    settings = await db.get_settings()
    force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
    mode_status = "🟢 Enabled" if force_sub_enabled else "🔴 Disabled"
    settings_text = f"<b>›› Request Fsub Settings:</b>\n\n<blockquote><b>Force Sub Mode: {mode_status}</b></blockquote>\n\n"
    channels = await db.show_channels()
    
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet. Use 𖤓 Add Channels 𖤓 to add channels.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels[:5]:  # Show only first 5 channels
            try:
                chat = await client.get_chat(ch_id)
                temp_off = await db.get_channel_temp_off(ch_id)
                status = "🔴 Off" if temp_off else "🟢 On"
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code> ({status})</b></blockquote>\n"
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                if "USERNAME_NOT_OCCUPIED" in str(e):
                    await db.rem_channel(ch_id)  # Remove invalid channel from database
                    logger.info(f"Removed invalid channel {ch_id} from database")
                    continue
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"
        if len(channels) > 5:  # If more than 5 channels
            settings_text += f"<blockquote><i>...and {len(channels) - 5} more.</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Add Channels ", callback_data="fsub_add_channel"),
                InlineKeyboardButton(" Remove Channels •", callback_data="fsub_remove_channel")
            ],
            [
                InlineKeyboardButton("• Toggle Mode •", callback_data="fsub_toggle_mode")
            ],
            [
                InlineKeyboardButton("• Single Off •", callback_data="fsub_single_off"),
                InlineKeyboardButton(" Fully Off •", callback_data="fsub_fully_off")
            ],
            [
                InlineKeyboardButton(" Channels List •", callback_data="fsub_channels_list")
            ],
            [
                InlineKeyboardButton("• Refresh ", callback_data="fsub_refresh"),
                InlineKeyboardButton(" Close•", callback_data="fsub_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

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
            logger.info("Edited message as text-only")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent photo message with image {selected_image}")
        except Exception as e:
            logger.error(f"Failed to send photo message with image {selected_image}: {e}")
            try:
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info("Sent text-only message as fallback")
            except Exception as e:
                logger.error(f"Failed to send text-only message: {e}")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info("Sent text-only message without effect as final fallback")

# Function to show the channels list
async def show_channels_list(client: Client, chat_id: int, message_id: int):
    """Show the list of force-sub channels with their links."""
    channels = await db.show_channels()
    settings_text = "<b>›› Force-sub Channels List:</b>\n\n"
    
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet.</i></blockquote>"
    else:
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code></b></blockquote>\n"
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                if "USERNAME_NOT_OCCUPIED" in str(e):
                    await db.rem_channel(ch_id)  # Remove invalid channel from database
                    logger.info(f"Removed invalid channel {ch_id} from database")
                    continue
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Back •", callback_data="fsub_back"),
                InlineKeyboardButton("• Close •", callback_data="fsub_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=settings_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("Edited message with channels list")
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=settings_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("Sent channels list message")

# Function to show the fully off settings
async def show_fully_off_settings(client: Client, chat_id: int, message_id: int = None):
    """Show the fully off settings menu for force-sub system."""
    settings = await db.get_settings()
    force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
    mode_status = "🟢 Enabled" if force_sub_enabled else "🔴 Disabled"
    settings_text = f"<b>›› Force Sub Fully Off Settings:</b>\n\n<blockquote><b>Force Sub Mode: {mode_status}</b></blockquote>\n\n"
    settings_text += "<b>Click below buttons to change settings</b>"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Disable ❌" if force_sub_enabled else "• Enable ✅", callback_data="fsub_toggle_full"),
                InlineKeyboardButton("• Refresh ", callback_data="fsub_full_refresh")
            ],
            [
                InlineKeyboardButton("• Back •", callback_data="fsub_back"),
                InlineKeyboardButton("• Close •", callback_data="fsub_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if message_id:
        try:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=buttons
            )
            logger.info("Edited message with fully off settings")
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent fully off settings message with image {selected_image}")
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info("Sent fully off settings message as fallback")
