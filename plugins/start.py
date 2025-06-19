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
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
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
            [InlineKeyboardButton(text="ᴏᴘᴇɴ ʟɪɴᴋ", url=short_link), InlineKeyboardButton(text="ᴛᴜᴛᴏʀɪᴀʟ", url=TUT_VID)],
            [InlineKeyboardButton(text="ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", callback_data="premium")]
        ]
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons))
    except IndexError:
        pass

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_premium = await is_premium_user(user_id)
    banned_users = await db.get_ban_users()
    
    if user_id in banned_users:
    return await message.reply_text(
        "You are Banned from using this bot.\n\nContact support if you think this is a mistake.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]])
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
            print(f"Error processing start payload: {e}")
            
        string = await decode(base64_string)
        argument = string.split("-")
        ids = []
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            except Exception as e:
                print(f"Error decoding IDs: {e}")
                return
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error decoding ID: {e}")
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
            await message.reply_text("Something went wrong!")
            print(f"Error getting messages: {e}")
            return
            
        animelord_msgs = []
        settings = await db.get_settings()
        PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)
        HIDE_CAPTION = settings.get('HIDE_CAPTION', False)
        DISABLE_CHANNEL_BUTTON = settings.get('DISABLE_CHANNEL_BUTTON', False)
        BUTTON_NAME = settings.get('BUTTON_NAME', None)
        BUTTON_LINK = settings.get('BUTTON_LINK', None)
        
        for msg in messages:
            caption = "" if HIDE_CAPTION else (
                CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                    filename=msg.document.file_name) if bool(CUSTOM_CAPTION) and bool(msg.document)
                else ("" if not msg.caption else msg.caption.html))
                
            reply_markup = None if DISABLE_CHANNEL_BUTTON or not msg.reply_markup else msg.reply_markup
            
            if BUTTON_NAME and BUTTON_LINK and not DISABLE_CHANNEL_BUTTON:
                custom_button = InlineKeyboardMarkup([[InlineKeyboardButton(BUTTON_NAME, url=BUTTON_LINK)]])
                reply_markup = custom_button if not reply_markup else InlineKeyboardMarkup(
                    reply_markup.inline_keyboard + custom_button.inline_keyboard)
                    
            try:
                copied_msg = await msg.copy(
                    chat_id=user_id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(
                    chat_id=user_id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message: {e}")
                pass
                
        auto_delete_mode = await db.get_auto_delete_mode()
        if auto_delete_mode and FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"This file will be deleted in {get_exp_time(FILE_AUTO_DELETE).lower()}.")
            await asyncio.sleep(FILE_AUTO_DELETE)
            
            for snt_msg in animelord_msgs:    
                if snt_msg:
                    try:    
                        await snt_msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {snt_msg.id}: {e}")
                        
            try:
                reload_url = f"https://t.me/{client.username}?start={message.command[1]}" if message.command and len(message.command) > 1 else None
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Get file again", url=reload_url)]]) if reload_url else None
                await notification_msg.edit(
                    "Your video/file is successfully deleted!\n\nClick below button to get your deleted video/file.",
                    reply_markup=keyboard)
            except Exception as e:
                print(f"Error updating notification: {e}")
        return

    # Original animation messages for /start command
    m = await message.reply_text("<blockquote><b>Welcome to my bot.\nHope you're doing well...</b></blockquote>")
    await asyncio.sleep(0.4)
    await m.edit_text("<blockquote><b>Checking...</b></blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote>🎊</blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote>⚡</blockquote>")
    await asyncio.sleep(0.5)
    await m.edit_text("<blockquote><b>Starting...</b></blockquote>")
    await asyncio.sleep(0.4)
    await m.delete()

    # Send sticker
    if STICKER_ID:
        m = await message.reply_sticker(STICKER_ID)
        await asyncio.sleep(1)
        await m.delete()

    # Send start message with new button layout
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Help", callback_data="help"), InlineKeyboardButton("About", callback_data="about")],
        [InlineKeyboardButton("Channels", callback_data="channels"), InlineKeyboardButton("Premium", callback_data="seeplans")]
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
        print(f"Error sending start photo: {e}")
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
    temp = await message.reply("<blockquote><b>Checking Subscription...</b></blockquote>")
    user_id = message.from_user.id
    buttons = []
    settings = await db.get_settings()
    count = 0
    
    try:
        all_channels = await db.show_channels()
        if not settings.get('FORCE_SUB_ENABLED', True) or not all_channels:
            await temp.delete()
            return await start_command(client, message)

        for total, chat_id in enumerate(all_channels, start=1):
            if await db.get_channel_temp_off(chat_id):
                continue
                
            mode = await db.get_channel_mode(chat_id)
            await message.reply_chat_action(ChatAction.TYPING)
            
            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        try:
                            data = await client.get_chat(chat_id)
                            chat_data_cache[chat_id] = data
                        except Exception as e:
                            if "USERNAME_NOT_OCCUPIED" in str(e):
                                await db.rem_channel(chat_id)
                                continue
                            else:
                                raise e

                    name = data.title

                    if mode == "on":
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None)
                        link = invite.invite_link
                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None)
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=f"{name}", url=link)])
                    count += 1
                    await temp.edit(f"<blockquote><b>Checking {count}...</b></blockquote>")
                except Exception as e:
                    continue
                    
        if count == 0:
            await temp.delete()
            return await start_command(client, message)

        try:
            buttons.append([InlineKeyboardButton(text='Check again', callback_data="check_sub")])
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
            reply_markup=InlineKeyboardMarkup(buttons))
            
    except Exception as e:
        await temp.edit(f"<blockquote><b>Error, contact developer @Mehediyt69\nReason: {e}</b></blockquote>")
        await asyncio.sleep(5)
        await temp.delete()
        return await start_command(client, message)
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
            "<blockquote><b>Usage:</b></blockquote>\n /addpremium <user_id> <time_value> <time_unit>\n\n"
            "...",
        )
        return
        
    try:
        usermega_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(usermega_id, time_value, time_unit)
        await msg.reply_text(
            f"User {usermega_id} added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration time: {expiration_time}.",
        )
        await client.send_message(
            chat_id=usermega_id,
            text=(
                f"<blockquote><b>Premium Activated!</b></blockquote>\n\n"
                f"<b>You have received premium access for {time_value} {time_unit}.</b>\n"
                f"<b>Expires in: {expiration_time}</b>"
            ))
    except ValueError:
        await msg.reply_text("<blockquote><b>Invalid input...</b></blockquote>")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")

@Bot.on_message(filters.command('remove_premium') & filters.private & admin)
async def pre_remove_user(client: Client, msg: Message):
    if len(msg.command) != 2:
        await msg.reply_text("<blockquote><b>Usage:</b></blockquote> /remove_premium user_id")
        return
        
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"<blockquote><b>User {user_id} has been removed...</b></blockquote>")
    except ValueError:
        await msg.reply_text("User id must be an integer or not available in database.")

@Bot.on_message(filters.command('premium_users') & filters.private & admin)
async def list_premium_users_command(client, message):
    from pytz import timezone
    ist = timezone("Asia/Dhaka")
    premium_users_cursor = collection.find({})
    premium_user_list = ['Active premium users in database:']
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
                f"User id: {user_id}\n"
                f"User: @{username}\n"
                f"Name: {mention}\n"
                f"Expiry: {expiry_info}")
        except Exception as e:
            premium_user_list.append(
                f"User id: {user_id}\n"
                f"Error: Unable to fetch user details ({str(e)})")
                
    if len(premium_user_list) == 1:
        await message.reply_text("Active premium users found in my database.")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

@Bot.on_message(filters.command("count") & filters.private & admin)
async def total_verify_count_cmd(client, message: Message):
    total = await db.get_total_verify_count()
    await message.reply_text(f"<blockquote><b>Total verified tokens today: {total}</b></blockquote>")

@Bot.on_message(filters.command('commands') & filters.private & admin)
async def bcmd(bot: Bot, message: Message):        
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("close", callback_data="close")]])
    await message.reply_text(text=CMD_TXT, reply_markup=reply_markup, quote=True)

@Bot.on_message(filters.command('premium_cmd') & filters.private & admin)
async def premium_cmd(bot: Bot, message: Message):
    reply_text = (
        "<blockquote><b>Use these commands to get premium users related commands.</b>\n\n"
        "<b>Other commands:</b></blockquote>\n"
        "- /addpremium - <b>Grant premium access [admin]</b>\n"
        "- /remove_premium - <b>Revoke premium access [admin]</b>\n"
        "- /premium_users - <b>List premium users [admin]</b>")
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("close", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)
