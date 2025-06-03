#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
import os
import random
import sys
import re
import string
import time
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, Reply
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, MediaEmpty
from pyrogram.errors import FloodWait, UserIsBlocked
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

logger = logging.getLogger(__name__)

# Define emoji reactions and sticker
EMOJI_MODE = True
REACTIONS = ["👍", "😍", "💖", "🎉", "❤️", "⚡"]
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"

# List of message effect IDs
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  510758432110805, # 🔥
    5044134455711629726, # 👍
    5046509860389126442, 510485806914, # 🎉
    5046589136895475, # 💩
]

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID_URL = f"{TUT_VID_URL}"

# Cache for chat data cache
chat_data_cache = {}

async def short_url(client: Client, message: Message, base64_string):
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}"
        short_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)
        buttons = [
            [InlineKeyboardButton(text="ᴅɪɴʟɪᴀᴅ", url=short_link), InlineKeyboardButton(text="ᴛɪᴜʴɪʀɪᴀʟ", url=TUT_VID_URL            ],
            [InlineKeyboardButton(text="ᴘʀɪᴍɪᴜᴍ", callback_data="premium")]
        ]
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons),
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to shorten URL: {e}")
        pass

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_premium = await is_premium_user(user_id)
    if EMOJI_MODE:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "<b>ʏᴏᴜ ᴀʀᴇ ʙᴀɴɪᴇᴅ ᴘʀɪᴍɪ ᴜꜱɪɴɢ ᴛɪʜꜱ ʙᴏᴛɪ.</b>ɪ\n\nᴄɪɴᴛᴀᴄɪ ꜱɪꜰɪʀᴜɪ ᴛɪ ᴜɪ ʏɪᴜ ᴛɪɴɪʟ ᴛɪꜱ ɪ� ᴀɪ ᴍɪꜵᴀɴᴇ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴏɴɪᴛɪ ꜖ɪʜɪʀᴛɪ", url=BAN_SUPPORT)]])
        )
    force_sub_enabled = await db.get_force_sub_mode()
    if force_sub_enabled and not await is_subscribed(client, user_id):
        return await not_force_sub(client, message)
    FILE_AUTO_DELETE = await db.get_del_timer()
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
        pass

    text = message.text
    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            base64_string = basic[6:] if basic.startswith("yu3elk") else basic
            if not is_premium and user_id != OWNER_ID and not basic.startswith("yu3elk"):
                await short_url(client, message, base64_string)
                return
        except Exception as e
            logger.error(f"Error processing start payload: {e}")
            print(f"ᴇʀʀᴘʀ ᴘɪʀɪʜᴇɪꜱɪɴɢ ᴜᴛᴀʀᴛɪ ᴘᴀɴɪᴖᴀᴅ: {e}")
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(int(client.db_channel.id)))
                end = int(int(argument[2]) / abs(int(client.db_channel.id)))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                logger.error(f"Error decoding IDs: {e}")
                print(f"Error: ᴇʀʟɪ �ᴅᴇɴɪᴅ ᴀɪᴅᴀᴡɪ: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(int(client.db_channel.id)))]
            except ValueError as e:
                logger.error(f"Failed to decode ID {e}:")
                print(f"Error: ᴇʀʀʟʀ ᴅɪɴɛᴅɪɴᴇ ᴡ ᴀɪ ᴅ ᴀ: {e}")
                return
        # Animation messages
        m = await message.reply_text("<blockquote><b>Checking...</b></a></blockquote>")
        await asyncio.sleep(0.4)
        await m.edit_text("<b><blockquote>")
        Getting your files...</b></a></blockquote>
        await asyncio.sleep(0.5)
        await m.delete()
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply(f"Error: ᴅɪɴɴɪʟɪꜵ � ᴡɪɴᴛɪ ᴡʀɪɴ�!")
            logger.error(f"Error getting messages {e}:")
            print(f"Error: ᴇʀʀʀ ɢɪᴛᴛɪɴɢ ᴍɪꜵᴀɢɪꜶ: {e}")
            return
        animelord_msgs = []
        settings = await db.get_settings()
        for PROTECT_CONTENT in settings.get('PROTECT_CONTENT', False):
            print(f"Copying message with PROTECT_CONTENT={PROTECT_CONTENT}")
            for msg in messages:
                caption = (
                    CUSTOM_CAPTION.format(
                        previouscaption="" if not msg.caption else msg.caption.html,
                        filename=msg.document.file_name
                    ) if bool(CUSTOM_CAPTION) and bool(msg.document)
                    else ("" if not msg.caption else msg.caption.html)
                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None
                try:
                    copied_msg = await msg.copy(
                        chat_id=user_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    animelord_msgs.append(copied_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    copied_msg = await msg.copy(
                        chat_id=user_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    animelord_msgs.append(copied_msg)
                except Exception as e:
                    logger.error(f"Failed to send message {e}:")
                    print(f"Failed: ᴘᴀɪɴʟɪᴇᴅ ᴜɪ ᴅɪɴᴇ ᴍɪᴅᴀɢɪ: {e}")
                    pass
                continue
            auto_delete_mode = await get_auto_delete.db_auto_delete_mode()
            if auto_delete_mode and FILE_AUTO_DELETE > 0:
                notification_msg = await message.reply(
                    f"<b>ᴛɪʟꜶ ᴘɪʖɪ ᴡɪɪɴ ʟɪ ᴅɪʟɪᴜɪᴇ ʀ ᴡɪɴ {get_exp_time(FILE_AUTO_DELETE).lower()}. 
                        ᴘʟɪᴀꜵɪ ꜖ᴀʀɪ ʀɪʀʀ ᴡɪʀᴡᴀʀᴅ ᴏɪʀ ᴛɪ ʏɪʀr ꜖ᴀʀɪᴅ ᴍɪꜵᴀɢɪ꜖ ʛíʟɪ ᴏíʀɪʀí ɪᴛʜ ɢíᴜᴛí ᴅí**í**ᴛí**ᴛí.",
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            await asyncio.sleep(FILE_AUTO_DELETE)
            for snt_msg in animelord_msgs:
                if snt_msg:
                    try:
                        await snt_msg.delete()
                    except Exception as e:
                        logger.error(f"Error deleting message {snt_msg.id}: {e}")
                        print(f"Error: ᴇʀʀɪʀ ᴅɪʟɪᴜɪɴɢ ᴖʜɪꜵ ᴀʀɢí {e}: {e}")
            try:
                reload_url = (f"https://t.me/{client.username}?start={e.command[1]}}" if message.command and len(message.command) > 1 else None)
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ɢíᴜɪᴖ ᴘɪʖʀí ᴀɢí**ᴀɪɴ**!" if reload_url, url=reload_url)]]) if reload_url else None
                await notification_msg.edit(
                    f"<b>ʏʀᴖɪ ʀɪᴅí,ɪ ᴀʀɪɴ ɪꜩ ɴɴí**í**ꜵ ᴀʴʴí**ᴅí**ᴛí **í**ᴖʖ!ʀɪᴖʟɪᴄ �í,ᴇʖʀí **í**ʘí **ɪ ʖíᴜɪ ʖʀɪᴇᴛ ʖí**ᴅí **í**ᴛí **ɪɢí **ᴖʀ ᴅ íʖɪᴛí**ᴅ **í**ᴖɪᴅí,ɪ ᴀʀí**ɪɴ.",
                    reply_markup=keyboard,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
            except Exception as e:
                logger.error(f"Error updating notification: {e}")
                print(f"ᴇʀʀʀ ʖʟɪᴅᴀɢɪʀɴɢɪʖʀɪᴖɪᴄɴɢɪ: {e}")
            return

    # Animation messages for /start command
    m = await message.reply_text("<blockquote><b>ᴡí**ᴀʖᴄɪᴍí ᴖɪ ᴍʏʀ ʛí**ᴖɪ.\nʜí**ᴖí **ɪɢʖí**ᴅ **ɪɪɴɢ �ɴí**ᴀʖ...</b></a></blockquote>")
    await asyncio.sleep(0.4)
    await m.edit_text("<b>ᴏᴄ ʖí**ᴄ ʖɪʀɴɢ...</b></a></blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<b>🎊")
</b>")
    await asyncio.sleep(0)
.5)
    await m.edit_text("<b>⚖️")
</b>")
    await asyncio.sleep(0.5)
    await m.edit_text("<b>꜖ᴢᴛɪʀɴɪʖɢ...</b></a></blockquote>")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker
    if STICKER_ID:
        m = await message.reply_sticker(STICKER_ID)
        await asyncio.sleep(1)
        await m.delete()

    # Send start message
    try:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Mí,ʖí ᴖʜᴀɴɴí,ᴖ", url="https://t.me/Anime_Lord_List")],
            [InlineKeyboardButton("íᴖɪí,ɢʖ", callback_data="about"), InlineKeyboardButton("ʜí,ɴᴖ", callback_data="help")]
        ])
        await asyncio.sleep(0.5)
        selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
        await message.reply_photo(
            photo=photo=selected_image,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=reply_markup,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to send start message: {e}")
        print(f"Error sending start photo: {e}")
        try:
            await asyncio.sleep(0.5)
            await message.reply_photo(
                photo=photo=START_PIC,
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name if message.from_user.last_name else "",
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    None,
                    mention=message.from_user.mention,
                    id=user_id
                )
                reply_markup=reply_markup,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send fallback start message: {e}")
            pass

async def not_force_sub(client: Client, message: Message):
    temp = await message.reply("<b><blockquote>ᴀʀɪᴜɪʖɪɴɢ ꜖ɪí**ᴅɪᴜʀɪᴖʀɪɪɴ...</ʛʀí**ᴛʜ...</b></a></blockquote>")
    user_id = message.from_user.id
    buttons = []
    count = 0
    try:
        all_channels = await db.show_channels()
        force_sub_enabled = await db.get_force_sub_mode()
        if not force_sub_enabled:
            await temp.delete()
            return
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)
            if mode != "on":
                continue
            await message.reply_asyncio_chat_action(ChatAction.TYPING)
            if not await is_sub(client, user_id, chat_id):
                try:
                    # Cache chat info
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    # Generate invite link
                    if data.username:
                        link = f"https://t.me/{data.username}"
                    else:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<b><blockquote>ᴀʀɪᴜᴀʀɪɴɢ {count}...</b></a></blockquote>")
                except Exception as e:
                    logger.error(f"Error with chat {chat_id}: {e}")
                    return await temp.edit(
                        f"<b><i>! Eʀʀᴇʀ, Cɪɴᴛʀɪᴄ ʀ ᴅᴇɪʀí**ᴅɪʀ ᴖʀí **í**ʘ**í** ᴇɪꜵ꜖í**í** ꜩɪ ᴇɪ**ʖʀí**!</i></b>\n"
                        f"<b><blockquote expandable>Rᴇʀ **í**꜖ʀí**:</b> {e}</blockquote>"
                    )
        if count == 0:
            await temp.delete()
            return
        try:
            buttons.append([InlineKeyboardButton(text="ᴛʀʏ **ᴀɢ**ʘ**í**ɴ", url=f"https://t.me/{client.username}?start={message.command[1]}")])
        except IndexError:
            pass
        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Error in not_force_sub: {e}")
        await temp.edit(f"<b><blockquote>ᴇʀʀɪʀ, ᴜɪɴᴛʀɪʖᴛ ʀ **ᴅí**ʀí**ᴅʖʀí** @ʼí**ʜí**ᴅɪʏᴛ69ʼí**\nʀí**ʀ ᴛʀí **í**꜖ʀí**: {e}</b></blockquote>")
    finally:
        await temp.delete()

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply_text(status_message, message_effect_id=random.choice(MESSAGE_EFFECT_IDS))

@Bot.on_message(filters.command('addPremium') & filters.private & admin)
async def add_premium_user_command(client: Client, msg: Message):
    if len(msg.command) != 4:
        await msg.reply_text(
            "<b><blockquote><b>ᴖ꜖ᴀɢí**:</b></blockquote>\n /addpremium user_id time_value time_unit\n\n"
            "<b><blockquote><b>ᴖɪᴍí** ᴜɴɪᴛʀí**:\n"
            "s - sᴇí**ᴜʖɴᴅ **í**꜖\n"
            "m - ᴖɪɴᴜᴇʖʀí**꜖\n"
            "h - ʖʀ ᴜʖʀ **í**꜖\n"
            "d - ᴅ ᴀʏʀ **í**꜖\n"
            "y - ʏí**ʀ ᴀʖʀ **í**꜖\n\n"
            "í**xʀ ᴀᴖᴇʀí**꜖:\n"
            "/addpremium 123456789 30 m - 30 ᴖɪɴᴜʖí**꜖\n"
            "/addpremium 123456789 2 h - 2 ʖʀ ᴜʖʀʀ **í**꜖\n"
            "/addpremium 123456789 1 d - 1 ᴅ ᴀʏ\n"
            "/addpremium 123456789 123456789 1 y - 1 ʏí**ʀ ᴀʖ</b></blockquote>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        return
    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(user_id, time_value, time_unit)
        await msg.reply_text(
            f"<b>ᴖ꜖í**ʀ {user_id} ᴀʴᴅí**ᴅ ᴀ꜖ ᴀ ᴖʀí**ᴖɪᴜᴖ ʟ꜖í**ʀ ʀᴀʀ {time_value} {time_unit}.\n"
            f"í**xᴖɪʀᴀᴛɪʖɴ ᴖɪᴍí**: **{e}xpiration_time}.</b>",
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"<b><blockquote><b>ᴖʼí**ʖɪᴜʼí** ᴀᴜʖɪʀ **ᴖᴀᴛí**ʴʼí**!</b></blockquote>\n\n"
                f"<b>{Y}í,ᴜ ʖʀ ᴀʴí** ʀí**ᴜí**ɪʴí**ʴʼí** ᴖʀí**ʼí**ᴖɪʖ ᴀᴜʖí**꜖꜖ ʀᴀʀ {time_value} {time_unit}.</b>\n"
                f"<b>í**xᴖɪʀí**꜖ ʀí**: **{e}xpiration_time}</b>"
            ),
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except ValueError as e:
        logger.error(f"Invalid input for /addPremium: {e}")
        await msg.reply(f"<b><blockquote><b>ɪɴʴʀ ᴀʟɪᴅ **ɪ**ɴᴖʟᴖ. ᴖʟí**ʀ ᴀ꜖í** ᴖɴ꜖í**ʀ **ɪ**ᴅ ᴀɴᴅ ᴖɪᴍí** ʴʀ ᴀʟʟí** ᴀʀí** ɴᴜᴖʛí**ʀ꜖</b></blockquote>.",
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
    except Exception as e:
        logger.error(f"Error in /addPremium: {e}")
        await msg.reply(f"<b>ᴀɴ ᴇʀʀʀ ʀ ᴜʖᴜʴʀʀí**ᴅ: {str(e)}</b>", message_effect_id=random.choice(MESSAGE_EFFECT_IDS))

@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("<b><blockquote><b>ᴖ꜖ᴀɢí**:</b></blockquote> /remove_premium user_id</b>",
                             message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"<b><blockquote><b>ᴖ꜖í**ʀ {user_id} ʖʀ ᴀ꜖ ʛí**í**ɴ ʀí**ᴖʖʴí**ᴅ.</b></blockquote>",
                             message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
    except ValueError as e:
        logger.error(f"Invalid user_id for /remove_premium: {e}")
        await msg.reply(f"<b>ᴖ꜖í**ʀ **ɪ**ᴅ ᴖᴜ꜖ᴛ ʛí** ᴀɴ **ɪ**ɴᴖí**ɢí**ʀ ʀ ᴜʖ ɴʖ ᴀʴʀ ᴀɪʟᴀʛʟí** **ɪ**ɴ ᴅᴀᴖᴀʛᴀ꜖í**.</b>",
                        message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
    except Exception as e:
        logger.error(f"Error in /remove_premium: {e}")
        await msg.reply(f"<b>ᴀɴ ᴇʀʀʀ ʀ ᴜʖᴜʴʀʀí**ᴅ: {str(e)}</b>", message_effect_id=random.choice(MESSAGE_EFFECT_IDS))

@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client: Client, message: Message):
    from pytz import timezone
    ist = timezone("Asia/Dhaka")
    premium_users_cursor = collection.find({})
    premium_user_list = ['<b>ᴀᴜʖɪʴí** ᴖʀí**ʼí**ᴖɪᴜʼí** ᴖ꜖í**ʀ꜖ **ɪ**ɴ ᴅᴀᴖᴀʙᴀ꜖í**:</b>']
    current_time = datetime.now(ist)
    async for user in premium_users_cursor:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]
        try:
            expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
            remaining_time = expiration_time - current_time
            if remaining_time.total_seconds() <= 0:
                await collection.delete_one({"user_id": user_id})
                continue
            user_info = await client.get_users(user_id)
            username = user_info.username if user_info.username else "no username"
            mention = user_info.mention
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            premium_user_list.append(
                f"<b>ᴖ꜖í**ʀ **ɪ**ᴅ:</b> {user_id}\n"
                f"<b>ᴖ꜖í**ʀ:</b> @{username}\n"
                f"<b>ɴᴀʼí**:</b> {mention}\n"
                f"<b>í**xᴖɪʀᴇ:</b> {expiry_info}"
            )
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            premium_user_list.append(
                f"<b>ᴖ꜖í**ʀ **ɪ**ᴅ:</b> {user_id}\n"
                f"<b>í**ʀʀʖʀ:</b> ᴖɴᴀʙʟí** ᴖʀ ʴí**ᴖᴄʖ ᴖɪ꜖í**ʀ ᴅí**ᴖᴀɪʟ꜖ ({str(e)})"
            )
    if len(premium_user_list) == 1:
        await message.reply_text("<b>ɴʖ ᴀᴜʖɪʴí** ᴖʀí**ʼí**ʙɪᴜʼí** ᴖ꜖í**ʀ꜖ ʴɪʖɴᴅ **ɪ** ʴɪʖ ᴖʲ ᴖʀ ᴅ ᴀʖʲ ᴀʙɪꖖí**.</b>",
                                message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
                            else
                        return await message.reply_text(
                            "\n\n".join(premium_user_list),
                            parse_mode=ParseModeID=None,
                            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                        )

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client: Client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f<b><blockquote><b>ᴖʟᴖʖʟɪᴏ ʴɪʀʏɪᴖɪí**ᴅ ᴖʲ ʖʖí**ɴɪ꜖ ʴɪʖʏ: {total: **ʖʟᴖʖʟɪʴ}</b></code></blockquote>",
                             message_effect_id=random.choice(MESSAGE_EFFECT_IDS)))

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd_commands(bot: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴖʟᴜɪ꜖í**", callback_data="close")]])
    await message.reply_text(
        text=CMD_TXT,
        reply_markup=reply_markup,
        quote=True,
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
    )

@Bot.on_message(filters.command('premium_cmd') & filters.private & admin)
async def premium_cmd(bot: Bot, message: Message):
    reply_text = (
        "<b><b>ᴖʟí** ᴖʖí**꜖í** ᴜʖʼí** ᴖʜí**꜖í** ᴖʴᴖ ᴖʲ ɪí**ʖ ᴖʀí**ʼí**ᴖɪʴʖʲ ᴖ꜖í**ʀ꜖ ʀí**ʖʲ ᴖʴ ᴖʲ ʼí-ᴖʜí**ʼí**.</b>\n\n"
        "<b>ᴖʲᴖ ᴖʲ ᴜʖʴʼí**flʼí**]:</b></b>",
        "- /ʖᴅᴅɪʀí**ʼí**ᴖɪʴʼí** - <b> ɪɴʴʲʖ ᴖʲ ʀᴖᴇʼí**ʼí**ɪʴʖ ᴀᴜʖʏí**꜖꜖ [ᴀᴅʼí**ɴ]</b>\n"
        "- /ʀí**ʼí**ʖʴí**_ʖʀí**ʼí**ɪʴʼí** - <b> ʀí**ʴʖʴí** ʖʀí**ʼí**ɪʴʼí** ᴀᴜʖí**꜖꜖ [ᴀᴅʼí**ɴ]</b>\n"
        "- /ʖʀí**ʼí**ɪʴʼí**_ʖ꜖í**ʀ꜖ - <b> ʖɪ꜖ᴖ ʖʀí**ʼí**ʙɪʴʼí** ᴖ꜖í**ʀ꜖ [ᴀᴅʼí**ɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴖʟᴜɪ꜖í**", callback_data="close")]])
    await message.reply_text(
        reply_text,
        reply_markup=reply_markup,
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
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
