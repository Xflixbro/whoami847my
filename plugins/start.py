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
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import Bot
from config import *
from helper_func import encode, get_message_id, subscribed
from database.database import db
from database.db_premium import is_premium_user  # Import for premium user check

# Set MESSAGE_EFFECT_IDS for random message effects
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    if not await db.present_user(id):
        await db.add_user(id)
        await client.send_message(
            chat_id=LOG_CHANNEL,
            text=f"#NEW_USER: \n\nNew User [{message.from_user.first_name}]({id}) started @{client.name} !!"
        )
    
    ban_status = await db.ban_user_exist(id)
    if ban_status:
        await message.reply_text("You are banned from using this bot. Contact the bot owner for more info.")
        return

    verify_status = await db.get_verify_status(id)
    is_verified = verify_status['is_verified']

    if not is_verified:
        token = await generate_token(id)
        link = f"https://t.me/{client.username}?start={token}"
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Verify", url=link),
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_verify")
                ]
            ]
        )
        await message.reply_text(
            text=VERIFY_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return

    if len(message.command) > 1:
        identifier = message.command[1]
        if identifier.startswith("verify_"):
            token = identifier.split("_")[1]
            verify_status = await db.get_verify_status(id)
            if verify_status['verify_token'] == token:
                await db.update_verify_status(id, is_verified=True, verified_time=int(time.time()))
                if verify_status['link']:
                    try:
                        m = await client.get_messages(AUTH_CHANNEL, int(verify_status['link']))
                        await m.delete()
                    except:
                        pass
                await db.update_verify_status(id, link="")
                reply_markup = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🏠 Home", callback_data="start")]
                    ]
                )
                await message.reply_text(
                    text="Verification successful! You can now use the bot.",
                    reply_markup=reply_markup
                )
                return
        else:
            data = await decode(identifier)
            if data.startswith("file_"):
                msg_id = int(data.split("_")[1])
                message_id = await get_message_id(client, message)
                if message_id != 0:
                    msg_id = message_id
                try:
                    msg = await client.get_messages(client.db_channel.id, msg_id)
                except:
                    await message.reply_text("This file has been deleted from my database!")
                    return
                caption = msg.caption or ""
                settings = await db.get_settings()
                if settings['HIDE_CAPTION']:
                    caption = ""
                elif settings['BUTTON_NAME'] and settings['BUTTON_LINK']:
                    reply_markup = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(settings['BUTTON_NAME'], url=settings['BUTTON_LINK'])]
                        ]
                    )
                else:
                    reply_markup = None
                if settings['PROTECT_CONTENT']:
                    await msg.copy(
                        chat_id=message.chat.id,
                        caption=caption,
                        reply_markup=reply_markup,
                        protect_content=True
                    )
                else:
                    await msg.copy(
                        chat_id=message.chat.id,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                auto_delete_mode = await db.get_auto_delete_mode()
                if auto_delete_mode:
                    del_timer = await db.get_del_timer()
                    await asyncio.sleep(del_timer)
                    await message.delete()
                return

    # Send start message with random effect
    selected_effect = random.choice(MESSAGE_EFFECT_IDS)
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔍 About", callback_data="about"),
                InlineKeyboardButton("📚 Help", callback_data="help")
            ],
            [
                InlineKeyboardButton("🌐 Channel", url=f"https://t.me/{UPDATES_CHANNEL[1:]}"),
                InlineKeyboardButton("👥 Group", url=f"https://t.me/{SUPPORT_GROUP[1:]}")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close")
            ]
        ]
    )
    await message.reply_photo(
        photo=START_PIC,
        caption=START_TXT.format(
            user=message.from_user.mention,
            bot=client.mention
        ),
        reply_markup=reply_markup,
        message_effect_id=selected_effect
    )

@Bot.on_message(filters.command('logs') & filters.user(OWNER_ID))
async def log_file(client: Client, message: Message):
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Bot.on_message(filters.command('users') & filters.user(OWNER_ID))
async def get_users(client: Client, message: Message):
    msg = await message.reply_text("Getting users...")
    users = await db.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.command('stats') & filters.user(OWNER_ID))
async def get_stats(client: Client, message: Message):
    msg = await message.reply_text("Getting stats...")
    users = await db.full_userbase()
    verify_count = await db.get_total_verify_count()
    await msg.edit(f"Total Users: {len(users)}\nTotal Verifications: {verify_count}")

@Bot.on_callback_query(filters.regex(r"^start$"))
async def start_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit(
        text=START_TXT.format(
            user=callback_query.from_user.mention,
            bot=client.mention
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🔍 About", callback_data="about"),
                    InlineKeyboardButton("📚 Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("🌐 Channel", url=f"https://t.me/{UPDATES_CHANNEL[1:]}"),
                    InlineKeyboardButton("👥 Group", url=f"https://t.me/{SUPPORT_GROUP[1:]}")
                ],
                [
                    InlineKeyboardButton("❌ Close", callback_data="close")
                ]
            ]
        )
    )
    await callback_query.answer()

@Bot.on_callback_query(filters.regex(r"^about$"))
async def about_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit(
        text=ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 Home", callback_data="start")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ]
        ),
        disable_web_page_preview=True
    )
    await callback_query.answer()

@Bot.on_callback_query(filters.regex(r"^help$"))
async def help_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.edit(
        text=HELP_TXT,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 Home", callback_data="start")],
                [InlineKeyboardButton("❌ Close", callback_data="close")]
            ]
        )
    )
    await callback_query.answer()

@Bot.on_callback_query(filters.regex(r"^refresh_verify$"))
async def refresh_verify_callback(client: Client, callback_query: CallbackQuery):
    id = callback_query.from_user.id
    verify_status = await db.get_verify_status(id)
    if verify_status['is_verified']:
        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🏠 Home", callback_data="start")]
            ]
        )
        await callback_query.message.edit(
            text="Your verification is already complete! You can now use the bot.",
            reply_markup=reply_markup
        )
    else:
        token = await generate_token(id)
        link = f"https://t.me/{client.username}?start={token}"
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Verify", url=link),
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_verify")
                ]
            ]
        )
        await callback_query.message.edit(
            text=VERIFY_TXT.format(callback_query.from_user.mention),
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    await callback_query.answer()

@Bot.on_callback_query(filters.regex(r"^close$"))
async def close_callback(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer()

async def generate_token(user_id: int):
    token = f"{user_id}:{random.randint(1000, 9999)}"
    await db.update_verify_status(user_id, verify_token=token)
    return token

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
