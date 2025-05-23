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
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatInviteLink, ChatPrivileges
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant
from bot import Bot
from config import *
from helper_func import *
from database.database import *

# Function to show user settings with user list, buttons, and message effects
async def show_user_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Uꜱᴇʀ Sᴇᴛᴛɪɴɢꜱ:</b>\n\n"
    users = await db.full_userbase()

    if not users:
        settings_text += "<i>Nᴏ ᴜꜱᴇʀꜱ ғᴏᴜɴᴅ ʏᴇᴛ.</i>"
    else:
        settings_text += "<blockquote><b>⚡ Cᴜʀʀᴇɴᴛ Uꜱᴇʀꜱ:</b></blockquote>\n\n"
        for idx, user_id in enumerate(users[:5], 1):  # Show up to 5 users
            try:
                user = await client.get_users(user_id)
                user_link = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
                settings_text += f"<blockquote><b>{idx}. {user_link} — <code>{user_id}</code></b></blockquote>\n"
            except:
                settings_text += f"<blockquote><b>{idx}. <code>{user_id}</code> — <i>Cᴏᴜʟᴅ ɴᴏᴛ ғᴇᴛᴄʜ ɴᴀᴍᴇ</i></b></blockquote>\n"
        if len(users) > 5:
            settings_text += f"<blockquote><i>...and {len(users) - 5} more.</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Bᴀɴ Uꜱᴇʀ", callback_data="user_ban"),
                InlineKeyboardButton("Uɴʙᴀɴ Uꜱᴇʀ •", callback_data="user_unban")
            ],
            [
                InlineKeyboardButton("Uꜱᴇʀ Lɪꜱᴛ", callback_data="user_list"),
                InlineKeyboardButton("Bᴀɴ Lɪꜱᴛ", callback_data="user_banlist")
            ],
            [
                InlineKeyboardButton("• Rᴇꜰʀᴇꜱʜ •", callback_data="user_refresh"),
                InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
            ]
        ]
    )

    # Select random image and effect
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

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
        except Exception as e:
            logger.error(f"Failed to edit user settings message: {e}")
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                message_effect_id=selected_effect
            )
        except Exception as e:
            logger.error(f"Failed to send user settings with photo: {e}")
            # Fallback to text-only message
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=selected_effect
            )

# Command to show user settings
@Bot.on_message(filters.private & filters.command('user') & admin)
async def user_settings(client: Client, message: Message):
    await show_user_settings(client, message.chat.id)

# Callback handler for user settings buttons
@Bot.on_callback_query(filters.regex(r"^user_"))
async def user_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    if data == "user_ban":
        await db.set_temp_state(chat_id, "awaiting_ban_user_input")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜꜱᴇʀ ID(ꜱ) ᴛᴏ ʙᴀɴ.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="user_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴜꜱᴇʀ ID(ꜱ).</b></blockquote>")

    elif data == "user_unban":
        await db.set_temp_state(chat_id, "awaiting_unban_user_input")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜꜱᴇʀ ID(ꜱ) ᴏʀ ᴛʏᴘᴇ 'all' ᴛᴏ ᴜɴʙᴀɴ ᴀʟʟ ᴜꜱᴇʀꜱ.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="user_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="user_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴜꜱᴇʀ ID(ꜱ) ᴏʀ ᴛʏᴘᴇ '[<code>all</code>]'.</b></blockquote>")

    elif data == "user_list":
        users = await db.full_userbase()
        if not users:
            user_list = "<b><blockquote>❌ Nᴏ ᴜꜱᴇʀꜱ ғᴏᴜɴᴅ.</blockquote></b>"
        else:
            user_list = "<b>⚡ Cᴜʀʀᴇɴᴛ ᴜꜱᴇʀ ʟɪꜱᴛ:</b>\n\n"
            for user_id in users:
                try:
                    user = await client.get_users(user_id)
                    user_link = f'<a href="tg://user?id={user_id}">{user.first_name}</a>'
                    user_list += f"<b><blockquote>{user_link} — <code>{user_id}</code></blockquote></b>\n"
                except:
                    user_list += f"<b><blockquote><code>{user_id}</code> — <i>Cᴏᴜʟᴅ ɴᴏᴛ ғᴇᴛᴄʜ ɴᴀᴍᴇ</i></blockquote></b>\n"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="user_close")]])
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=user_list,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Sʜᴏᴡɪɴɢ ᴜꜱᴇʀ ʟɪꜱᴛ!")

    elif data == "user_banlist":
        banuser_ids = await db.get_ban_users()
        if not banuser_ids:
            result = "<b><blockquote>✅ Nᴏ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ʙᴀɴ Lɪꜱᴛ.</blockquote></b>"
        else:
            result = "<b>🚫 Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ:</b>\n\n"
            for uid in banuser_ids:
                await callback.message.reply_chat_action(ChatAction.TYPING)
                try:
                    user = await client.get_users(uid)
                    user_link = f'<a href="tg://user?id={uid}">{user.first_name}</a>'
                    result += f"<b><blockquote>{user_link} — <code>{uid}</code></blockquote></b>\n"
                except:
                    result += f"<b><blockquote><code>{uid}</code> — <i>Cᴏᴜʟᴅ ɴᴏᴛ ғᴇᴛᴄʜ ɴᴀᴍᴇ</i></blockquote></b>\n"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="user_close")]])
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=result,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Sʜᴏᴡɪɴɢ ʙᴀɴ ʟɪꜱᴛ!")

    elif data == "user_refresh":
        await show_user_settings(client, chat_id, message_id)
        await callback.answer("Sᴇᴛᴛɪɴɢꜱ ʀᴇꜰʀᴇꜱʜᴇᴅ!")

    elif data == "user_close":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer("Sᴇᴛᴛɪɴɢꜱ ᴄʟᴏꜱᴇᴅ!")

    elif data == "user_back":
        await db.set_temp_state(chat_id, "")
        await show_user_settings(client, chat_id, message_id)
        await callback.answer("Bᴀᴄᴋ ᴛᴏ ꜱᴇᴛᴛɪɴɢꜱ!")

# Handle user input for banning/unbanning users
@Bot.on_message(filters.private & filters.regex(r"^-?\d+$|^all$") & admin)
async def handle_user_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)

    try:
        if state == "awaiting_ban_user_input":
            banuser_ids = await db.get_ban_users()
            user_ids = message.text.split()
            pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
            report, success_count = "", 0

            for uid in user_ids:
                try:
                    uid_int = int(uid)
                except:
                    report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code></b></blockquote>\n"
                    continue

                if uid_int in await db.get_all_admins() or uid_int == OWNER_ID:
                    report += f"<blockquote><b>Sᴋɪᴘᴘᴇᴅ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ ID: <code>{uid_int}</code></b></blockquote>\n"
                    continue

                if uid_int in banuser_ids:
                    report += f"<blockquote><b>Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ: <code>{uid_int}</code></b></blockquote>\n"
                    continue

                if len(str(uid_int)) == 10:
                    await db.add_ban_user(uid_int)
                    report += f"<b><blockquote>Bᴀɴɴᴇᴅ: <code>{uid_int}</code></blockquote></b>\n"
                    success_count += 1
                else:
                    report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ Tᴇʟᴇɢʀᴀᴍ ID ʟᴇɴɢᴛʜ: <code>{uid_int}</code></b></blockquote>\n"

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="user_close")]])

            if success_count:
                await pro.edit(f"<b>✅ Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ Uᴘᴅᴀᴛᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)
            else:
                await pro.edit(f"<b>❌ Nᴏ ᴜꜱᴇʀꜱ ᴡᴇʀᴇ ʙᴀɴɴᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)
            await db.set_temp_state(chat_id, "")
            await show_user_settings(client, chat_id)

        elif state == "awaiting_unban_user_input":
            banuser_ids = await db.get_ban_users()
            if message.text.lower() == "all":
                if not banuser_ids:
                    await message.reply("<blockquote><b>❌ Nᴏ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪꜱᴛ.</b></blockquote>")
                    return
                for uid in banuser_ids:
                    await db.del_ban_user(uid)
                listed = "\n".join([f"<b><blockquote>Uɴʙᴀɴɴᴇᴅ: <code>{uid}</code></blockquote></b>" for uid in banuser_ids])
                await message.reply(f"<b>🚫 Cʟᴇᴀʀᴇᴅ Bᴀɴ Lɪꜱᴛ:</b>\n\n{listed}")
            else:
                user_ids = message.text.split()
                pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
                report = ""

                for uid in user_ids:
                    try:
                        uid_int = int(uid)
                    except:
                        report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code></b></blockquote>\n"
                        continue

                    if uid_int in banuser_ids:
                        await db.del_ban_user(uid_int)
                        report += f"<b><blockquote>Uɴʙᴀɴɴᴇᴅ: <code>{uid_int}</code></blockquote></b>\n"
                    else:
                        report += f"<blockquote><b>Nᴏᴛ ɪɴ ʙᴀɴ ʟɪꜱᴛ: <code>{uid_int}</code></b></blockquote>\n"

                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="user_close")]])
                await pro.edit(f"<b>🚫 Uɴʙᴀɴ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup=reply_markup)
            await db.set_temp_state(chat_id, "")
            await show_user_settings(client, chat_id)

    except Exception as e:
        logger.error(f"Failed to process user input {message.text}: {e}")
        await message.reply(
            f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇꜱꜱ ᴜꜱᴇʀ ɪɴᴘᴜᴛ:</b></blockquote>\n<code>{message.text}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_user_settings(client, chat_id)

# BAN-USER-SYSTEM
@Bot.on_message(filters.private & filters.command('ban') & admin)
async def add_banuser(client: Client, message: Message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇꜱꜱɪɴɢ ʀᴇǫᴜᴇꜱᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close")]])

    if not banusers:
        return await pro.edit(
            "<b>❗ Yᴏᴜ ᴍᴜꜱᴛ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ IDs ᴛᴏ ʙᴀɴ.</b>\n\n"
            "<b>📌 Uꜱᴀɢᴇ:</b>\n"
            "<code>/ban [user_id]</code> — Bᴀɴ ᴏɴᴇ ᴏʀ ᴍᴏʀᴇ ᴜꜱᴇʀꜱ ʙʏ ID.",
            reply_markup=reply_markup
        )

    report, success_count = "", 0
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code></b></blockquote>\n"
            continue

        if uid_int in await db.get_all_admins() or uid_int == OWNER_ID:
            report += f"<blockquote><b>Sᴋɪᴘᴘᴇᴅ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ ID: <code>{uid_int}</code></b></blockquote>\n"
            continue

        if uid_int in banuser_ids:
            report += f"<blockquote><b>Aʟʀᴇᴀᴅʏ ʙᴀɴɴᴇᴅ: <code>{uid_int}</code></b></blockquote>\n"
            continue

        if len(str(uid_int)) == 10:
            await db.add_ban_user(uid_int)
            report += f"<b><blockquote>Bᴀɴɴᴇᴅ: <code>{uid_int}</code></blockquote></b>\n"
            success_count += 1
        else:
            report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ Tᴇʟᴇɢʀᴀᴍ ID ʟᴇɴɢᴛʜ: <code>{uid_int}</code></b></blockquote>\n"

    if success_count:
        await pro.edit(f"<b>✅ Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ Uᴘᴅᴀᴛᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)
    else:
        await pro.edit(f"<b>❌ Nᴏ ᴜꜱᴇʀꜱ ᴡᴇʟʀᴇ ʙᴀɴɴᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('unban') & admin)
async def delete_banuser(client: Client, message: Message):        
    pro = await message.reply("⏳ <i>Pʀᴏᴄᴇꜱꜱɪɴɢ ʀᴇǫᴜᴇꜱᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()
    banusers = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close")]])

    if not banusers:
        return await pro.edit(
            "<b>❗ Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ IDs ᴛᴏ ᴜɴʙᴀɴ.</b>\n\n"
            "<b>📌 Uꜱᴀɢᴇ:</b>\n"
            "<code>/unban [user_id]</code> — Uɴʙᴀɴ ꜱᴘᴇᴄɪғɪᴄ ᴜꜱᴇʀ(ꜱ)\n"
            "<code>/unban all</code> — Rᴇᴍᴏᴠᴇ ᴀʟʟ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀꜱ",
            reply_markup=reply_markup
        )

    if banusers[0].lower() == "all":
        if not banuser_ids:
            return await pro.edit("<b>✅ Nᴏ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪꜱᴛ.</b>", reply_markup=reply_markup)
        for uid in banuser_ids:
            await db.del_ban_user(uid)
        listed = "\n".join([f"<b><blockquote>Uɴʙᴀɴɴᴇᴅ: <code>{uid}</code></blockquote></b>" for uid in banuser_ids])
        return await pro.edit(f"<b>🚫 Cʟᴇᴀʀᴇᴅ Bᴀɴ Lɪꜱᴛ:</b>\n\n{listed}", reply_markup=reply_markup)

    report = ""
    for uid in banusers:
        try:
            uid_int = int(uid)
        except:
            report += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code></b></blockquote>\n"
            continue

        if uid_int in banuser_ids:
            await db.del_ban_user(uid_int)
            report += f"<b><blockquote>Uɴʙᴀɴɴᴇᴅ: <code>{uid_int}</code></blockquote></b>\n"
        else:
            report += f"<blockquote><b>Nᴏᴛ ɪɴ ʙᴀɴ ʟɪꜱᴛ: <code>{uid_int}</code></b></blockquote>\n"

    await pro.edit(f"<b>🚫 Uɴʙᴀɴ Rᴇᴘᴏʀᴛ:</b>\n\n{report}", reply_markup=reply_markup)

@Bot.on_message(filters.private & filters.command('banlist') & admin)
async def get_banuser_list(client: Client, message: Message):        
    pro = await message.reply("⏳ <i>Fᴇᴛᴄʜɪɴɢ Bᴀɴ Lɪꜱᴛ...</i>", quote=True)
    banuser_ids = await db.get_ban_users()

    if not banuser_ids:
        return await pro.edit("<b>✅ Nᴏ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ʙᴀɴ Lɪꜱᴛ.</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close")]]))

    result = "<b>🚫 Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ:</b>\n\n"
    for uid in banuser_ids:
        await message.reply_chat_action(ChatAction.TYPING)
        try:
            user = await client.get_users(uid)
            user_link = f'<a href="tg://user?id={uid}">{user.first_name}</a>'
            result += f"<b><blockquote>{user_link} — <code>{uid}</code></blockquote></b>\n"
        except:
            result += f"<b><blockquote><code>{uid}</code> — <i>Cᴏᴜʟᴅ ɴᴏᴛ ғᴇᴛᴄʜ ɴᴀᴍᴇ</i></blockquote></b>\n"

    await pro.edit(result, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close")]]))

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
