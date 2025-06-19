#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from database.db_premium import *

# Constants
STICKER_ID = "CAACAgUAAxkBAAJFeWd037UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"
BAN_SUPPORT = f"{BAN_SUPPORT}"
TUT_VID = f"{TUT_VID}"

# Debug mode - set to False in production
DEBUG = True

def debug_log(message: str):
    if DEBUG:
        print(f"DEBUG: {datetime.now()}: {message}")

async def verify_premium(user_id: int) -> bool:
    """Strict premium verification with expiration check"""
    try:
        if user_id == OWNER_ID:
            return True
            
        user_data = await collection.find_one({"user_id": user_id})
        if not user_data:
            debug_log(f"User {user_id} not premium")
            return False
            
        ist = timezone("Asia/Dhaka")
        expiration = user_data.get("expiration_timestamp")
        if not expiration:
            return False
            
        exp_time = datetime.fromisoformat(expiration).astimezone(ist)
        if datetime.now(ist) > exp_time:
            await remove_premium(user_id)
            return False
            
        return True
    except Exception as e:
        debug_log(f"Premium check error: {str(e)}")
        return False

async def create_shortlink(client: Client, base64_string: str) -> str:
    """Generate shortlink for free users"""
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}"
        return await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)
    except Exception as e:
        debug_log(f"Shortlink error: {str(e)}")
        return None

async def handle_free_user(client: Client, message: Message, base64_string: str):
    """Process file access for free users"""
    try:
        short_link = await create_shortlink(client, base64_string)
        if not short_link:
            return await message.reply_text("Failed to generate link. Please try again.")
            
        buttons = [
            [InlineKeyboardButton("🔗 Open Link", url=short_link)],
            [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")]
        ]
        
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption="🔒 Premium required for direct access\n\n"
                   "📎 Your temporary download link:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        debug_log(f"Free user error: {str(e)}")
        await message.reply_text("Please use this link (premium required for direct access):")

async def process_files(client: Client, message: Message, ids: list):
    """Send files to premium users"""
    try:
        processing_msg = await message.reply_text("🔄 Processing...")
        messages = await get_messages(client, ids)
        if not messages:
            await processing_msg.delete()
            return await message.reply_text("No files found")
            
        settings = await db.get_settings()
        protect_content = settings.get('PROTECT_CONTENT', False)
        
        for msg in messages:
            try:
                await msg.copy(
                    chat_id=message.from_user.id,
                    protect_content=protect_content
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(chat_id=message.from_user.id)
            except Exception as e:
                debug_log(f"Send error: {str(e)}")
        
        await processing_msg.delete()
        await message.reply_text("✅ Files sent successfully")
    except Exception as e:
        debug_log(f"File process error: {str(e)}")
        await message.reply_text("Failed to send files")

async def decode_file_request(client: Client, base64_string: str):
    """Decode and validate file request"""
    try:
        string = await decode(base64_string)
        if not string:
            return None
            
        parts = string.split("-")
        if len(parts) == 3:  # File range
            start = int(int(parts[1]) / abs(client.db_channel.id))
            end = int(int(parts[2]) / abs(client.db_channel.id))
            return list(range(start, end + 1)) if start <= end else list(range(start, end - 1, -1))
        elif len(parts) == 2:  # Single file
            return [int(int(parts[1]) / abs(client.db_channel.id))]
        return None
    except Exception as e:
        debug_log(f"Decode error: {str(e)}")
        return None

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    try:
        user_id = message.from_user.id
        debug_log(f"Start from {user_id}")
        
        # Check ban status
        if user_id in await db.get_ban_users():
            return await message.reply_text(
                "🚫 You are banned",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]]
                )
            )
        
        # Check subscription
        if not await is_subscribed(client, user_id):
            return await not_joined(client, message)
            
        # Add new users
        if not await db.present_user(user_id):
            await db.add_user(user_id)

        # Handle file requests
        if len(message.text.split()) > 1:
            base64_string = message.text.split()[1]
            is_premium = await verify_premium(user_id)
            
            if is_premium:
                file_ids = await decode_file_request(client, base64_string)
                if file_ids:
                    await process_files(client, message, file_ids)
                else:
                    await message.reply_text("❌ Invalid file request")
            else:
                await handle_free_user(client, message, base64_string)
        else:
            await send_welcome_message(client, message)
            
    except Exception as e:
        debug_log(f"Start error: {str(e)}")
        await message.reply_text("❌ An error occurred")

# [Keep all other existing functions below unchanged]
async def send_welcome_message(client: Client, message: Message):
    """Send welcome message and animations"""
    try:
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
    except Exception as e:
        print(f"Error with start animation: {e}")

    if STICKER_ID:
        try:
            m = await message.reply_sticker(STICKER_ID)
            await asyncio.sleep(1)
            await m.delete()
        except Exception as e:
            print(f"Error sending sticker: {e}")

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Help", callback_data="help"), 
         InlineKeyboardButton("About", callback_data="about")],
        [InlineKeyboardButton("Channels", callback_data="channels"), 
         InlineKeyboardButton("Premium", callback_data="seeplans")]
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
        await message.reply_text(
            START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name if message.from_user.last_name else "",
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup
        )

async def not_joined(client: Client, message: Message):
    """Handle users who haven't joined required channels"""
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
                    data = await client.get_chat(chat_id)
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

        buttons.append([InlineKeyboardButton(text='Check again', callback_data="check_sub")])
            
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
    """Check if user has joined required channels"""
    user_id = callback.from_user.id
    message = callback.message
    if await is_subscribed(client, user_id):
        await message.delete()
        await start_command(client, callback.message)
    else:
        await callback.answer("You still haven't joined all required channels. Please join and try again.")
        await not_joined(client, message)

@Bot.on_message(filters.command('myplan') & filters.private)
async def check_plan(client: Client, message: Message) -> None:
    """Check user's premium plan status"""
    user_id = message.from_user.id
    status_message = await check_user_plan(user_id)
    await message.reply_text(status_message)

@Bot.on_message(filters.command('addPremium') & filters.private & filters.user(ADMINS))
async def add_premium_user_command(client: Client, msg: Message) -> None:
    """Add premium user (admin only)"""
    if len(msg.command) != 4:
        await msg.reply_text(
            "<blockquote><b>Usage:</b></blockquote>\n /addpremium <user_id> <time_value> <time_unit>\n\n"
            "Example: /addpremium 123456789 1 month",
        )
        return
        
    try:
        user_id = int(msg.command[1])
        time_value = int(msg.command[2])
        time_unit = msg.command[3].lower()
        expiration_time = await add_premium(user_id, time_value, time_unit)
        await msg.reply_text(
            f"User {user_id} added as a premium user for {time_value} {time_unit}.\n"
            f"Expiration time: {expiration_time}.",
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"<blockquote><b>Premium Activated!</b></blockquote>\n\n"
                f"<b>You have received premium access for {time_value} {time_unit}.</b>\n"
                f"<b>Expires in: {expiration_time}</b>"
            ))
    except ValueError:
        await msg.reply_text("<blockquote><b>Invalid input...</b></blockquote>")
    except Exception as e:
        await msg.reply_text(f"An error occurred: {str(e)}")

@Bot.on_message(filters.command('remove_premium') & filters.private & filters.user(ADMINS))
async def pre_remove_user(client: Client, msg: Message) -> None:
    """Remove premium user (admin only)"""
    if len(msg.command) != 2:
        await msg.reply_text("<blockquote><b>Usage:</b></blockquote> /remove_premium user_id")
        return
        
    try:
        user_id = int(msg.command[1])
        await remove_premium(user_id)
        await msg.reply_text(f"<blockquote><b>User {user_id} has been removed...</b></blockquote>")
    except ValueError:
        await msg.reply_text("User id must be an integer or not available in database.")

@Bot.on_message(filters.command('premium_users') & filters.private & filters.user(ADMINS))
async def list_premium_users_command(client: Client, message: Message) -> None:
    """List all premium users (admin only)"""
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
        await message.reply_text("No active premium users found in database.")
    else:
        await message.reply_text("\n\n".join(premium_user_list), parse_mode=None)

@Bot.on_message(filters.command("count") & filters.private & filters.user(ADMINS))
async def total_verify_count_cmd(client: Client, message: Message) -> None:
    """Show verification count (admin only)"""
    total = await db.get_total_verify_count()
    await message.reply_text(f"<blockquote><b>Total verified tokens today: {total}</b></blockquote>")

@Bot.on_message(filters.command('commands') & filters.private & filters.user(ADMINS))
async def bcmd(client: Client, message: Message) -> None:        
    """Show available commands (admin only)"""
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("close", callback_data="close")]])
    await message.reply_text(text=CMD_TXT, reply_markup=reply_markup, quote=True)

@Bot.on_message(filters.command('premium_cmd') & filters.private & filters.user(ADMINS))
async def premium_cmd(client: Client, message: Message) -> None:
    """Show premium commands (admin only)"""
    reply_text = (
        "<blockquote><b>Use these commands to get premium users related commands.</b>\n\n"
        "<b>Other commands:</b></blockquote>\n"
        "- /addpremium - <b>Grant premium access [admin]</b>\n"
        "- /remove_premium - <b>Revoke premium access [admin]</b>\n"
        "- /premium_users - <b>List premium users [admin]</b>")
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("close", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)
