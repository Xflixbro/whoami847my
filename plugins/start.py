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

# Cache for chat data
chat_data_cache = {}

async def short_url(client: Client, message: Message, base64_string: str) -> None:
    """Generate and send short URL for file access"""
    try:
        prem_link = f"https://t.me/{client.username}?start=yu3elk{base64_string}"
        short_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, prem_link)
        buttons = [
            [InlineKeyboardButton("ᴏᴘᴇɴ ʟɪɴᴋ", url=short_link), 
             InlineKeyboardButton("ᴛᴜᴛᴏʀɪᴀʟ", url=TUT_VID)],
            [InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", callback_data="seeplans")]
        ]
        await message.reply_photo(
            photo=SHORTENER_PIC,
            caption=SHORT_MSG.format(),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error in short_url: {e}")
        await message.reply_text("Failed to generate short URL. Please try again later.")

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message) -> None:
    """Handle /start command with comprehensive error handling"""
    try:
        user_id = message.from_user.id
        is_premium = await is_premium_user(user_id)
        banned_users = await db.get_ban_users()
        
        if user_id in banned_users:
            return await message.reply_text(
                "You are banned from using this bot.\n\nContact support if you think this is a mistake.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]])
            )
        
        if not await is_subscribed(client, user_id):
            return await not_joined(client, message)
            
        FILE_AUTO_DELETE = await db.get_del_timer()
        
        if not await db.present_user(user_id):
            try:
                await db.add_user(user_id)
            except Exception as e:
                print(f"Error adding user to database: {e}")

        text = message.text
        if len(text.split()) > 1:
            await handle_file_request(client, message, text, is_premium, user_id)
        else:
            await send_welcome_message(client, message)
    except Exception as e:
        print(f"Critical error in start_command: {e}")
        await message.reply_text("An error occurred. Please try again later.")

async def handle_file_request(client: Client, message: Message, text: str, is_premium: bool, user_id: int) -> None:
    """Handle file requests from start command with enhanced premium checks"""
    try:
        basic = text.split(" ", 1)[1]
        base64_string = basic[6:] if basic.startswith("yu3elk") else basic
        
        # Enhanced premium verification with expiration check
        current_premium_status = await is_premium_user(user_id)
        if not current_premium_status and user_id != OWNER_ID:
            await message.reply_text("This file is only available for premium users.")
            await short_url(client, message, base64_string)
            return
            
        string = await decode(base64_string)
        argument = string.split("-")
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
                ids = list(range(int(start), int(end) + 1)) if start <= end else list(range(int(start), int(end) - 1, -1))
            except (ValueError, ZeroDivisionError, AttributeError) as e:
                print(f"Error decoding range IDs: {e}")
                return await message.reply_text("Invalid file range format")
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except (ValueError, ZeroDivisionError, AttributeError) as e:
                print(f"Error decoding single ID: {e}")
                return await message.reply_text("Invalid file ID format")
        else:
            return await message.reply_text("Invalid request format")
        
        await process_file_request(client, message, ids)
    except Exception as e:
        print(f"Error handling file request: {e}")
        await message.reply_text("Failed to process your request. Please try again.")

async def process_file_request(client: Client, message: Message, ids: list) -> None:
    """Process and send requested files"""
    try:
        m = await message.reply_text("<blockquote><b>Checking...</b></blockquote>")
        await asyncio.sleep(0.4)
        await m.edit_text("<blockquote><b>Getting your files...</b></blockquote>")
        await asyncio.sleep(0.5)
        await m.delete()
    except Exception as e:
        print(f"Error with animation messages: {e}")
    
    try:
        messages = await get_messages(client, ids)
    except Exception as e:
        print(f"Error getting messages: {e}")
        return await message.reply_text("Failed to retrieve files. Please try again later.")
        
    animelord_msgs = []
    try:
        settings = await db.get_settings()
        PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)
        HIDE_CAPTION = settings.get('HIDE_CAPTION', False)
        DISABLE_CHANNEL_BUTTON = settings.get('DISABLE_CHANNEL_BUTTON', False)
        BUTTON_NAME = settings.get('BUTTON_NAME', None)
        BUTTON_LINK = settings.get('BUTTON_LINK', None)
    except Exception as e:
        print(f"Error getting settings: {e}")
        PROTECT_CONTENT = False
        HIDE_CAPTION = False
        DISABLE_CHANNEL_BUTTON = False
        BUTTON_NAME = None
        BUTTON_LINK = None
    
    for msg in messages:
        try:
            caption = "" if HIDE_CAPTION else (
                CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                ) if bool(CUSTOM_CAPTION) and bool(msg.document)
                else ("" if not msg.caption else msg.caption.html))
                
            reply_markup = None if DISABLE_CHANNEL_BUTTON or not msg.reply_markup else msg.reply_markup
            
            if BUTTON_NAME and BUTTON_LINK and not DISABLE_CHANNEL_BUTTON:
                custom_button = InlineKeyboardMarkup([[InlineKeyboardButton(BUTTON_NAME, url=BUTTON_LINK)]])
                reply_markup = custom_button if not reply_markup else InlineKeyboardMarkup(
                    reply_markup.inline_keyboard + custom_button.inline_keyboard)
                    
            try:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id, 
                    caption=caption, 
                    parse_mode=ParseMode.HTML, 
                    reply_markup=reply_markup, 
                    protect_content=PROTECT_CONTENT)
                animelord_msgs.append(copied_msg)
            except Exception as e:
                print(f"Failed to send message {msg.id}: {e}")
        except Exception as e:
            print(f"Error processing message {msg.id if msg else 'unknown'}: {e}")
            
    await handle_auto_delete(client, message, animelord_msgs)

async def handle_auto_delete(client: Client, message: Message, sent_messages: list) -> None:
    """Handle auto-deletion of sent files if enabled"""
    try:
        auto_delete_mode = await db.get_auto_delete_mode()
        FILE_AUTO_DELETE = await db.get_del_timer()
        
        if auto_delete_mode and FILE_AUTO_DELETE > 0:
            notification_msg = await message.reply(
                f"This file will be deleted in {get_exp_time(FILE_AUTO_DELETE).lower()}.")
            await asyncio.sleep(FILE_AUTO_DELETE)
            
            for msg in sent_messages:    
                if msg:
                    try:    
                        await msg.delete()  
                    except Exception as e:
                        print(f"Error deleting message {msg.id}: {e}")
                        
            try:
                reload_url = f"https://t.me/{client.username}?start={message.command[1]}" if message.command and len(message.command) > 1 else None
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Get file again", url=reload_url)]]) if reload_url else None
                await notification_msg.edit(
                    "Your video/file is successfully deleted!\n\nClick below button to get your deleted video/file.",
                    reply_markup=keyboard)
            except Exception as e:
                print(f"Error updating notification: {e}")
    except Exception as e:
        print(f"Error in auto-delete process: {e}")

async def send_welcome_message(client: Client, message: Message) -> None:
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
        try:
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
        except Exception as e:
            print(f"Fallback start message failed: {e}")

async def not_joined(client: Client, message: Message) -> None:
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
async def check_sub_callback(client: Client, callback: CallbackQuery) -> None:
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
    """Check user's premium plan status with expiration info"""
    user_id = message.from_user.id
    user_data = await collection.find_one({"user_id": user_id})
    
    if not user_data:
        await message.reply_text("You don't have an active premium subscription.")
        return
    
    try:
        expiration_time = datetime.fromisoformat(user_data["expiration_timestamp"])
        current_time = datetime.now()
        remaining_time = expiration_time - current_time
        
        if remaining_time.total_seconds() <= 0:
            await collection.delete_one({"user_id": user_id})
            await message.reply_text("Your premium subscription has expired.")
            return
        
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        status_message = (
            "✨ <b>Your Premium Status</b> ✨\n\n"
            f"• <b>Plan Active:</b> Yes\n"
            f"• <b>Expires in:</b> {days} days, {hours} hours\n"
            f"• <b>Expiration Date:</b> {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await message.reply_text(status_message)
    except Exception as e:
        print(f"Error checking premium plan: {e}")
        await message.reply_text("Error checking your premium status. Please try again later.")

@Bot.on_message(filters.command('addPremium') & filters.private & filters.user(ADMINS))
async def add_premium_user_command(client: Client, msg: Message) -> None:
    """Add premium user (admin only) with enhanced validation"""
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
        
        # Validate time unit
        valid_units = ['minute', 'hour', 'day', 'week', 'month', 'year']
        if time_unit not in valid_units:
            await msg.reply_text(
                f"Invalid time unit. Please use one of: {', '.join(valid_units)}"
            )
            return
            
        # Validate time value
        if time_value <= 0:
            await msg.reply_text("Time value must be positive")
            return
            
        expiration_time = await add_premium(user_id, time_value, time_unit)
        await msg.reply_text(
            f"✅ User {user_id} added as a premium user for {time_value} {time_unit}(s).\n"
            f"⏳ Expiration time: {expiration_time}."
        )
        await client.send_message(
            chat_id=user_id,
            text=(
                f"🎉 <b>Premium Activated!</b> 🎉\n\n"
                f"✨ <b>You have received premium access for {time_value} {time_unit}(s).</b>\n"
                f"⏳ <b>Expires on: {expiration_time}</b>\n\n"
                f"Thank you for supporting us!"
            ))
    except ValueError:
        await msg.reply_text("<blockquote><b>Invalid input. User ID and time must be numbers.</b></blockquote>")
    except Exception as e:
        await msg.reply_text(f"❌ An error occurred: {str(e)}")

@Bot.on_message(filters.command('remove_premium') & filters.private & filters.user(ADMINS))
async def pre_remove_user(client: Client, msg: Message) -> None:
    """Remove premium user (admin only) with confirmation"""
    if len(msg.command) != 2:
        await msg.reply_text("<blockquote><b>Usage:</b></blockquote> /remove_premium user_id")
        return
        
    try:
        user_id = int(msg.command[1])
        user_data = await collection.find_one({"user_id": user_id})
        
        if not user_data:
            await msg.reply_text(f"User {user_id} is not a premium user.")
            return
            
        await remove_premium(user_id)
        await msg.reply_text(f"✅ User {user_id} has been removed from premium access.")
        
        # Notify the user
        try:
            await client.send_message(
                chat_id=user_id,
                text="⚠️ <b>Your premium access has been revoked by admin.</b>"
            )
        except Exception:
            pass
    except ValueError:
        await msg.reply_text("❌ User id must be an integer.")

@Bot.on_message(filters.command('premium_users') & filters.private & filters.user(ADMINS))
async def list_premium_users_command(client: Client, message: Message) -> None:
    """List all premium users (admin only) with enhanced formatting"""
    from pytz import timezone
    ist = timezone("Asia/Dhaka")
    current_time = datetime.now(ist)
    active_users = 0
    expired_users = 0
    
    premium_user_list = ['<b>🛡️ Active Premium Users</b>\n']
    
    async for user in collection.find({}):
        try:
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"]).astimezone(ist)
            remaining_time = expiration_time - current_time
            
            # Cleanup expired users
            if remaining_time.total_seconds() <= 0:
                await collection.delete_one({"_id": user["_id"]})
                expired_users += 1
                continue
                
            active_users += 1
            user_info = await client.get_users(user["user_id"])
            username = f"@{user_info.username}" if user_info.username else "No Username"
            mention = user_info.mention
            
            days = remaining_time.days
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            premium_user_list.append(
                f"┌ <b>User:</b> {mention}\n"
                f"├ <b>ID:</b> <code>{user['user_id']}</code>\n"
                f"├ <b>Username:</b> {username}\n"
                f"├ <b>Expires in:</b> {days}d {hours}h\n"
                f"└ <b>Expiry:</b> {expiration_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"────────────────────"
            )
        except Exception as e:
            premium_user_list.append(
                f"┌ <b>User ID:</b> <code>{user['user_id']}</code>\n"
                f"└ <b>Error:</b> {str(e)[:50]}...\n"
                f"────────────────────"
            )
    
    stats = (
        f"\n<b>📊 Premium Stats</b>\n"
        f"• Active Users: {active_users}\n"
        f"• Expired/Cleaned: {expired_users}\n"
        f"• Total in DB: {active_users + expired_users}"
    )
    
    if active_users == 0:
        await message.reply_text("No active premium users found in database." + stats)
    else:
        await message.reply_text(
            "\n".join(premium_user_list) + stats,
            parse_mode=ParseMode.HTML
        )

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
        "<blockquote><b>🌟 Premium Management Commands 🌟</b>\n\n"
        "<b>User Management:</b>\n"
        "- /addpremium user_id time_value unit - <b>Grant premium access</b>\n"
        "- /remove_premium user_id - <b>Revoke premium access</b>\n\n"
        "<b>Information:</b>\n"
        "- /premium_users - <b>List all premium users</b>\n"
        "- /myplan - <b>Check your premium status</b></blockquote>"
    )
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("close", callback_data="close")]])
    await message.reply_text(reply_text, reply_markup=reply_markup)

# Premium user cleanup task
async def cleanup_expired_premium_users():
    """Periodically remove expired premium users from database"""
    while True:
        try:
            current_time = datetime.now()
            result = await collection.delete_many({
                "expiration_timestamp": {"$lt": current_time.isoformat()}
            })
            if result.deleted_count > 0:
                print(f"Cleaned up {result.deleted_count} expired premium users")
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Error in premium user cleanup: {e}")
            await asyncio.sleep(600)

# Start the cleanup task when bot starts
asyncio.create_task(cleanup_expired_premium_users())
