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
        await pro.edit(f"<b>✅ Aᴅᴍɪɴ(ꜱ) ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ:</b>\n\n{admin_list}", reply_markup=reply_markup)
    else:
        await pro.edit(
            f"<b>❌ Sᴏᴍᴇ ᴇʀʀᴏʀꜱ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴀᴅᴅɪɴɢ ᴀᴅᴍɪɴꜱ:</b>\n\n{admin_list.strip()}\n\n"
            "<b><i>Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.</i></b>",
            reply_markup=reply_markup
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
            "<code>/deladmin [user_id]</code> — Rᴇᴍᴏᴠᴇ ꜱᴘᴇᴄɪꜰɪᴄ ɪᴅꜱ\n"
            "<code>/deladmin all</code> — Rᴇᴍᴏᴠᴇ ᴀʟʟ ᴀᴅᴍɪɴꜱ",
            reply_markup=reply_markup
        )

    if len(admins) == 1 and admins[0].lower() == "all":
        if admin_ids:
            for id in admin_ids:
                await db.del_admin(id)
            ids = "\n".join(f"<blockquote><code>{admin}</code> ✅</blockquote>" for admin in admin_ids)
            return await pro.edit(f"<b>⛔️ Aʟʟ ᴀᴅᴍɪɴ ɪᴅꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ:</b>\n{ids}", reply_markup=reply_markup)
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

        await pro.edit(f"<b>⛔️ Aᴅᴍɪɴ ʀᴇᴍᴏᴠᴀʟ ʀᴇꜱᴜʟᴛ:</b>\n\n{passed}", reply_markup=reply_markup)
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

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="close")]])
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