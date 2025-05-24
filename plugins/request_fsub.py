#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#

import asyncio
import os
import random
import sys
import time
import logging
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, ChatMemberUpdated, ChatPermissions
from bot import Bot
from helper_func import *
from database.database import *

# Set up logging for this module
logger = logging.getLogger(__name__)

# Define message effect IDs (same as in start.py)
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

# Function to show force-sub settings with channels list, buttons, image, and message effects
async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Rᴇǫᴜᴇsᴛ Fꜱᴜʙ Sᴇᴛᴛɪɴɢs:</b>\n\n"
    channels = await db.show_channels()
    
    if not channels:
        settings_text += "<blockquote><i>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ʏᴇᴛ. Uꜱᴇ 𖤓 ᴀᴅᴅ Cʜᴀɴɴᴇʟs 𖤓 ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟs:</b></blockquote>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]</blockquote>\n"
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                settings_text += f"<blockquote><b>•</b> <code>{ch_id}</code> — <i>Uɴᴀᴠᴀɪʟᴀʙʟᴇ</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• ᴀᴅᴅ Cʜᴀɴɴᴇʟs ", callback_data="fsub_add_channel"),
                InlineKeyboardButton(" ʀᴇᴍovᴇ Cʜᴀɴɴᴇʟs •", callback_data="fsub_remove_channel")
            ],
            [
                InlineKeyboardButton("• ᴛᴏɢɢʟᴇ Mᴏᴅᴇ •", callback_data="fsub_toggle_mode")
            ]
            [
                InlineKeyboardButton("• ʀᴇꜰᴇʀsʜ ", callback_data="fsub_refresh"),
                InlineKeyboardButton(" ᴄʟosᴇ•", callback_data="fsub_close")
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
            logger.info("Edited message as text-only")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
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
            logger.info(f"Sent photo message with image {selected_image} and effect {selected_effect}")
        except Exception as e:
            logger.error(f"Failed to send photo message with image {selected_image}: {e}")
            # Fallback to text-only message
            try:
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=selected_effect
                )
                logger.info(f"Sent text-only message with effect {selected_effect} as fallback")
            except Exception as e:
                logger.error(f"Failed to send text-only message with effect {selected_effect}: {e}")
                # Final fallback without effect
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                logger.info("Sent text-only message without effect as final fallback")

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Client, message: Message):
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    if data == "fsub_add_channel":
        await db.set_temp_state(chat_id, "awaiting_add_channel_input")
        logger.info(f"Set state to 'awaiting_add_channel_input' for chat {chat_id}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID.</b>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("•ʙᴀᴄᴋ•", callback_data="fsub_back"),
                    InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID.</b>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b></blockquote>")

    elif data == "fsub_remove_channel":
        await db.set_temp_state(chat_id, "awaiting_remove_channel_input")
        logger.info(f"Set state to 'awaiting_remove_channel_input' for chat {chat_id}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴏʀ ᴛʏᴘᴇ '<code>all</code>' ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴄʜᴀɴɴᴇʟs.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("•ʙᴀᴄᴋ•", callback_data="fsub_back"),
                    InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴏʀ ᴛʏᴘᴇ '<code>all</code>'.</b></blockquote>")

    elif data == "fsub_toggle_mode":
        temp = await callback.message.reply("<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>", quote=True)
        channels = await db.show_channels()

        if not channels:
            await temp.edit("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
            await callback.answer()
            return

        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "🟢" if mode == "on" else "🔴"
                title = f"{status} {chat.title}"
                buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Uɴᴀᴠᴀɪʟᴀʙʟᴇ)", callback_data=f"rfs_ch_{ch_id}")])

        buttons.append([InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")])

        await temp.edit(
            "<blockquote><b>⚡ Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        await callback.answer()

    elif data == "fsub_refresh":
        await show_force_sub_settings(client, chat_id, callback.message.id)
        await callback.answer("Sᴇᴛᴛɪɴɢs ʀᴇғʀᴇsʜᴇᴅ!")

    elif data == "fsub_close":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer("Sᴇᴛᴛɪɴɢs ᴄʟᴏsᴇᴅ!")

    elif data == "fsub_back":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Bᴀᴄᴋ ᴛᴏ sᴇᴛᴛɪɴɢs!")

    elif data == "fsub_cancel":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Aᴄᴛɪᴏɴ ᴄᴀɴᴄᴇʟʟᴇᴅ!")

@Bot.on_message(filters.private & filters.regex(r"^-?\d+$|^all$") & admin)
async def handle_channel_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Handling input: {message.text} for state: {state} in chat {chat_id}")

    try:
        if state == "awaiting_add_channel_input":
            channel_id = int(message.text)
            all_channels = await db.show_channels()
            channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
            if channel_id in channel_ids_only:
                await message.reply(f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <blockquote><code>{channel_id}</code></blockquote>")
                return

            chat = await client.get_chat(channel_id)

            if chat.type != ChatType.CHANNEL:
                await message.reply("<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>")
                return

            member = await client.get_chat_member(chat.id, "me")
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await message.reply("<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>")
                return

            link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
            
            await db.add_channel(channel_id)
            await message.reply(
                f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                f"<blockquote><b>Iᴅ: <code>{channel_id}</code></b></blockquote>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id)

        elif state == "awaiting_remove_channel_input":
            all_channels = await db.show_channels()
            if message.text.lower() == "all":
                if not all_channels:
                    await message.reply("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
                    return
                for ch_id in all_channels:
                    await db.rem_channel(ch_id)
                await message.reply("<blockquote><b>✅ Aʟʟ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ʀᴇᴍᴏᴠᴇᴅ.</b></blockquote>")
            else:
                ch_id = int(message.text)
                if ch_id in all_channels:
                    await db.rem_channel(ch_id)
                    await message.reply(f"<blockquote><b>✅ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ:</b></blockquote>\n <blockquote><code>{ch_id}</code></blockquote>")
                else:
                    await message.reply(f"<blockquote><b>❌ Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <blockquote><code>{ch_id}</code></blockquote>")
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id)

    except ValueError:
        logger.error(f"Invalid input received: {message.text}")
        await message.reply("<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>")
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)
    except Exception as e:
        logger.error(f"Failed to process channel input {message.text}: {e}")
        await message.reply(
            f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{message.text}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)

@Bot.on_message(filters.command('fsub_mode') & filters.private & admin)
async def change_force_sub_mode(client: Client, message: Message):
    temp = await message.reply("<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>", quote=True)
    channels = await db.show_channels()

    if not channels:
        await temp.edit("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
        return

    buttons = []
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            mode = await db.get_channel_mode(ch_id)
            status = "🟢" if mode == "on" else "🔴"
            title = f"{status} {chat.title}"
            buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
        except Exception as e:
            logger.error(f"Failed to fetch chat {ch_id}: {e}")
            buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Uɴᴀᴠᴀɪʟᴀʙʟᴇ)", callback_data=f"rfs_ch_{ch_id}")])

    buttons.append([InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")])

    await temp.edit(
        "<blockquote><b>⚡ Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:</b></blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )

@Bot.on_chat_member_updated()
async def handle_Chatmembers(client, chat_member_updated: ChatMemberUpdated):    
    chat_id = chat_member_updated.chat.id

    if await db.reqChannel_exist(chat_id):
        old_member = chat_member_updated.old_chat_member

        if not old_member:
            return

        if old_member.status == ChatMemberStatus.MEMBER:
            user_id = old_member.user.id

            if await db.req_user_exist(chat_id, user_id):
                await db.del_req_user(chat_id, user_id)

@Bot.on_chat_join_request()
async def handle_join_request(client, chat_join_request):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id

    if await db.reqChannel_exist(chat_id):
        if not await db.req_user_exist(chat_id, user_id):
            await db.req_user(chat_id, user_id)

@Bot.on_message(filters.command('addchnl') & filters.private & admin)
async def add_force_sub(client: Client, message: Message):
    temp = await message.reply("<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
        await temp.edit(
            "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/addchnl -100XXXXXXXXXX</code>\n<b>Aᴅᴅ ᴏɴʟʏ ᴏɴᴇ ᴄʜᴀɴɴᴇʟ ᴀᴛ ᴀ ᴛɪᴍᴇ.</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    try:
        channel_id = int(args[1])
    except ValueError:
        await temp.edit("<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ!</b></blockquote>")
        return

    all_channels = await db.show_channels()
    channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
    if channel_id in channel_ids_only:
        await temp.edit(f"<blockquote><b>Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <blockquote><code>{channel_id}</code></blockquote>")
        return

    try:
        chat = await client.get_chat(channel_id)

        if chat.type != ChatType.CHANNEL:
            await temp.edit("<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>")
            return

        member = await client.get_chat_member(chat.id, "me")
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await temp.edit("<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>")
            return

        link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
        
        await db.add_channel(channel_id)
        await temp.edit(
            f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
            f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
            f"<blockquote><b>Iᴅ:</b> <code>{channel_id}</code></blockquote>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Failed to add channel {channel_id}: {e}")
        await temp.edit(
            f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('delchnl') & filters.private & admin)
async def del_force_sub(client: Client, message: Message):
    temp = await message.reply("<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)
    all_channels = await db.show_channels()

    if len(args) < 2:
        buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
        await temp.edit(
            "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/delchnl <channel_id | all</code>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if args[1].lower() == "all":
        if not all_channels:
            await temp.edit("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
            return
        for ch_id in all_channels:
            await db.rem_channel(ch_id)
        await temp.edit("<blockquote><b>✅ Aʟʟ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ʀᴇᴍᴏᴠᴇᴅ.</b></blockquote>")
        return

    try:
        ch_id = int(args[1])
        if ch_id in all_channels:
            await db.rem_channel(ch_id)
            await temp.edit(f"<blockquote><b>✅ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ:</b></blockquote>\n <code>{ch_id}</code>")
        else:
            await temp.edit(f"<blockquote><b>❌ Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <code>{ch_id}</code>")
    except ValueError:
        buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
        await temp.edit(
            "<blockquote><b>Uꜱᴀɢᴇ:</b></blockquote>\n <code>/delchnl <channel_id | all</code>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error removing channel {args[1]}: {e}")
        await temp.edit(f"<blockquote><b>❌ Eʀʀᴏʀ:</b></blockquote>\n <code>{e}</code>")

@Bot.on_message(filters.command('listchnl') & filters.private & admin)
async def list_force_sub_channels(client: Client, message: Message):
    temp = await message.reply("<b><i>Wᴀɪᴛ ᴀ sᴇᴄ...</i></b>", quote=True)
    channels = await db.show_channels()

    if not channels:
        await temp.edit("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
        return

    result = "<blockquote><b>⚡ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟs:</b></blockquote>\n\n"
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
            result += f"<b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]\n"
        except Exception as e:
            logger.error(f"Failed to fetch chat {ch_id}: {e}")
            result += f"<b>•</b> <code>{ch_id}</code> — <i>Uɴᴀᴠᴀɪʟᴀʙʟᴇ</i>\n"

    buttons = [[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data="close")]]
    await temp.edit(
        result, 
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved
#
