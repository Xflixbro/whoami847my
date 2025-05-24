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
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatMemberUpdated, ChatPermissions
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, InviteHashEmpty, ChatAdminRequired, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import *
from database.database import *
from banuser import show_user_settings  # Importing show_user_settings from banuser.py

# Function to show admin settings with admin list, buttons, and message effects
async def show_admin_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Aᴅᴍɪɴ Sᴇᴛᴛɪɴɢꜱ:</b>\n\n"
    admin_ids = await db.get_all_admins()

    if not admin_ids:
        settings_text += "<i>Nᴏ ᴀᴅᴍɪɴꜱ ᴄᴏɴғɪɢᴜʀᴇᴅ ʏᴇᴛ. Uꜱᴇ 'ᴀᴅᴅ ᴀᴅᴍɪɴ' ᴛᴏ ᴀᴅᴅ ᴀ/ᴍᴜʟᴛɪᴘʟᴇ ᴀᴅᴍɪɴ.</i>"
    else:
        settings_text += "<blockquote><b>⚡ Cᴜʀʀᴇɴᴛ Aᴅᴍɪɴꜱ:</b></blockquote>\n\n"
        for idx, admin_id in enumerate(admin_ids[:5], 1):  # Show up to 5 admins
            settings_text += f"<blockquote><b>{idx}. Iᴅ: <code>{admin_id}</code></b></blockquote>\n"
        if len(admin_ids) > 5:
            settings_text += f"<blockquote><i>...and {len(admin_ids) - 5} more.</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Aᴅᴅ Aᴅᴍɪɴ", callback_data="admin_add"),
                InlineKeyboardButton("Rᴇᴍᴏᴠᴇ Aᴅᴍɪɴ •", callback_data="admin_remove")
            ],
            [
                InlineKeyboardButton("Aᴅᴍɪɴ Lɪꜱᴛ", callback_data="admin_list"),
                InlineKeyboardButton("• Rᴇꜰʀᴇꜱʜ •", callback_data="admin_refresh")
            ],
            [
                InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="admin_close")
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
            logger.error(f"Failed to edit admin settings message: {e}")
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
            logger.error(f"Failed to send admin settings with photo: {e}")
            # Fallback to text-only message
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=selected_effect
            )

# Command to show admin settings
@Bot.on_message(filters.command('admin') & filters.private & admin)
async def admin_settings(client: Client, message: Message):
    await show_admin_settings(client, message.chat.id)

# Callback handler for admin settings buttons
@Bot.on_callback_query(filters.regex(r"^admin_"))
async def admin_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    if data == "admin_add":
        await db.set_temp_state(chat_id, "awaiting_add_admin_input")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴀᴅᴍɪɴ ID(ꜱ).</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="admin_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="admin_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴀᴅᴍɪɴ ID(ꜱ).</b></blockquote>")

    elif data == "admin_remove":
        await db.set_temp_state(chat_id, "awaiting_remove_admin_input")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴀᴅᴍɪɴ ID(ꜱ) ᴏʀ ᴛʏᴘᴇ 'all' ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴀᴅᴍɪɴꜱ.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="admin_back"),
                    InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="admin_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴀᴅᴍɪɴ ID(ꜱ) ᴏʀ ᴛʏᴘᴇ '[<code>all</code>]'.</b></blockquote>")

    elif data == "admin_list":
        admin_ids = await db.get_all_admins()
        if not admin_ids:
            admin_list = "<b><blockquote>❌ Nᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ.</blockquote></b>"
        else:
            admin_list = "\n".join(f"<b><blockquote>Iᴅ: <code>{id}</code></blockquote></b>" for id in admin_ids)

        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="admin_back"),
                InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="admin_close")
            ]
        ])
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"<b>⚡ Cᴜʀʀᴇɴᴛ ᴀᴅᴍɪɴ ʟɪꜱᴛ:</b>\n\n{admin_list}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Sʜᴏᴡɪɴɢ ᴀᴅᴍɪɴ ʟɪꜱᴛ!")

    elif data == "admin_refresh":
        await show_admin_settings(client, chat_id, message_id)
        await callback.answer("Sᴇᴛᴛɪɴɢꜱ ʀᴇꜰʀᴇꜱʜᴇᴅ!")

    elif data == "admin_close":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer("Sᴇᴛᴛɪɴɢꜱ ᴄʟᴏꜱᴇᴅ!")

    elif data == "admin_back":
        await db.set_temp_state(chat_id, "")
        await show_admin_settings(client, chat_id, message_id)
        await callback.answer("Bᴀᴄᴋ ᴛᴏ ꜱᴇᴛᴛɪɴɢꜱ!")

# Handle admin input for adding/removing admins and banning/unbanning users
@Bot.on_message(filters.private & filters.regex(r"^-?\d+$|^all$") & admin)
async def handle_admin_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        if state == "awaiting_add_admin_input":
            admin_ids = message.text.split()
            pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
            check = 0
            existing_admins = await db.get_all_admins()
            admin_list = ""

            for id in admin_ids:
                try:
                    id = int(id)
                except:
                    admin_list += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ɪᴅ: <code>{id}</code></b></blockquote>\n"
                    continue

                if id in existing_admins:
                    admin_list += f"<blockquote><b>Iᴅ <code>{id}</code> ᴀʟʀᴇᴀᴅʏ ᴇхɪꜱᴛꜱ.</b></blockquote>\n"
                    continue

                id = str(id)
                if id.isdigit() and len(id) == 10:
                    admin_list += f"<b><blockquote>(Iᴅ: <code>{id}</code>) ᴀᴅᴅᴇᴅ.</blockquote></b>\n"
                    check += 1
                else:
                    admin_list += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ɪᴅ: <code>{id}</code></b></blockquote>\n"

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="admin_close")]])

            if check == len(admin_ids):
                for id in admin_ids:
                    await db.add_admin(int(id))
                await pro.edit(f"<b>✅ Aᴅᴍɪɴ(ꜱ) ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ:</b>\n\n{admin_list}", reply_markup=reply_markup)
            else:
                await pro.edit(
                    f"<b>❌ Sᴏᴍᴇ ᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴀᴅᴅɪɴɢ ᴀᴅᴍɪɴꜱ:</b>\n\n{admin_list.strip()}\n\n"
                    "<b><i>Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</i></b>",
                    reply_markup=reply_markup
                )
            await db.set_temp_state(chat_id, "")
            await show_admin_settings(client, chat_id)

        elif state == "awaiting_remove_admin_input":
            admin_ids = await db.get_all_admins()
            if message.text.lower() == "all":
                if not admin_ids:
                    await message.reply("<blockquote><b>❌ Nᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ.</b></blockquote>")
                    return
                for admin_id in admin_ids:
                    await db.del_admin(admin_id)
                await message.reply("<blockquote><b>✅ Aʟʟ ᴀᴅᴍɪɴꜱ ʀᴇᴍᴏᴠᴇᴅ.</b></blockquote>")
            else:
                try:
                    id = int(message.text)
                    if id in admin_ids:
                        await db.del_admin(id)
                        await message.reply(f"<blockquote><b>✅ Aᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ:</b></blockquote>\n <code>{id}</code>")
                    else:
                        await message.reply(f"<blockquote><b>❌ Aᴅᴍɪɴ ɴᴏᴛ ꜰᴏᴜɴᴅ:</b></blockquote>\n <code>{id}</code>")
                except ValueError:
                    await message.reply("<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/deladmin <admin_id | all</code>")
                except Exception as e:
                    logger.error(f"Error removing admin {message.text}: {e}")
                    await message.reply(f"<blockquote><b>❌ Eʀʀᴏʀ:</b></blockquote>\n <code>{e}</code>")
            await db.set_temp_state(chat_id, "")
            await show_admin_settings(client, chat_id)

        elif state == "awaiting_ban_input":
            banuser_ids = await db.get_ban_users()
            banusers = message.text.split()
            pro = await message.reply("<b><i>Pʀᴏᴄᴇꜱꜱɪɴɢ ʀᴇꜱᴜᴇꜱᴛ...</i></b>", quote=True)
            report, success_count = "", 0

            for uid in banusers:
                try:
                    uid_int = int(uid)
                except:
                    report += f"<blockquote><b>⚠️ Iɴᴠᴀʟɪᴅ ID: <code>{uid}</code></b></blockquote>\n"
                    continue

                if uid_int in await db.get_all_admins() or uid_int == OWNER_ID:
                    report += f"<blockquote><b>⛔ Sᴋɪᴘᴘᴇᴅ ᴀᴅᴍɪɴ/ᴏᴡɴᴇʀ ID: <code>{uid_int}</code></b></blockquote>\n"
                    continue

                if uid_int in banuser_ids:
                    report += f"<blockquote><b>⚠️ Aʟʀᴇᴀᴅʏ: <code>{uid_int}</code></b></blockquote>\n"
                    continue

                if len(str(uid_int)) == 10:
                    await db.add_ban_user(uid_int)
                    report += f"<blockquote><b>✅ Bᴀɴɴᴇᴅ: <code>{uid_int}</code></b></blockquote>\n"
                    success_count += 1
                else:
                    report += f"<blockquote><b>⚠️ Iɴᴠᴀʟɪᴅ Tᴇʟᴇɢʀᴀᴍ ID ʟᴇɴɡᴛʜ: <code>{uid_int}</code></b></blockquote>\n"

            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="user_close")]])

            if success_count:
                await pro.edit(f"<b>✅ Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ Uᴘᴅᴀᴛᴇᴅ:</b>\n\n{report}", reply_markup=reply_markup)
            else:
                await pro.edit(f"<b>❌ Nᴏ ᴜꜱᴇʀꜱ ᴡᴇʀᴇ ʙᴀɴɴᴇᴅ.</b>\n\n{report}", reply_markup=reply_markup)
            await db.set_temp_state(chat_id, "")
            await show_user_settings(client, chat_id)

        elif state == "awaiting_unban_input":
            banuser_ids = await db.get_ban_users()
            if message.text.lower() == "all":
                if not banuser_ids:
                    await message.reply("<blockquote><b>✅ Nᴏ ᴜꜱᴇʀꜱ ɪɴ ᴛʜᴇ ʙᴀɴ ʟɪꜱᴛ.</b></blockquote>")
                    return
                for uid in banuser_ids:
                    await db.del_ban_user(uid)
                listed = "\n".join([f"<blockquote><b>✅ Uɴʙᴀɴɴᴇᴅ: <code>{uid}</code></b></blockquote>" for uid in banuser_ids])
                await message.reply(f"<b>🚫 Cʟᴇᴀʀᴇᴅ Bᴀɴ Lɪꜱᴛ:</b>\n\n{listed}")
            else:
                try:
                    uid_int = int(message.text)
                    if uid_int in banuser_ids:
                        await db.del_ban_user(uid_int)
                        await message.reply(f"<blockquote><b>✅ Uɴʙᴀɴɴᴇᴅ:</b></blockquote>\n <code>{uid_int}</code>")
                    else:
                        await message.reply(f"<blockquote><b>⚠️ Nᴏᴛ ɪɴ ʙᴀɴ ʟɪꜱᴛ:</b></blockquote>\n <code>{uid_int}</code>")
                except ValueError:
                    await message.reply("<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/unban <user_id | all</code>")
                except Exception as e:
                    logger.error(f"Error unbanning user {message.text}: {e}")
                    await message.reply(f"<blockquote><b>❌ Eʀʀᴏʀ:</b></blockquote>\n <code>{e}</code>")
            await db.set_temp_state(chat_id, "")
            await show_user_settings(client, chat_id)

    except Exception as e:
        logger.error(f"Failed to process input {message.text}: {e}")
        await message.reply(
            f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇꜱꜱ ɪɴᴘᴜᴛ:</b></blockquote>\n<code>{message.text}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        if state in ["awaiting_add_admin_input", "awaiting_remove_admin_input"]:
            await show_admin_settings(client, chat_id)
        elif state in ["awaiting_ban_input", "awaiting_unban_input"]:
            await show_user_settings(client, chat_id)

# Commands for adding admins by owner
@Bot.on_message(filters.command('add_admin') & filters.private & filters.user(OWNER_ID))
async def add_admins(client: Client, message: Message):
    pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
    check = 0
    admin_ids = await db.get_all_admins()
    admins = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="close")]])

    if not admins:
        return await pro.edit(
            "<b>Yᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴜꜱᴇʀ ɪᴅ(ꜱ) ᴛᴏ ᴀᴅᴅ ᴀꜱ ᴀᴅᴍɪɴ.</b>\n\n"
            "<b>Uꜱᴀɢᴇ:</b>\n"
            "<code>/add_admin [user_id]</code> — Aᴅᴅ ᴏɴᴇ ᴏʀ ᴍᴏʀᴇ ᴜꜱᴇʀ ɪᴅꜱ\n\n"
            "<b>Eхᴀᴍᴘʟᴇ:</b>\n"
            "<code>/add_admin 1234567890 9876543210</code>",
            reply_markup=reply_markup
        )

    admin_list = ""
    for id in admins:
        try:
            id = int(id)
        except:
            admin_list += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ɪᴅ: <code>{id}</code></b></blockquote>\n"
            continue

        if id in admin_ids:
            admin_list += f"<blockquote><b>Iᴅ <code>{id}</code> ᴀʟʀᴇᴀᴅʏ ᴇхɪꜱᴛꜱ.</b></blockquote>\n"
            continue

        id = str(id)
        if id.isdigit() and len(id) == 10:
            admin_list += f"<b><blockquote>(Iᴅ: <code>{id}</code>) ᴀᴅᴅᴇᴅ.</blockquote></b>\n"
            check += 1
        else:
            admin_list += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ɪᴅ: <code>{id}</code></b></blockquote>\n"

    if check == len(admins):
        for id in admins:
            await db.add_admin(int(id))
        await pro.edit(f"<b>✅ Aᴅᴍɪɴ(ꜱ) ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ:</b>\n\n{admin_list}", reply_markup=reply_markup)
    else:
        await pro.edit(
            f"<b>❌ Sᴏᴍᴇ ᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴀᴅᴅɪɴɢ ᴀᴅᴍɪɴꜱ:</b>\n\n{admin_list.strip()}\n\n"
            "<b><i>Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</i></b>",
            reply_markup=reply_markup
        )

@Bot.on_message(filters.command('deladmin') & filters.private & filters.user(OWNER_ID))
async def delete_admins(client: Client, message: Message):
    pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
    admin_ids = await db.get_all_admins()
    admins = message.text.split()[1:]

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="close")]])

    if not admins:
        return await pro.edit(
            "<b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴠᴀʟɪᴅ ᴀᴅᴍɪɴ ɪᴅ(ꜱ) ᴛᴏ ʀᴇᴍᴏᴠᴇ.</b>\n\n"
            "<b>Uꜱᴀɢᴇ:</b>\n"
            "<code>/deladmin [user_id]</code> — Rᴇᴍᴏᴠᴇ ꜱᴘᴇᴄɪғɪᴄ ɪᴅꜱ\n"
            "<code>/deladmin all</code> — Rᴇᴍᴏᴠᴇ ᴀʟʟ ᴀᴅᴍɪɴꜱ",
            reply_markup=reply_markup
        )

    if len(admins) == 1 and admins[0].lower() == "all":
        if admin_ids:
            for id in admin_ids:
                await db.del_admin(id)
            ids = "\n".join(f"<blockquote><code>{admin}</code> ✅</blockquote>" for admin in admin_ids)
            return await pro.edit(f"<b>⛔ Aʟʟ ᴀᴅᴍɪɴ ɪᴅꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ:</b>\n{ids}", reply_markup=reply_markup)
        else:
            return await pro.edit("<b><blockquote>Nᴏ ᴀᴅᴍɪɴ ɪᴅꜱ ᴛᴏ ʀᴇᴍᴏᴠᴇ.</blockquote></b>", reply_markup=reply_markup)

    if admin_ids:
        passed = ''
        for admin_id in admins:
            try:
                id = int(admin_id)
            except:
                passed += f"<blockquote><b>Iɴᴠᴀʟɪᴅ ɪᴅ: <code>{admin_id}</code></b></blockquote>\n"
                continue

            if id in admin_ids:
                await db.del_admin(id)
                passed += f"<blockquote><code>{id}</code> ✅ Rᴇᴍᴏᴠᴇᴅ</blockquote>\n"
            else:
                passed += f"<blockquote><b>Iᴅ <code>{id}</code> ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴀᴅᴍɪɴ ʟɪꜱᴛ.</b></blockquote>\n"

        await pro.edit(f"<b>⛔ Aᴅᴍɪɴ ʀᴇᴍᴏᴠᴀʟ ʀᴇꜱᴜʟᴛ:</b>\n\n{passed}", reply_markup=reply_markup)
    else:
        await pro.edit("<b><blockquote>Nᴏ ᴀᴅᴍɪɴ ɪᴅꜱ ᴀᴠᴀɪʟᴀʙʟᴇ ᴛᴏ ᴅᴇʟᴇᴛᴇ.</blockquote></b>", reply_markup=reply_markup)

@Bot.on_message(filters.command('admins') & filters.private & admin)
async def get_admins(client: Client, message: Message):
    pro = await message.reply("<b><i>Pʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</i></b>", quote=True)
    admin_ids = await db.get_all_admins()

    if not admin_ids:
        admin_list = "<b><blockquote>❌ Nᴏ ᴀᴅᴍɪɴꜱ ꜰᴏᴜɴᴅ.</blockquote></b>"
    else:
        admin_list = "\n".join(f"<b><blockquote>Iᴅ: <code>{id}</code></blockquote></b>" for id in admin_ids)

    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• Bᴀᴄᴋ •", callback_data="admin_back"),
            InlineKeyboardButton("• Cʟᴏꜱᴇ •", callback_data="admin_close")
        ]
    ])
    await pro.edit(f"<b>⚡ Cᴜʀʀᴇɴᴛ ᴀᴅᴍɪɴ ʟɪꜱᴛ:</b>\n\n{admin_list}", reply_markup=reply_markup)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
