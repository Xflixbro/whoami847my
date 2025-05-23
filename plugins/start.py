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
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, MediaEmpty
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

# Define emoji reactions and sticker
EMOJI_MODE = True
REACTIONS = ["👍", "😍", "🔥", "🎉", "❤️", "⚡"]
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"

# List of message effect IDs for random selection (Converted to integers)
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

async def short_url(client: Client, message: Message, base64_string):
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}"
        short_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)
        buttons = [
            [InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ", url=short_link), InlineKeyboardButton(text="ᴛᴜᴛᴏʀɪᴀʟ", url=TUT_VID)],
            [InlineKeyboardButton(text="ᴘʀᴇᴍɪᴜᴍ", callback_data="premium")]
        ]
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except IndexError:
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
            "ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.\n\nᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪs ɪs ᴀ ᴍɪsᴛᴀᴋᴇ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ", url=BAN_SUPPORT)]])
        )
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)
    FILE_AUTO_DELETE = await db.get_del_timer()
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    # Animation messages
    m = await message.reply_text("ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴍʏ ʙᴏᴛ.\nʜᴏᴘᴇ ʏᴏᴜ'ʀᴇ ᴅᴏɪɴɢ ᴡᴇʟʟ...")
    await asyncio.sleep(0.4)
    await m.edit_text("...")
    await asyncio.sleep(0.5)
    await m.edit_text("ᴄʜᴇᴄᴋɪɴɢ...")
    await asyncio.sleep(0.5)
    await m.edit_text("sᴛᴀʀᴛɪɴɢ...")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker
    if STICKER_ID:
        m = await message.reply_sticker(STICKER_ID)
        await asyncio.sleep(1)
        await m.delete()

    text = message.text
    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            base64_string = basic[6:-1] if basic.startswith("yu3elk") else basic
            if not is_premium and user_id != OWNER_ID and not basic.startswith("yu3elk"):
                await short_url(client, message, base64_string)
                return
        except Exception as e:
            print(f"ᴇʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ sᴛᴀʀᴛ ᴘᴀʏʟᴏᴀᴅ: {e}")
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"ᴇʀʀᴏʀ ᴅᴇᴄᴏᴅɪɴɢ ɪᴅs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"ᴇʀʀᴏʀ ᴅᴇᴄᴏᴅɪɴɢ ɪᴅ: {e}")
                return
        temp_msg = await message.reply("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ!")
            print(f"ᴇʀʀᴏʀ ɢᴇᴛᴛɪɴɢ ᴍᴇssᴀɢᴇs: {e}")
            return
        finally:
            await temp_msg.delete()
        animelord_msgs = []
        # Load settings dynamically before copying messages
        settings = await db.get_settings()
        PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)
        print(f"Copying message with PROTECT_CONTENT={PROTECT_CONTENT}")
        for msg in messages:
            caption = (CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                             filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                       else ("" if not msg.caption else msg.caption.html))
            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None
            try:
                copied_msg = await msg.copy(chat_id=user_id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=user_id, caption=caption, parse_mode=ParseMode.HTML, 
                                            reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except Exception as e:
                print(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇ: {e}")
                pass
        if FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"ᴛʜɪs ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_exp_time(FILE_AUTO_DELETE).lower()}. ᴘʟᴇᴀsᴇ sᴀᴠᴇ ᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ ʏᴏᴜʀ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs ʙᴇғᴏʀᴇ ɪᴛ ɢᴇᴛs ᴅᴇʟᴇᴛᴇᴅ."
            )
            await asyncio.sleep(FILE_AUTO_DELETE)
            for snt_msg in animelord_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"ᴇʀʀᴏʀ ᴅᴇʟᴇᴛɪɴɢ ᴍᴇssᴀɢᴇ {snt_msg.id}: {e}")
            try:
                reload_url = f"https://t.me/{client.username}?start={message.command[1]}" if message.command and len(message.command) > 1 else None
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ ᴀɢᴀɪɴ!", url=reload_url)]]) if reload_url else None
                await notification_msg.edit(
                    "ʏᴏᴜʀ ᴠɪᴅᴇᴏ/ғɪʟᴇ ɪs sᴜᴄᴄᴇssғᴜʟʏ ᴅᴇʟᴇᴛᴇᴅ!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ/ғɪʟᴇ.",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"ᴇʀʀᴏʀ ᴜᴘᴅᴀᴛɪɴɢ ɴᴏᴛɪғɪᴄᴀᴛɪᴏɴ: {e}")
        return

    # Send start message
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs", url="https://t.me/Anime_Lord_List")],
        [InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"), InlineKeyboardButton("ʜᴇʟᴘ", callback_data="help")]
    ])
    try:
        await asyncio.sleep(0.5)
        selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
        await message.reply_photo(
            photo=selected_image,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        print(f"ᴇʀʀᴏʀ sᴇɴᴅɪɴɢ sᴛᴀʜʀᴛ ᴘʜᴏᴛᴏ: {e}")
        await asyncio.sleep(0.5)
        await message.reply_photo(
            photo=START_PIC,
            caption=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
        )

async def not_joined(client: Client, message: Message):
    temp = await message.reply("ᴄʜᴇᴄᴋɪɴɢ sᴜʙsᴄʀɪᴘᴛɪᴏɴ...")
    user_id = message.from_user.id
    buttons = []
    count = 0
    try:
        all_channels = await db.show_channels()
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)
            await message.reply_chat_action(ChatAction.TYPING)
            if not await is_sub(client, user_id, chat_id):
                try:
                    data = await client.get_chat(chat_id)
                    name = data.title
                    link = f"https://t.me/{data.username}" if data.username else (await client.create_chat_invite_link(
                        chat_id=chat_id,
                        expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                    )).invite_link
                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"ᴄʜᴇᴄᴋɪɴɢ {count}...")
                except Exception as e:
                    print(f"ᴇʀʀᴏʀ ᴡɪᴛʜ ᴄʜᴀᴛ {chat_id}: {e}")
                    return await temp.edit(f"ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ @Mehediyt69\nʀᴇᴀsᴏɴ: {e}")
        try:
            buttons.append([InlineKeyboardButton(text='ᴛʀʏ ᴀɢᴀɪɴ', url=f"https://t.me/{client.username}?start={message.command[1]}")])
        except IndexError:
            pass
        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        print(f"ғɪɴᴀʟ ᴇʀʀᴏʀ: {e}")
        await temp.edit(f"<blockquote><b>ᴇʀʀᴏʀ, ᴄᴏɴᴛᴀᴄᴛ ᴅᴇᴠᴇʟᴏᴘᴇʀ @MehediYT69\nʀᴇᴀsᴏɴ: {e}</b></blockquote>")
    finally:
        await temp.delete()

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply_text(status_message)

@Bot.on_message(filters.command('addPremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "<blockquote><b>ᴜsᴀɢᴇ:</b></blockquote>\n /addpremium <user_id> <time_value> <time_unit>\n\n"
            "<blockquote><b>ᴛɪᴍᴇ ᴜɴɪᴛs:\n"
            "s - sᴇᴄᴏɴᴅs\n"
            "m - ᴍɪɴᴜᴛᴇs\n"
            "h - ʜᴏᴜʀs\n"
            "d - ᴅᴀʏs\n"
            "y - ʏᴇᴀʀs\n\n"
            "ᴇxᴀᴍᴘʟᴇs:\n"
            "/addpremium 123456789 30 m - 30 ᴍɪɴᴜᴛᴇs\n"
            "/addpremium 123456789 2 h - 2 ʜᴏᴜʀs\n"
            "/addpremium 123456789 1 d - 1 ᴅᴀʏ\n"
            "/addpremium 123456789 1 y - 1 ʏᴇᴀʀ</b></blockquote>"
        )
        return
    try:
        usermega_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(user_id, time_value, time_unit)
        await msg.reply_text(
            f"ᴜsᴇʀ {user_id} ᴀᴅᴅᴇᴅ ᴀs ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀ ғᴏʀ {time_value} {time_unit}.\n"
            f"ᴇxᴘɪʀᴀᴛɪᴏɴ ᴛɪᴍᴇ: {expiration_time}."
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"<blockquote><b>ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!</b></blockquote>\n\n"
                f"<b>Yᴏᴜ ʜᴀᴠᴇ ʀᴇᴄᴇɪᴠᴇᴅ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ғᴏʀ {time_value} {time_unit}.</b>\n"
                f"<b>ᴇxᴘɪʀᴇs ᴏɴ: {expiration_time}</b>"
            ),
        )
    except ValueError:
        await msg.reply_text("<blockquote><b>ɪɴᴠᴀʟɪᴅ ɪɴᴘᴜᴛ. ᴘʟᴇᴀsᴇ ᴇɴsᴜʀᴇ ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴛɪᴍᴇ ᴠᴀʟᴜᴇ ᴀʀᴇ ɴᴜᴍʙᴇRs</b></blockquote>.")
    except Exception as e:
        await msg.reply_text(f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {str(e)}")

@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("<blockquote><b>ᴜsᴀɢᴇ:</b></blockquote> /remove_premium user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"<blockquote><b>ᴜsᴇʀ {user_id} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ.</b></blockquote>")
    except ValueError:
        await msg.reply_text("ᴜsᴇʀ ɪᴅ ᴍᴜsᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ ᴏʀ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ.")

@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    from pytz import timezone
    ist = timezone("Asia/Dhaka")
    premium_users_cursor = collection.find({})
    premium_user_list = ['ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ɪɴ ᴅᴀᴛᴀʙᴀsᴇ:']
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
                f"ᴜsᴇʀ ɪᴅ: {user_id}\n"
                f"ᴜsᴇʀ: @{username}\n"
                f"ɴᴀᴍᴇ: {mention}\n"
                f"ᴇxᴘɪʀʏ: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"ᴜsᴇʀ ɪᴅ: {user_id}\n"
                f"ᴇʀʀᴏʀ: ᴜɴᴀʙʟᴇ ᴛᴏ ғᴇᴛᴄʜ ᴜsᴇʀ ᴅᴇᴛᴀɪʟs ({str(e)})"
            )
    if len(premium_user_list) == 1:
        await message.reply_text("ɴᴏ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ.")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"<blockquote><b>ᴛᴏᴛᴀʟ ᴠᴇʀɪғɪᴇᴅ ᴛᴏᴋᴇɴs ᴛᴏᴅᴀʏ: {total}</b></blockquote>")

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(text=CMD_TXT, reply_markup=reply_markup, quote=True)

@Bot.on_message(filters.command('admin_cmd') & filters.private & admin)
async def admin_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ᴀᴅᴅ, ʀᴇᴍᴏᴠᴇ, ᴀɴᴅ ɢᴇᴛ ᴀ ʟɪsᴛ ᴏғ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs.</b>\n\n"
        "<b>ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>\n"
        "- /add_admin - <b>ᴀᴅᴅ ɴᴇᴡ ᴀᴅᴍɪɴ [ᴀᴅᴍɪɴ]</b>\n"
        "- /deladmin - <b>ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴ [ᴀᴅᴍɪɴ]</b>\n"
        "- /admins - <b>ʟɪsᴛ ᴀʟʟ ᴀᴅᴍɪɴs [ᴀᴅᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('premium_cmd') & filters.private & admin)
async def premium_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs ʀᴇʟᴀᴛᴇᴅ ᴄᴏᴍᴍᴀɴᴅs.</b>\n\n"
        "<b>ᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>\n"
        "- /addpremium - <b>ɢʀᴀɴᴛ ᴘʀᴇᴮᴍɪᴜᴍ ᴀᴄᴄᴇss [ᴀᴅᴍɪɴ]</b>\n"
        "- /remove_premium - <b>ʀᴇᴠᴏᴋᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss [ᴀᴅᴍɪɴ]</b>\n"
        "- /premium_users - <b>ᴛ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs [ᴀᴅᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('user_cmd') & filters.private & admin)
async def user_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ ᴜsᴇʀs ʀᴇʟᴀᴛᴇᴅ ᴄᴏᴍᴍᴀɴᴅs.</b>\n\n"
        "<b>ᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>\n"
        "- /users - <b>ᴠɪᴇᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs [ᴀᴅᴍɪɴ]</b>\n"
        "- /ban - <b>ᴀɴ ᴀ ᴜsᴇʀ [ᴀᴅᴍɪɴ]</b>\n"
        "- /unban - <b>ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ [ᴀᴅᴍɪɴ]</b>\n"
        "- /banlist - <b>ᴛ ʙᴀɴɴᴇᴅ ᴜsᴇʀs [ᴀᴅᴮᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('broadcast_cmd') & filters.private & admin)
async def broadcast_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅs.</b>\n\n"
        "</b>ᴏᴛ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>\n"
        "- /broadcast - <b>ᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇs ᴛᴏ ᴜsᴇʀs [ᴀᴅᴍɪɴ]</b>\n"
        "- /dbroadcast - <b>ᴏᴀᴅᴄᴀsᴛ ᴡɪᴛʜ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ [ᴀᴅᴍɪɴ]</b>\n"
        "- /pbroadcast - <b>ᴘɪɴ ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs [ᴀᴅᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('force_chn_cmd') & filters.private & admin)
async def force_chn_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ ғᴏʀᴄᴇ sᴜʙ ᴄᴏᴍᴍᴀɴᴅs.</b>\n\n"
        "<b>ᴏᴛ ᴄᴏᴍᴮᴍᴀɴᴅs:</b></blockquote>\n"
        "- /fsub_mode - <b>ᴛᴏɢɢʟᴇ ғᴏʀᴄᴇ-sᴜʙsᴄʀɪʙᴇ [ᴀᴅᴍɪɴ]</b>\n"
        "- /addchnl - <b>ᴀᴅᴅ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟ [ᴀᴅᴍɪɴ]</b>\n"
        "- /delchnl - <b>ᴇᴍᴏᴠᴇ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟ [ᴀᴅᴍɪɴ]</b>\n"
        "- /listchnl - <b>ᴠɪᴇᴡ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs [ᴀᴅᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('auto_dlt_cmd') & filters.private & admin)
async def auto_dlt_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴄᴏᴍᴮᴍᴀɴᴅs.</b>\n\n"
        "<b>ᴏᴛ ᴄᴏᴍᴮᴍᴀɴᴅs:</b></blockquote>\n"
        "- /dlt_time - sᴇᴛ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴮᴍᴇ [ᴀᴅᴍɪɴ]</b>\n"
        "- /check_dlt_time - <b>ᴄʜᴇᴄᴋ ᴅᴇʟᴇᴛᴇ ᴛɪᴮᴍᴇ [ᴀᴅᴍɪɴ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

@Bot.on_message(filters.command('links_cmd') & filters.private & admin)
async def links_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>ᴜsᴇ ᴛʜᴇsᴇ ᴄᴏᴍᴮᴍᴀɴᴅs ᴛᴏ ɢᴇᴛ sɪɴɢʟᴇ ғɪʟᴇ, ʙᴀᴛᴄʜ ᴀɴᴅ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ʟɪɴᴋs ᴄᴏᴍᴮᴍᴀɴᴅs.</b>\n\n"
        "<b>ʙᴏᴛ ᴄᴏᴍᴮᴍᴀɴᴅs:</b></blockquote>\n"
        "- /batch - <b>ᴄʀᴇᴀᴛᴇ ʟɪɴᴋs ғᴏʀ ᴮᴍᴜʟᴛɪᴘʟᴇ ᴘᴏsᴛs</b>\n"
        "- /flink - <b>ꜱᴇᴛ ᴀᴜᴛᴏ ʙᴀᴛᴄʜ ꜰᴏʀᴮᴍᴀᴛ</b>\n"
        "- /custom_batch - <b>ᴄʀᴇᴀᴛᴇ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ғʀᴏᴮᴍ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ</b>\n"
        "- /genlink - <b>ᴄʀᴇᴀᴛᴇ ʟɪɴᴋ ғᴏʀ ᴀ sɪɴɢʟᴇ ᴘᴏsᴛ</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
