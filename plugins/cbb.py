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
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType
from pyrogram.types import InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from database.database import db
from helper_func import get_readable_time

# Custom filter for timer input
async def timer_input_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    if state == "awaiting_timer_input" and message.text and message.text.isdigit():
        return True
    return False

# Custom filter for force-sub states
async def fsub_state_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    if state not in ["awaiting_add_channel_input", "awaiting_remove_channel_input"]:
        return False
    if not message.text:
        return False
    is_valid_input = message.text.lower() == "all" or all(
        part.startswith("-") and part[1:].isdigit() for part in message.text.split()
    )
    return is_valid_input

# Function to show auto-delete settings
async def show_auto_delete_settings(client: Bot, chat_id: int, message_id: int = None):
    auto_delete_mode = await db.get_auto_delete_mode()
    delete_timer = await db.get_del_timer()
    mode_status = "Enabled ✅" if auto_delete_mode else "Disabled ❌"
    timer_text = get_readable_time(delete_timer)
    
    settings_text = (
        "» <b>Auto Delete Settings</b>\n\n"
        f"<blockquote>» <b>Auto Delete Mode:</b> {mode_status}</blockquote>\n"
        f"<blockquote>» <b>Delete Timer:</b> {timer_text}</blockquote>\n\n"
        "<b>Click buttons below to change settings</b>"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Toggle Mode", callback_data="auto_toggle"),
            InlineKeyboardButton("Set Timer", callback_data="auto_set_timer")
        ],
        [
            InlineKeyboardButton("Refresh", callback_data="auto_refresh"),
            InlineKeyboardButton("Back", callback_data="auto_back")
        ]
    ])
    
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    
    if message_id:
        try:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=keyboard
            )
        except Exception:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

# Function to show force-sub settings
async def show_force_sub_settings(client: Bot, chat_id: int, message_id: int = None):
    settings = await db.get_settings()
    force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
    mode_status = "🟢 Enabled" if force_sub_enabled else "🔴 Disabled"
    
    settings_text = (
        f"<b>›› Force Sub Settings</b>\n\n"
        f"<blockquote><b>Force Sub Mode:</b> {mode_status}</blockquote>\n\n"
    )
    
    channels = await db.show_channels()
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels[:5]:
            try:
                chat = await client.get_chat(ch_id)
                temp_off = await db.get_channel_temp_off(ch_id)
                status = "🔴 Off" if temp_off else "🟢 On"
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code> ({status})</b></blockquote>\n"
            except Exception:
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"
        
        if len(channels) > 5:
            settings_text += f"<blockquote><i>...and {len(channels) - 5} more.</i></blockquote>\n"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Add Channels", callback_data="fsub_add_channel"),
            InlineKeyboardButton("Remove Channels", callback_data="fsub_remove_channel")
        ],
        [
            InlineKeyboardButton("Toggle Mode", callback_data="fsub_toggle_mode")
        ],
        [
            InlineKeyboardButton("Single Off", callback_data="fsub_single_off"),
            InlineKeyboardButton("Fully Off", callback_data="fsub_fully_off")
        ],
        [
            InlineKeyboardButton("Channels List", callback_data="fsub_channels_list")
        ],
        [
            InlineKeyboardButton("Refresh", callback_data="fsub_refresh"),
            InlineKeyboardButton("Close", callback_data="fsub_close")
        ]
    ])
    
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    
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
        except Exception:
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

@Bot.on_message(filters.command('auto_delete') & filters.private & admin)
async def auto_delete_settings(client: Bot, message: Message):
    await show_auto_delete_settings(client, message.chat.id)

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Bot, message: Message):
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user

    async def safe_edit_media(image, caption, markup):
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption),
                reply_markup=markup
            )
        except Exception:
            try:
                await query.message.edit_text(caption, reply_markup=markup)
            except Exception:
                await query.answer("Operation failed, please try again", show_alert=True)

    try:
        if data == "help":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home'),
                [InlineKeyboardButton("• ᴄʟᴏꜱᴇ •", callback_data='close')
            ]])
            caption = HELP_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)
       
        elif data == "extramenu":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ •", callback_data="auto_delete"),
                    InlineKeyboardButton("• ꜰɪʟᴇ ꜱᴇᴛᴛɪɴɢꜱ •", callback_data="fsettings")
                ],
                [InlineKeyboardButton("• ғᴏʀᴄᴇ ꜱᴜʙ •", callback_data="forcesub")],
                [
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home'),
                    InlineKeyboardButton('• ᴄʟᴏꜱᴇ •', callback_data='close')
                ]
            ])
            caption = START_MSG.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)
        
        elif data == "auto_delete":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            member = await client.get_chat_member(query.message.chat.id, user.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await query.answer("❌ Only admins can use this feature.", show_alert=True)
                return
            await auto_delete_settings(client, query.message)
            await query.answer("Auto-Delete Settings")

        elif data == "forcesub":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            member = await client.get_chat_member(query.message.chat.id, user.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await query.answer("❌ Only admins can use this feature.", show_alert=True)
                return
            await force_sub_settings(client, query.message)
            await query.answer("Force-Sub Settings")

        elif data == "home":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• ʜᴇʟᴘ •", callback_data="help"),
                    InlineKeyboardButton("• ᴀʙᴏᴜᴛ •", callback_data="about")
                ],
                [
                    InlineKeyboardButton("• ᴜᴘᴅᴀᴛᴇꜱ •", url="https://t.me/CornXvilla"),
                    InlineKeyboardButton("• ᴘʀᴇᴍɪᴜᴍ •", callback_data="seeplans")
                ],
                [InlineKeyboardButton('• ᴇxᴛʀᴀ ꜰᴇᴀᴛᴜʀᴇꜱ •', callback_data='extramenu')]
            ])
            caption = START_MSG.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "about":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ᴄʜᴀɴɴᴇʟꜱ •', callback_data='channels'),
                    InlineKeyboardButton("• ᴄʀᴇᴅɪᴛ •", callback_data='info')
                ],
                [
                    InlineKeyboardButton('• close •', callback_data='close'),
                    InlineKeyboardButton("• ʜᴏᴍᴇ •", callback_data='home')
                ]
            ])
            caption = ABOUT_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "info":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ᴏᴡɴᴇʀ •', url='https://t.me/MrXeonTG'),
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home')
                ]
            ])
            caption = CREDIT_INFO.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "channels":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ᴍᴏᴠɪᴇꜱ •', url='http://t.me/MovieNationSpot'),
                    InlineKeyboardButton('• ꜱᴇʀɪᴇꜱ •', url='https://t.me/SeriesNationSpot')
                ],
                [
                    InlineKeyboardButton('• ᴀɴɪᴍᴇꜱ •', url='https://t.me/AnimeXeon'),
                    InlineKeyboardButton('• ᴀᴅᴜʟᴛ •', url='https://t.me/CornXvilla')
                ],
                [
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home'),
                    InlineKeyboardButton('• ᴄʟᴏꜱᴇ •', callback_data='close')
                ]
            ])
            caption = ABOUT_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "seeplans":
            await client.send_chat_action(query.message.chat.id, ChatAction.TYPING)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ʙᴜʏ ɴᴏᴡ •', url='https://t.me/Xeonflixadmin'),
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home')
                ]
            ])
            caption = PREPLANSS_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "close":
            try:
                await query.message.delete()
                if query.message.reply_to_message:
                    await query.message.reply_to_message.delete()
            except Exception:
                pass

        # [Rest of your existing callback handlers...]

    except Exception as e:
        await query.answer("An unexpected error occurred", show_alert=True)

# [Rest of your existing message handlers...]

@Bot.on_chat_member_updated()
async def handle_Chatmembers(client: Client, chat_member_updated: ChatMemberUpdated):    
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
async def handle_join_request(client: Client, chat_join_request):
    chat_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id
    if await db.reqChannel_exist(chat_id):
        mode = await db.get_channel_mode(chat_id)
        if mode == "on" and not await db.req_user_exist(chat_id, user_id):
            await db.req_user(chat_id, user_id)
            try:
                await client.approve_chat_join_request(chat_id, user_id)
            except Exception:
                pass

@Bot.on_message(filters.command('addchnl') & filters.private & admin)
async def add_force_sub(client: Client, message: Message):
    temp = await message.reply("<b><i>Waiting...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Close", callback_data="fsub_close")]]
        await temp.edit(
            "<blockquote><b>Usage:</b></blockquote>\n<code>/addchnl -100XXXXXXXXXX</code>\n\n"
            "<b>Add only one channel at a time.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return
    try:
        channel_id = int(args[1])
        all_channels = await db.show_channels()
        channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
        if channel_id in channel_ids_only:
            await temp.edit(f"<blockquote><b>Channel already exists:</b></blockquote>\n <blockquote><code>{channel_id}</code></blockquote>")
            return
        chat = await client.get_chat(channel_id)
        if chat.type != ChatType.CHANNEL:
            await temp.edit("<b>❌ Only public or private channels are allowed.</b>")
            return
        member = await client.get_chat_member(chat.id, "me")
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await temp.edit("<b>❌ Bot must be an admin in that channel.</b>")
            return
        link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
        await db.add_channel(channel_id)
        await temp.edit(
            f"<blockquote><b>✅ Force-sub Channel added successfully!</b></blockquote>\n\n"
            f"<blockquote><b>Name:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
            f"<blockquote><b>ID: <code>{channel_id}</code></b></blockquote>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except ValueError:
        await temp.edit("<blockquote><b>❌ Invalid channel ID!</b></blockquote>")
    except Exception as e:
        await temp.edit(f"<blockquote><b>❌ Failed to add channel:</b></blockquote>\n<code>{args[1]}</code>\n\n<i>{e}</i>", parse_mode=ParseMode.HTML)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
