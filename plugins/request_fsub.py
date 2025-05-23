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
from urllib.parse import urlparse
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatMemberUpdated
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, InviteHashEmpty, ChatAdminRequired, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import RANDOM_IMAGES, START_PIC
from helper_func import *
from database.database import *

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

# Function to validate if a URL is likely valid
def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception as e:
        logger.error(f"URL validation failed for {url}: {e}")
        return False

# Function to show force-sub settings with channels list and buttons
async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Rᴇǫᴜᴇsᴛ Fꜱᴜʙ Sᴇᴛᴛɪɴɢs:</b>\n\n"
    channels = await db.show_channels()
    
    if not channels:
        settings_text += "<i>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ʏᴇᴛ. Uꜱᴇ 'ᴀᴅᴅ Cʜᴀɴɴᴇʟs' ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</i>"
    else:
        settings_text += "<blockquote><b>⚡ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟs:</b></blockquote>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]</blockquote>\n"
            except Exception:
                settings_text += f"<blockquote><b>•</b> <code>{ch_id}</code> — <i>Uɴᴀᴠᴀɪʟᴀʙʟᴇ</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("•ᴀᴅᴅ Cʜᴀɴɴᴇʟs", callback_data="fsub_add_channel"),
                InlineKeyboardButton("ʀᴇᴍovᴇ Cʜᴀɴɴᴇʟs•", callback_data="fsub_remove_channel")
            ],
            [
                InlineKeyboardButton("Tᴏɢɢʟᴇ Mᴏᴅᴇ•", callback_data="fsub_toggle_mode"),
                InlineKeyboardButton("•ʀᴇꜰᴇʀsʜ•", callback_data="fsub_refresh")
            ],
            [
                InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
            ]
        ]
    )

    # Select a random image and validate
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Sending text message instead.")
        selected_image = None

    if message_id:
        try:
            if selected_image:
                await client.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(media=selected_image, caption=settings_text),
                    reply_markup=buttons
                )
            else:
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message with image {selected_image}: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    else:
        try:
            if selected_image:
                logger.info(f"Attempting to send photo with URL: {selected_image}")
                await client.send_photo(
                    chat_id=chat_id,
                    photo=selected_image,
                    caption=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
                logger.info(f"Successfully sent photo with URL: {selected_image}")
            else:
                logger.warning("No valid image URL available. Sending text message.")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to send photo with URL {selected_image}: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Client, message: Message):
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Using text message.")
        selected_image = None

    if data == "fsub_add_channel":
        await db.set_temp_state(chat_id, "awaiting_channel_input")
        logger.info(f"Set state to 'awaiting_channel_input' for chat {chat_id}")
        try:
            if selected_image:
                await callback.message.reply_photo(
                    photo=selected_image,
                    caption=(
                        "<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴀᴅᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b></blockquote>\n"
                        "<blockquote><b>Eɴsᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b></blockquote>\n"
                        "<blockquote><b>Eɴᴛᴇʀ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b></blockquote>\n\n"
                        "<b>E x ᴀ ᴍ ᴘ ʟ ᴇ:</b>\n"
                        "<code>-100XXXXXXXXXX</code>\n"
                        "<code>@ChannelUsername</code>"
                    ),
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await callback.message.reply(
                    "<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴀᴅᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b></blockquote>\n"
                    "<blockquote><b>Eɴsᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b></blockquote>\n"
                    "<blockquote><b>Eɴᴛᴇʀ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b></blockquote>\n\n"
                    "<b>E x ᴀ ᴍ ᴘ ʟ ᴇ:</b>\n"
                    "<code>-100XXXXXXXXXX</code>\n"
                    "<code>@ChannelUsername</code>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to send photo for channel input prompt: {e}")
            await callback.message.reply(
                "<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴀᴅᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b></blockquote>\n"
                "<blockquote><b>Eɴsᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b></blockquote>\n"
                "<blockquote><b>Eɴᴛᴇʀ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b></blockquote>\n\n"
                "<b>E x ᴀ ᴍ ᴘ ʟ ᴇ:</b>\n"
                "<code>-100XXXXXXXXXX</code>\n"
                "<code>@ChannelUsername</code>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        await callback.answer("<blockquote><b>Eɴᴛᴇʀ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ!</b></blockquote>")

    elif data == "fsub_remove_channel":
        await show_force_sub_settings(client, chat_id, callback.message.id)
        await callback.answer("<blockquote><b>Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇᴍᴏᴠᴇ!</b></blockquote>")

    elif data == "fsub_toggle_mode":
        current_mode = await db.get_force_sub_mode()
        new_mode = not current_mode
        await db.set_force_sub_mode(new_mode)
        await show_force_sub_settings(client, chat_id, callback.message.id)
        await callback.answer(f"<blockquote><b>Fᴏʀᴄᴇ Sᴜʙ Mᴏᴅᴇ {'Eɴᴀʙʟᴇᴅ' if new_mode else 'Dɪsᴀʙʟᴇᴅ'}!</b></blockquote>")

    elif data == "fsub_refresh":
        await show_force_sub_settings(client, chat_id, callback.message.id)
        await callback.answer("<blockquote><b>Sᴇᴛᴛɪɴɢs ʀᴇғʀᴇsʜᴇᴅ!</b></blockquote>")

    elif data == "fsub_close":
        await callback.message.delete()
        await callback.answer("<blockquote><b>Sᴇᴛᴛɪɴɢs ᴄʟᴏsᴇᴅ!</b></blockquote>")

@Bot.on_message(filters.private & filters.regex(r"^-?\d+$|^@[\w]+$") & admin)
async def handle_channel_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Using text message.")
        selected_image = None

    if state == "awaiting_channel_input":
        channel_input = message.text
        try:
            if channel_input.startswith("@"):
                chat = await client.get_chat(channel_input)
                channel_id = chat.id
            else:
                channel_id = int(channel_input)
                chat = await client.get_chat(channel_id)

            if chat.type != ChatType.CHANNEL:
                try:
                    if selected_image:
                        await message.reply_photo(
                            photo=selected_image,
                            caption="<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                    else:
                        await message.reply(
                            "<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                except Exception as e:
                    logger.error(f"Failed to send photo for invalid channel type: {e}")
                    await message.reply(
                        "<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                return

            member = await client.get_chat_member(chat.id, "me")
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                try:
                    if selected_image:
                        await message.reply_photo(
                            photo=selected_image,
                            caption="<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                    else:
                        await message.reply(
                            "<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                except Exception as e:
                    logger.error(f"Failed to send photo for non-admin bot: {e}")
                    await message.reply(
                        "<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                return

            all_channels = await db.show_channels()
            channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
            if channel_id in channel_ids_only:
                try:
                    if selected_image:
                        await message.reply_photo(
                            photo=selected_image,
                            caption=f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                    else:
                        await message.reply(
                            f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>",
                            parse_mode=ParseMode.HTML,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )
                except Exception as e:
                    logger.error(f"Failed to send photo for existing channel: {e}")
                    await message.reply(
                        f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                return

            link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
            await db.add_channel(channel_id)
            try:
                if selected_image:
                    await message.reply_photo(
                        photo=selected_image,
                        caption=(
                            f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                            f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                            f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>"
                        ),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                else:
                    await message.reply(
                        f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                        f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                        f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
            except Exception as e:
                logger.error(f"Failed to send photo for channel added: {e}")
                await message.reply(
                    f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                    f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                    f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            await db.set_temp_state(chat_id, "")
        except Exception as e:
            try:
                if selected_image:
                    await message.reply_photo(
                        photo=selected_image,
                        caption=f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_input}</code>\n\n<i>{e}</i>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                else:
                    await message.reply(
                        f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_input}</code>\n\n<i>{e}</i>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
            except Exception as e2:
                logger.error(f"Failed to send photo for channel add failure: {e2}")
                await message.reply(
                    f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_input}</code>\n\n<i>{e}</i>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            await db.set_temp_state(chat_id, "")

@Bot.on_chat_member_updated()
async def handle_chat_members(client: Client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id

    if await db.reqChannel_exist(chat_id):
        old_member = chat_member_updated.old_chat_member

        if not old_member:
            return

        if old_member.status == ChatMemberStatus.MEMBER:
            user_id = old_member.user.id

            if await db.req_user_exist(chat_id, user_id):
                await db.del_req_user(chat_id, user_id)

@Bot.on_chat_join_request()
async def handle_join_request(client: Client, chat_join_request):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id

    if await db.reqChannel_exist(chat_id):
        if not await db.req_user_exist(chat_id, user_id):
            await db.req_user(chat_id, user_id)

@Bot.on_message(filters.command('addchnl') & filters.private & admin)
async def add_force_sub(client: Client, message: Message):
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Using text message.")
        selected_image = None

    try:
        temp = await client.send_photo(
            chat_id=message.chat.id,
            photo=selected_image,
            caption="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        ) if selected_image else await client.send_message(
            chat_id=message.chat.id,
            text="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to send initial message/photo: {e}")
        temp = await client.send_message(
            chat_id=message.chat.id,
            text="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption="<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/addchnl -100XXXXXXXXXX</code>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/addchnl -100XXXXXXXXXX</code>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for usage: {e}")
            await temp.edit(
                "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/addchnl -100XXXXXXXXXX</code>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    try:
        channel_id = int(args[1])
    except ValueError:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption="<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    "<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for invalid channel ID: {e}")
            await temp.edit(
                "<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    all_channels = await db.show_channels()
    channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
    if channel_id in channel_ids_only:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for existing channel: {e}")
            await temp.edit(
                f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <code>{channel_id}</code>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    try:
        chat = await client.get_chat(channel_id)

        if chat.type != ChatType.CHANNEL:
            try:
                if selected_image:
                    await temp.edit_media(
                        media=InputMediaPhoto(
                            media=selected_image,
                            caption="<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>"
                        ),
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                else:
                    await temp.edit(
                        "<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
            except Exception as e:
                logger.error(f"Failed to edit message for non-channel type: {e}")
                await temp.edit(
                    "<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            return

        member = await client.get_chat_member(chat.id, "me")
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            try:
                if selected_image:
                    await temp.edit_media(
                        media=InputMediaPhoto(
                            media=selected_image,
                            caption="<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>"
                        ),
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
                else:
                    await temp.edit(
                        "<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                        parse_mode=ParseMode.HTML,
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                    )
            except Exception as e:
                logger.error(f"Failed to edit message for non-admin bot: {e}")
                await temp.edit(
                    "<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            return

        link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
        
        await db.add_channel(channel_id)
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=(
                            f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                            f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                            f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>"
                        )
                    ),
                    disable_web_page_preview=True,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                    f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                    f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for channel added: {e}")
            await temp.edit(
                f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʜʟʟʏ!</b></blockquote>\n\n"
                f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    except Exception as e:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e2:
            logger.error(f"Failed to edit message for channel add failure: {e2}")
            await temp.edit(
                f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

@Bot.on_message(filters.command('delchnl') & filters.private & admin)
async def del_force_sub(client: Client, message: Message):
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Using text message.")
        selected_image = None

    try:
        temp = await client.send_photo(
            chat_id=message.chat.id,
            photo=selected_image,
            caption="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        ) if selected_image else await client.send_message(
            chat_id=message.chat.id,
            text="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to send initial message/photo: {e}")
        temp = await client.send_message(
            chat_id=message.chat.id,
            text="<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption="<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/delchnl -100XXXXXXXXXX</code>\n<b>Rᴇᴍᴏᴠᴇ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>"
                    ),
                    reply_markup=InlineKeyboardMarkup(buttons),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/delchnl -100XXXXXXXXXX</code>\n<b>Rᴇᴍᴏᴠᴇ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for usage: {e}")
            await temp.edit(
                "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/delchnl -100XXXXXXXXXX</code>\n<b>Rᴇᴍᴏᴠᴇ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    try:
        channel_id = int(args[1])
    except ValueError:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption="<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    "<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for invalid channel ID: {e}")
            await temp.edit(
                "<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    all_channels = await db.show_channels()
    channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
    if channel_id not in channel_ids_only:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=f"<blockquote><b>Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <code>{channel_id}</code>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for channel not found: {e}")
            await temp.edit(
                f"<blockquote><b>Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    try:
        chat = await client.get_chat(channel_id)
        await db.del_channel(channel_id)
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=(
                            f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                            f"<blockquote><b>Nᴀᴍᴇ:</b> {chat.title}</blockquote>\n"
                            f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>"
                        )
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                    f"<blockquote><b>Nᴀᴍᴇ:</b> {chat.title}</blockquote>\n"
                    f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to edit message for channel removed: {e}")
            await temp.edit(
                f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʬ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                f"<blockquote><b>Nᴀᴍᴇ:</b> {chat.title}</blockquote>\n"
                f"<blockquote><b>Iᴅ:</b></blockquote>\n <code>{channel_id}</code>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    except Exception as e:
        try:
            if selected_image:
                await temp.edit_media(
                    media=InputMediaPhoto(
                        media=selected_image,
                        caption=f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>"
                    ),
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await temp.edit(
                    f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e2:
            logger.error(f"Failed to edit message for channel remove failure: {e2}")
            await temp.edit(
                f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

@Bot.on_message(filters.command('listchnl') & filters.private & admin)
async def list_force_sub_channels(client: Client, message: Message):
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    if not is_valid_url(selected_image):
        logger.warning(f"Selected image URL invalid: {selected_image}. Falling back to START_PIC: {START_PIC}")
        selected_image = START_PIC
    if not is_valid_url(selected_image):
        logger.error(f"START_PIC URL invalid: {START_PIC}. Using text message.")
        selected_image = None

    channels = await db.show_channels()
    if not channels:
        try:
            if selected_image:
                await message.reply_photo(
                    photo=selected_image,
                    caption="<b>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            else:
                await message.reply(
                    "<b>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
        except Exception as e:
            logger.error(f"Failed to send photo for no channels: {e}")
            await message.reply(
                "<b>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ғᴏʀ ғᴏʀᴄᴇ-sᴜʙ.</b>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        return

    settings_text = "<b>›› Fᴏʀᴄᴇ-Sᴜʙ Cʜᴀɴɴᴇʟs:</b>\n\n"
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
            settings_text += f"<blockquote><b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]</blockquote>\n"
        except Exception:
            settings_text += f"<blockquote><b>•</b> <code>{ch_id}</code> — <i>Uɴᴀᴠᴀɪʟᴀʙʟᴇ</i></blockquote>\n"

    try:
        if selected_image:
            await message.reply_photo(
                photo=selected_image,
                caption=settings_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        else:
            await message.reply(
                settings_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo for channel list: {e}")
            await message.reply(
                settings_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#
