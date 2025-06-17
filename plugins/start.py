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

# Define sticker
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"

BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

# Cache for chat data to improve performance
chat_data_cache = {}

async def short_url(client: Client, message: Message, base64_string):
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}"
        short_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)
        buttons = [
            [InlineKeyboardButton(text="бҙ…ЙӘбҙЎЙҙКҹЙӘбҙҖбҙ…", url=short_link), InlineKeyboardButton(text="бҙӣбҙңбҙӣЙӘКҖЙӘбҙҖКҹ", url=TUT_VID)],
            [InlineKeyboardButton(text="бҙҳКҖбҙҮбҙҚЙӘбҙңбҙҚ", callback_data="premium")]
        ]
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except IndexError:
        pass

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_premium = await is_premium_user(user_id)
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "КҸЙӘбҙң бҙҖКҖбҙҮ КҷбҙҖЙҙЙҙбҙҮбҙ… Т“КҖЙӘбҙҚ бҙңsЙӘЙҙЙў бҙӣКңЙӘs КҷЙӘбҙӣ.\n\nбҙ„ЙӘЙҙбҙӣбҙҖбҙ„бҙӣ sбҙңбҙҳбҙҳЙӘКҖбҙӣ ЙӘТ“ КҸЙӘбҙң бҙӣКңЙӘЙҙбҙӢ бҙӣКңЙӘs ЙӘs бҙҖ бҙҚЙӘsбҙӣбҙҖбҙӢбҙҮ.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("бҙ„ЙӘЙҙбҙӣбҙҖбҙ„бҙӣ sбҙңбҙҳбҙҳЙӘКҖбҙӣ", url=BAN_SUPPORT)]])
        )
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)
    FILE_AUTO_DELETE = await db.get_del_timer()
    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except:
            pass

    text = message.text
    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            base64_string = basic[6:-1] if basic.startswith("yu3elk") else basic
            if not is_premium and user_id != OWNER_ID and not basic.startswith("yu3elk"):
                await short_url(client, message, base64_string)
                return
        except Exception as e:
            print(f"бҙҮКҖКҖЙӘКҖ бҙҳКҖЙӘбҙ„бҙҮssЙӘЙҙЙў sбҙӣбҙҖКҖбҙӣ бҙҳбҙҖКҸКҹЙӘбҙҖбҙ…: {e}")
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"бҙҮКҖКҖЙӘКҖ бҙ…бҙҮбҙ„ЙӘбҙ…ЙӘЙҙЙў ЙӘбҙ…s: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"бҙҮКҖКҖЙӘКҖ бҙ…бҙҮбҙ„ЙӘбҙ…ЙӘЙҙЙў ЙӘбҙ…: {e}")
                return
        # New animation messages for file request
        m = await message.reply_text("<blockquote><b>Checking...</b></blockquote>")
        await asyncio.sleep(0.4)
        await m.edit_text("<blockquote><b>Getting your files...</b></blockquote>")
        await asyncio.sleep(0.5)
        await m.delete()
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("sЙӘбҙҚбҙҮбҙӣКңЙӘЙҙЙў бҙЎбҙҮЙҙбҙӣ бҙЎКҖЙӘЙҙЙў!")
            print(f"бҙҮКҖКҖЙӘКҖ ЙўбҙҮбҙӣбҙӣЙӘЙҙЙў бҙҚбҙҮssбҙҖЙўбҙҮs: {e}")
            return
        animelord_msgs = []
        # Load settings dynamically before copying messages
        settings = await db.get_settings()
        PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)
        HIDE_CAPTION = settings.get('HIDE_CAPTION', False)
        DISABLE_CHANNEL_BUTTON = settings.get('DISABLE_CHANNEL_BUTTON', False)
        BUTTON_NAME = settings.get('BUTTON_NAME', None)
        BUTTON_LINK = settings.get('BUTTON_LINK', None)
        print(f"Copying message with PROTECT_CONTENT={PROTECT_CONTENT}, HIDE_CAPTION={HIDE_CAPTION}, DISABLE_CHANNEL_BUTTON={DISABLE_CHANNEL_BUTTON}")
        for msg in messages:
            caption = "" if HIDE_CAPTION else (
                CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                      filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                else ("" if not msg.caption else msg.caption.html))
            reply_markup = None if DISABLE_CHANNEL_BUTTON or not msg.reply_markup else msg.reply_markup
            # Add custom button if BUTTON_NAME and BUTTON_LINK are set
            if BUTTON_NAME and BUTTON_LINK and not DISABLE_CHANNEL_BUTTON:
                custom_button = InlineKeyboardMarkup([[InlineKeyboardButton(BUTTON_NAME, url=BUTTON_LINK)]])
                reply_markup = custom_button if not reply_markup else InlineKeyboardMarkup(
                    reply_markup.inline_keyboard + custom_button.inline_keyboard
                )
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
                print(f"Т“бҙҖЙӘКҹбҙҮбҙ… бҙӣЙӘ sбҙҮЙҙбҙ… бҙҚбҙҮssбҙҖЙўбҙҮ: {e}")
                pass
        auto_delete_mode = await db.get_auto_delete_mode()  # Check auto-delete mode
        if auto_delete_mode and FILE_AUTO_DELETE > 0:  # Only proceed if mode is enabled and timer is positive
            notification_msg = await message.reply(
                f"бҙӣКңЙӘs Т“ЙӘКҹбҙҮ бҙЎЙӘКҹКҹ КҷбҙҮ бҙ…бҙҮКҹбҙҮбҙӣбҙҮбҙ… ЙӘЙҙ {get_exp_time(FILE_AUTO_DELETE).lower()}."
            )
            await asyncio.sleep(FILE_AUTO_DELETE)
            for snt_msg in animelord_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"бҙҮКҖКҖЙӘКҖ бҙ…бҙҮКҹбҙҮбҙӣЙӘЙҙЙў бҙҚбҙҮssбҙҖЙўбҙҮ {snt_msg.id}: {e}")
            try:
                reload_url = f"https://t.me/{client.username}?start={message.command[1]}" if message.command and len(message.command) > 1 else None
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ЙўбҙҮбҙӣ Т“ЙӘКҹбҙҮ бҙҖЙўбҙҖЙӘЙҙ!", url=reload_url)]]) if reload_url else None
                await notification_msg.edit(
                    "КҸЙӘбҙңКҖ бҙ ЙӘбҙ…бҙҮЙӘ/Т“ЙӘКҹбҙҮ ЙӘs sбҙңбҙ„бҙ„бҙҮssТ“бҙңКҹКҹКҸ бҙ…бҙҮКҹбҙҮбҙӣбҙҮбҙ…!\n\nбҙ„КҹЙӘбҙ„бҙӢ КҷбҙҮКҹЙӘбҙЎ КҷбҙңбҙӣбҙӣЙӘЙҙ бҙӣЙӘ ЙўбҙҮбҙӣ КҸЙӘбҙңКҖ бҙ…бҙҮКҹбҙҮбҙӣбҙҮбҙ… бҙ ЙӘбҙ…бҙҮЙӘ/Т“ЙӘКҹбҙҮ.",
                    reply_markup=keyboard
                )
            except Exception as e:
                print(f"бҙҮКҖКҖЙӘКҖ бҙңбҙӘбҙ…бҙҖбҙӣЙӘЙҙЙў ЙҙЙӘбҙӣЙӘТ“ЙӘбҙ„бҙҖбҙӣЙӘЙӘЙҙ: {e}")
        return

    # Original animation messages for /start command
    m = await message.reply_text("<blockquote><b>бҙЎбҙҮКҹбҙ„ЙӘбҙҚбҙҮ бҙӣЙӘ бҙҚКҸ КҷЙӘбҙӣ.\nКңЙӘбҙӘбҙҮ КҸЙӘбҙң'КҖбҙҮ бҙ…ЙӘЙӘЙҙЙў бҙЎбҙҮКҹКҹ...</b></blockquote>")
    await asyncio.sleep(0.4)
    await m.edit_text("<blockquote><b>бҙ„КңбҙҮбҙ„бҙӢЙӘЙҙЙў...</b></blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote>рҹҺҠ</blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote>вҡЎ</blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote><b>sбҙӣбҙҖКҖбҙӣЙӘЙҙЙў...</b></blockquote>")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker
    if STICKER_ID:
        m = await message.reply_sticker(STICKER_ID)
        await asyncio.sleep(1)
        await m.delete()

    # Send start message
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("бҙҚЙӘКҖбҙҮ бҙ„КңбҙҖЙҙЙҙбҙҮКҹs", url="https://t.me/Anime_Lord_List")],
        [InlineKeyboardButton("бҙҖКҷЙӘбҙңбҙӣ", callback_data="about"), InlineKeyboardButton("КңбҙҮКҹбҙӘ", callback_data="help")]
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
            reply_markup=reply_markup
        )
    except Exception as e:
        print(f"бҙҮКҖКҖЙӘКҖ sбҙҮЙҙбҙ…ЙӘЙҙЙў sбҙӣбҙҖКҖбҙӣ бҙӘКңЙӘбҙӣЙӘ: {e}")
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

# [Rest of the file remains unchanged...]
    except Exception as e:
        print(f"бҙҮКҖКҖЙӘКҖ sбҙҮЙҙбҙ…ЙӘЙҙЙў sбҙӣбҙҖКҖбҙӣ бҙӘКңЙӘбҙӣЙӘ: {e}")
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
    temp = await message.reply("<blockquote><b>бҙ„КңбҙҮбҙ„бҙӢЙӘЙҙЙў sбҙңКҷsбҙ„КҖЙӘбҙӘбҙӣЙӘЙӘЙҙ...</b></blockquote>")
    user_id = message.from_user.id
    buttons = []
    settings = await db.get_settings()
    count = 0
    try:
        all_channels = await db.show_channels()
        if not settings.get('FORCE_SUB_ENABLED', True) or not all_channels:
            await temp.delete()
            return await start_command(client, message)  # Bypass if force-sub disabled or no channels

        for total, chat_id in enumerate(all_channels, start=1):
            if await db.get_channel_temp_off(chat_id):  # Skip channels with temp_off=True
                continue
            mode = await db.get_channel_mode(chat_id)
            await message.reply_chat_action(ChatAction.TYPING)
            if not await is_sub(client, user_id, chat_id):
                try:
                    # Cache chat info
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        try:
                            data = await client.get_chat(chat_id)
                            chat_data_cache[chat_id] = data
                        except Exception as e:
                            logger.error(f"Failed to fetch chat {chat_id}: {e}")
                            if "USERNAME_NOT_OCCUPIED" in str(e):
                                await db.rem_channel(chat_id)  # Remove invalid channel from database
                                logger.info(f"Removed invalid channel {chat_id} from database")
                                continue
                            else:
                                raise e

                    name = data.title

                    # Generate proper invite link based on the mode
                    if mode == "on":
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=f"{name}", url=link)])
                    count += 1
                    await temp.edit(f"<blockquote><b>бҙ„КңбҙҮбҙ„бҙӢЙӘЙҙЙў {count}...</b></blockquote>")
                except Exception as e:
                    logger.error(f"Error with chat {chat_id}: {e}")
                    continue  # Skip invalid channels instead of stopping
        if count == 0:  # All required channels are subscribed
            await temp.delete()
            return await start_command(client, message)

        try:
            buttons.append([InlineKeyboardButton(text='бҙ„КңбҙҮбҙ„бҙӢ бҙҖЙўбҙҖЙӘЙҙ', callback_data="check_sub")])
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
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Final error in not_joined: {e}")
        await temp.edit(f"<blockquote><b>бҙҮКҖКҖЙӘКҖ, бҙ„ЙӘЙҙбҙӣбҙҖбҙ„бҙӣ бҙ…бҙҮбҙ бҙҮКҹЙӘбҙӘбҙҮКҖ @Mehediyt69\nКҖбҙҮбҙҖsЙӘЙҙ: {e}</b></blockquote>")
        await asyncio.sleep(5)  # Show error for 5 seconds
        await temp.delete()
        return await start_command(client, message)  # Proceed to start_command even if error occurs
    finally:
        await temp.delete()

@Bot.on_callback_query(filters.regex(r"^check_sub"))
async def check_sub_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    message = callback.message
    if await is_subscribed(client, user_id):
        await message.delete()
        await start_command(client, callback.message)
    else:
        await callback.answer("You still haven't joined all required channels. Please join and try again.")
        await not_joined(client, message)

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message):
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply_text(status_message)

@Bot.on_message(filters.command('addPremium') & filters.private & admin)
async def add_premium_user_command(client, msg):
    if len(msg.command) != 4:
        await msg.reply_text(
            "<blockquote><b>бҙңsбҙҖЙўбҙҮ:</b></blockquote>\n /addpremium <user_id> <time_value> <time_unit>\n\n"
            "...",  # trimmed for brevity
        )
        return
    try:
        usermega_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(usermega_id, time_value, time_unit)
        await msg.reply_text(
            f"бҙңsбҙҮКҖ {usermega_id} бҙҖбҙ…бҙ…бҙҮбҙ… бҙҖs бҙҖ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙңsбҙҮКҖ Т“ЙӘКҖ {time_value} {time_unit}.\n"
            f"бҙҮxбҙӘЙӘКҖбҙҖбҙӣЙӘЙӘЙҙ бҙӣЙӘбҙҚбҙҮ: {expiration_time}.",
        )
        await client.send_message(
            chat_id=usermega_id,
            text=(
                f"<blockquote><b>бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙҖбҙ„бҙӣЙӘбҙ бҙҖбҙӣбҙҮбҙ…!</b></blockquote>\n\n"
                f"<b>YЙӘбҙң КңбҙҖбҙ бҙҮ КҖбҙҮбҙ„бҙҮЙӘбҙ бҙҮбҙ… бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙҖбҙ„бҙ„бҙҮss Т“ЙӘКҖ {time_value} {time_unit}.</b>\n"
                f"<b>бҙҮxбҙӘЙӘКҖбҙҮs ЙӘЙҙ: {expiration_time}</b>"
            )
        )
    except ValueError:
        await msg.reply_text("<blockquote><b>ЙӘЙҙбҙ бҙҖКҹЙӘбҙ… ЙӘЙҙбҙҳбҙңбҙӣ...</b></blockquote>")
    except Exception as e:
        await msg.reply_text(f"бҙҖЙҙ бҙҮКҖКҖЙӘКҖ ЙӘбҙ„бҙ„бҙңКҖКҖбҙҮбҙ…: {str(e)}")

@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("<blockquote><b>бҙңsбҙҖЙўбҙҮ:</b></blockquote> /remove_premium user_id")
        return
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"<blockquote><b>бҙңsбҙҮКҖ {user_id} КңбҙҖs КҷбҙҮбҙҮЙҙ КҖбҙҮбҙҚЙӘбҙ бҙҮбҙ….</b></blockquote>")
    except ValueError:
        await msg.reply_text("бҙңsбҙҮКҖ ЙӘбҙ… бҙҚбҙңsбҙӣ КҷбҙҮ бҙҖЙҙ ЙӘЙҙбҙӣбҙҮЙўбҙҮКҖ ЙӘКҖ ЙҙЙӘбҙӣ бҙҖбҙ бҙҖЙӘКҹбҙҖКҷКҹбҙҮ ЙӘЙҙ бҙ…бҙҖбҙӣбҙҖКҷбҙҖsбҙҮ.")

@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    from pytz import timezone
    ist = timezone("Asia/Dhaka")
    premium_users_cursor = collection.find({})
    premium_user_list = ['бҙҖбҙ„бҙӣЙӘбҙ бҙҮ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙңsбҙҮКҖs ЙӘЙҙ бҙ…бҙҖбҙӣбҙҖКҷбҙҖsбҙҮ:']
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
                f"бҙңsбҙҮКҖ ЙӘбҙ…: {user_id}\n"
                f"бҙңsбҙҮКҖ: @{username}\n"
                f"ЙҙбҙҖбҙҚбҙҮ: {mention}\n"
                f"бҙҮxбҙӘЙӘКҖКҸ: {expiry_info}"
            )
        except Exception as e:
            premium_user_list.append(
                f"бҙңsбҙҮКҖ ЙӘбҙ…: {user_id}\n"
                f"бҙҮКҖКҖЙӘКҖ: бҙңЙҙбҙҖКҷКҹбҙҮ бҙӣЙӘ Т“бҙҮбҙӣбҙ„Кң бҙңsбҙҮКҖ бҙ…бҙҮбҙӣбҙҖЙӘКҹs ({str(e)})"
            )
    if len(premium_user_list) == 1:
        await message.reply_text("ЙҙЙӘ бҙҖбҙ„бҙӣЙӘбҙ бҙҮ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙңsбҙҮКҖs Т“ЙӘбҙңЙҙбҙ… ЙӘЙҙ бҙҚКҸ бҙ…бҙҖбҙӣбҙҖКҷбҙҖsбҙҮ.")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"<blockquote><b>бҙӣЙӘбҙӣбҙҖКҹ бҙ бҙҮКҖЙӘТ“ЙӘбҙҮбҙ… бҙӣЙӘбҙӢбҙҮЙҙs бҙӣЙӘбҙ…бҙҖКҸ: {total}</b></blockquote>")

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("бҙ„КҹЙӘsбҙҮ", callback_data="close")]])
    await message.reply_text(text=CMD_TXT, reply_markup=reply_markup, quote=True)

@Bot.on_message(filters.command('premium_cmd') & filters.private & admin)
async def premium_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>бҙңsбҙҮ бҙӣКңбҙҮsбҙҮ бҙ„ЙӘбҙҚбҙҚбҙҖЙҙбҙ…s бҙӣЙӘ ЙўбҙҮбҙӣ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙңsбҙҮКҖs КҖбҙҮКҹбҙҖбҙӣбҙҮбҙ… бҙ„ЙӘбҙҚбҙҚбҙҖЙҙбҙ…s.</b>\n\n"
        "<b>ЙӘбҙӣКңбҙҮКҖ бҙ„ЙӘбҙҚбҙҚбҙҖЙҙбҙ…s:</b></blockquote>\n"
        "- /addpremium - <b>ЙўКҖбҙҖЙҙбҙӣ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙҖбҙ„бҙ„бҙҮss [бҙҖбҙ…бҙҚЙӘЙҙ]</b>\n"
        "- /remove_premium - <b>КҖбҙҮбҙ ЙӘбҙӢбҙҮ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙҖбҙ„бҙ„бҙҮss [бҙҖбҙ…бҙҚЙӘЙҙ]</b>\n"
        "- /premium_users - <b>КҹЙӘsбҙӣ бҙӘКҖбҙҮбҙҚЙӘбҙңбҙҚ бҙңsбҙҮКҖs [бҙҖбҙ…бҙҳЙӘЙҙ]</b>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("бҙ„КҹЙӘsбҙҮ", callback_data="close")]])
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
