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
import logging
from urllib.parse import quote
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatMemberUpdated
from bot import Bot
from helper_func import *
from database.database import *
from config import OWNER_ID

logger = logging.getLogger(__name__)

async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    """Show the force-sub settings menu with channel list and controls."""
    settings_text = "<b>›› Request Fsub Settings:</b>\n\n"
    channels = await db.show_channels()
    
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet. Use 𖤓 Add Channels 𖤓 to add a channel.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels:
            channel_info = await db.get_channel_info(ch_id)
            if channel_info:
                title = channel_info.get('title', f"Channel {ch_id}")
                link = quote(channel_info.get('invite_link', ''))
                mode = channel_info.get('mode', 'off')
                status = "🟢" if mode == "on" else "🔴"
                settings_text += f"<blockquote><b>{status} <a href='{link}'>{title}</a> - <code>{ch_id}</code></b></blockquote>\n"
            else:
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Add Channels ", callback_data="fsub_add_channel"),
                InlineKeyboardButton(" Remove Channels •", callback_data="fsub_remove_channel")
            ],
            [
                InlineKeyboardButton("• Toggle Mode •", callback_data="fsub_toggle_mode")
            ],
            [
                InlineKeyboardButton("• Refresh ", callback_data="fsub_refresh"),
                InlineKeyboardButton(" Close •", callback_data="fsub_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if 'RANDOM_IMAGES' in globals() and RANDOM_IMAGES else START_PIC

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
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Sent photo message with image {selected_image}")
        except Exception as e:
            logger.error(f"Failed to send photo message with image {selected_image}: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info("Sent text-only message as fallback")

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Client, message: Message):
    logger.info(f"Received /forcesub command from chat {message.chat.id}")
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    logger.info(f"Received callback query with data: {data} in chat {chat_id}")

    if data == "fsub_add_channel":
        await db.set_temp_state(chat_id, "awaiting_add_channel_input")
        logger.info(f"Set state to 'awaiting_add_channel_input' for chat {chat_id}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Give me the channel IDs (space-separated).</b>\n<b>Example: -100123456789 -100987654321</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Back •", callback_data="fsub_back"),
                    InlineKeyboardButton("• Close •", callback_data="fsub_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Provide channel IDs (space-separated).")

    elif data == "fsub_remove_channel":
        await db.set_temp_state(chat_id, "awaiting_remove_channel_input")
        logger.info(f"Set state to 'awaiting_remove_channel_input' for chat {chat_id}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<blockquote><b>Give me the channel ID or type '<code>all</code>' to remove all channels.</b></blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Back •", callback_data="fsub_back"),
                    InlineKeyboardButton("• Close •", callback_data="fsub_close")
                ]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Please provide the channel ID or type 'all'.")

    elif data == "fsub_toggle_mode":
        temp = await callback.message.reply("<b><i>Wait a sec...</i></b>", quote=True)
        channels = await db.show_channels()

        if not channels:
            await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
            await callback.answer()
            return

        buttons = []
        for ch_id in channels:
            channel_info = await db.get_channel_info(ch_id)
            if channel_info:
                mode = channel_info.get('mode', 'off')
                title = channel_info.get('title', f"Channel {ch_id}")
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(f"{status} {title}", callback_data=f"rfs_ch_{ch_id}")])
            else:
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])

        buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])

        await temp.edit(
            "<blockquote><b>⚡ Select a channel to toggle force-sub mode:</b></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer()

    elif data == "fsub_refresh":
        await show_force_sub_settings(client, chat_id, callback.message.id)
        await callback.answer("Settings refreshed!")

    elif data == "fsub_close":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer("Settings closed!")

    elif data == "fsub_back":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Back to settings!")

    elif data == "fsub_cancel":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Action cancelled!")

async def fsub_state_filter(_, __, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Checking fsub_state_filter for chat {chat_id}: state={state}, message_text={message.text}")
    if state not in ["awaiting_add_channel_input", "awaiting_remove_channel_input"]:
        logger.info(f"State {state} not relevant for fsub_state_filter in chat {chat_id}")
        return False
    if not message.text:
        logger.info(f"No message text provided in chat {chat_id}")
        return False
    is_valid_input = message.text.lower() == "all" or all(
        (part.startswith("-") and part[1:].isdigit()) for part in message.text.split()
    )
    logger.info(f"Input validation for chat {chat_id}: is_valid_input={is_valid_input}")
    return is_valid_input

@Bot.on_message(filters.private & admin & filters.create(fsub_state_filter), group=1)
async def handle_channel_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Handling input: {message.text} for state: {state} in chat {chat_id}")

    try:
        if state == "awaiting_add_channel_input":
            channel_ids = [int(ch_id) for ch_id in message.text.split()]
            all_channels = await db.show_channels()
            added_channels = []
            failed_channels = []

            for channel_id in channel_ids:
                if channel_id in all_channels:
                    failed_channels.append((channel_id, "Already exists"))
                    continue

                try:
                    chat = await client.get_chat(channel_id)
                    if chat.type != ChatType.CHANNEL:
                        failed_channels.append((channel_id, "Not a channel"))
                        continue

                    member = await client.get_chat_member(chat.id, "me")
                    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                        failed_channels.append((channel_id, "Bot not admin"))
                        continue

                    link_type = "join_request"
                    link = await client.create_chat_invite_link(chat.id, creates_join_request=True)
                    await db.add_channel(channel_id, chat.title, link.invite_link, link_type)
                    added_channels.append((channel_id, chat.title, link.invite_link))

                except Exception as e:
                    logger.error(f"Failed to add channel {channel_id}: {e}")
                    failed_channels.append((channel_id, str(e)))

            response_text = ""
            if added_channels:
                response_text += "<blockquote><b>✅ Channels added successfully:</b></blockquote>\n"
                for ch_id, title, link in added_channels:
                    response_text += f"<blockquote><b><a href='{quote(link)}'>{title}</a> - <code>{ch_id}</code></b></blockquote>\n"
            if failed_channels:
                response_text += "<blockquote><b>❌ Failed to add channels:</b></blockquote>\n"
                for ch_id, reason in failed_channels:
                    response_text += f"<blockquote><b><code>{ch_id}</code> - {reason}</b></blockquote>\n"

            await message.reply(response_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id)

        elif state == "awaiting_remove_channel_input":
            all_channels = await db.show_channels()
            if message.text.lower() == "all":
                if not all_channels:
                    await message.reply("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
                    await db.set_temp_state(chat_id, "")
                    await show_force_sub_settings(client, chat_id)
                    return
                for ch_id in all_channels:
                    await db.rem_channel(ch_id)
                await message.reply("<blockquote><b>✅ All force-sub channels removed.</b></blockquote>")
            else:
                ch_id = int(message.text)
                if ch_id in all_channels:
                    await db.rem_channel(ch_id)
                    await message.reply(f"<blockquote><b>✅ Channel removed:</b></blockquote>\n<blockquote><code>{ch_id}</code></blockquote>")
                else:
                    await message.reply(f"<blockquote><b>❌ Channel not found:</b></blockquote>\n<blockquote><code>{ch_id}</code></blockquote>")
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id)

    except ValueError:
        logger.error(f"Invalid input received: {message.text}")
        await message.reply("<blockquote><b>❌ Invalid channel ID(s)!</b></blockquote>")
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)
    except Exception as e:
        logger.error(f"Failed to process channel input {message.text}: {e}")
        await message.reply(
            f"<blockquote><b>❌ Failed to process channel(s):</b></blockquote>\n<code>{message.text}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)

@Bot.on_message(filters.command('fsub_mode') & filters.private & admin)
async def change_force_sub_mode(client: Client, message: Message):
    temp = await message.reply("<b><i>Wait a sec...</i></b>", quote=True)
    channels = await db.show_channels()

    if not channels:
        await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
        return

    buttons = []
    for ch_id in channels:
        channel_info = await db.get_channel_info(ch_id)
        if channel_info:
            mode = channel_info.get('mode', 'off')
            title = channel_info.get('title', f"Channel {ch_id}")
            status = "🟢" if mode == "on" else "🔴"
            buttons.append([InlineKeyboardButton(f"{status} {title}", callback_data=f"rfs_ch_{ch_id}")])
        else:
            buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])

    buttons.append([InlineKeyboardButton("Close ✖️", callback_data="close")])

    await temp.edit(
        "<blockquote><b>⚡ Select a channel to toggle force-sub mode:</b></blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@Bot.on_callback_query(filters.regex(r"^rfs_ch_"))
async def toggle_channel_mode(client: Client, callback: CallbackQuery):
    ch_id = int(callback.data.split("_")[-1])
    logger.info(f"Toggling mode for channel {ch_id} by user {callback.from_user.id}")

    try:
        channel_info = await db.get_channel_info(ch_id)
        if not channel_info:
            await callback.message.edit_text(
                f"<blockquote><b>❌ Channel not found:</b></blockquote>\n<code>{ch_id}</code>",
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Channel not found")
            return

        current_mode = channel_info.get('mode', 'off')
        new_mode = "off" if current_mode == "on" else "on"

        chat = await client.get_chat(ch_id)
        if chat.type != ChatType.CHANNEL:
            await callback.message.edit_text(
                f"<blockquote><b>❌ Not a channel:</b></blockquote>\n<code>{ch_id}</code>",
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Not a channel")
            return

        link_type = "join_request"
        link = await client.create_chat_invite_link(ch_id, creates_join_request=True)
        
        await db.set_channel_mode(ch_id, new_mode, link.invite_link, link_type)
        
        status = "🟢" if new_mode == "on" else "🔴"
        await callback.message.edit_text(
            f"<blockquote><b>✅ Mode toggled for channel:</b></blockquote>\n\n"
            f"<blockquote><b>Name:</b> <a href='{quote(link.invite_link)}'>{chat.title}</a></blockquote>\n"
            f"<blockquote><b>ID:</b> <code>{ch_id}</code></blockquote>\n"
            f"<blockquote><b>Mode:</b> {status} {'Enabled' if new_mode == 'on' else 'Disabled'}</blockquote>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• Back •", callback_data="fsub_toggle_mode")]
            ]),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer(f"Force-sub {'enabled' if new_mode == 'on' else 'disabled'} for channel {ch_id}")
    except Exception as e:
        logger.error(f"Failed to toggle mode for channel {ch_id}: {e}")
        await callback.message.edit_text(
            f"<blockquote><b>❌ Failed to toggle mode for channel:</b></blockquote>\n<code>{ch_id}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await callback.answer()

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
        if not await db.req_user_exist(chat_id, user_id):
            await db.req_user(chat_id, user_id)

@Bot.on_message(filters.command('addchnl') & filters.private & admin)
async def add_force_sub(client: Client, message: Message):
    temp = await message.reply("<b><i>Waiting...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Close", callback_data="close")]]
        await temp.edit(
            "<blockquote><b>Usage:</b></blockquote>\n<code>/addchnl -100XXXXXXXXXX -100YYYYYYYYYY</code>\n\n"
            "<b>Add one or more channel IDs (space-separated).</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    try:
        channel_ids = [int(ch_id) for ch_id in args[1].split()]
        all_channels = await db.show_channels()
        added_channels = []
        failed_channels = []

        for channel_id in channel_ids:
            if channel_id in all_channels:
                failed_channels.append((channel_id, "Already exists"))
                continue

            try:
                chat = await client.get_chat(channel_id)
                if chat.type != ChatType.CHANNEL:
                    failed_channels.append((channel_id, "Not a channel"))
                    continue

                member = await client.get_chat_member(chat.id, "me")
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    failed_channels.append((channel_id, "Bot not admin"))
                    continue

                link_type = "join_request"
                link = await client.create_chat_invite_link(chat.id, creates_join_request=True)
                await db.add_channel(channel_id, chat.title, link.invite_link, link_type)
                added_channels.append((channel_id, chat.title, link.invite_link))

            except Exception as e:
                logger.error(f"Failed to add channel {channel_id}: {e}")
                failed_channels.append((channel_id, str(e)))

        response_text = ""
        if added_channels:
            response_text += "<blockquote><b>✅ Channels added successfully:</b></blockquote>\n"
            for ch_id, title, link in added_channels:
                response_text += f"<blockquote><b><a href='{quote(link)}'>{title}</a> - <code>{ch_id}</code></b></blockquote>\n"
        if failed_channels:
            response_text += "<blockquote><b>❌ Failed to add channels:</b></blockquote>\n"
            for ch_id, reason in failed_channels:
                response_text += f"<blockquote><b><code>{ch_id}</code> - {reason}</b></blockquote>\n"

        await temp.edit(response_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except ValueError:
        await temp.edit("<blockquote><b>❌ Invalid channel ID(s)!</b></blockquote>")
    except Exception as e:
        logger.error(f"Failed to add channels: {e}")
        await temp.edit(
            f"<blockquote><b>❌ Failed to add channels:</b></blockquote>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('delchnl') & filters.private & admin)
async def del_force_sub_channel(client: Client, message: Message):
    temp = await message.reply("<b><i>Waiting...</i></b>", quote=True)
    args = message.text.split(maxsplit=1)

    all_channels = await db.show_channels()

    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Close", callback_data="close")]]
        await temp.edit(
            "<blockquote><b>Usage:</b></blockquote>\n<code>/delchnl -100XXXXXXXXXX</code>\n\n"
            "<b>Or type:</b> <code>/delchnl all</code> to remove all channels.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if args[1].lower() == "all":
        if not all_channels:
            await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
            return
        for ch_id in all_channels:
            await db.rem_channel(ch_id)
        await temp.edit("<blockquote><b>✅ All force-sub channels removed.</b></blockquote>")
        return

    try:
        ch_id = int(args[1])
        if ch_id in all_channels:
            await db.rem_channel(ch_id)
            await temp.edit(f"<blockquote><b>✅ Channel removed:</b></blockquote>\n<blockquote><code>{ch_id}</code></blockquote>")
        else:
            await temp.edit(f"<blockquote><b>❌ Channel not found:</b></blockquote>\n<blockquote><code>{ch_id}</code></blockquote>")
    except ValueError:
        await temp.edit("<blockquote><b>❌ Invalid channel ID!</b></blockquote>")

@Bot.on_message(filters.command('listchnl') & filters.private & admin)
async def list_force_sub_channels(client: Client, message: Message):
    temp = await message.reply("<b><i>Fetching channels...</i></b>", quote=True)
    try:
        channels = await db.show_channels()

        if not channels:
            await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
            return

        text = "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels:
            channel_info = await db.get_channel_info(ch_id)
            if channel_info:
                title = channel_info.get('title', f"Channel {ch_id}")
                link = quote(channel_info.get('invite_link', ''))
                mode = channel_info.get('mode', 'off')
                status = "🟢" if mode == "on" else "🔴"
                text += f"<blockquote><b>{status} <a href='{link}'>{title}</a> - <code>{ch_id}</code></b></blockquote>\n"
            else:
                text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

        buttons = [[InlineKeyboardButton("Close", callback_data="close")]]
        await temp.edit(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Failed to list channels: {e}")
        await temp.edit("<blockquote><b>❌ Failed to fetch channels:</b></blockquote>")

@Bot.on_message(filters.command('checkfsub') & filters.private)
async def check_force_sub(client: Client, message: Message):
    user_id = message.from_user.id
    channels = await db.show_channels()
    if not channels:
        await message.reply("<blockquote><b>✅ No force-sub channels configured.</b></blockquote>")
        return

    not_subscribed = []
    buttons = []

    for ch_id in channels:
        try:
            member = await client.get_chat_member(ch_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                channel_info = await db.get_channel_info(ch_id)
                if channel_info:
                    title = channel_info.get('title', f"Channel {ch_id}")
                    link = quote(channel_info.get('invite_link', ''))
                    not_subscribed.append((ch_id, title, link))
                    buttons.append([InlineKeyboardButton(f"Join {title}", url=link)])
        except Exception as e:
            logger.error(f"Error checking membership for user {user_id} in channel {ch_id}: {e}")
            continue

    if not_subscribed:
        text = "<blockquote><b>❌ You must join the following channels to proceed:</b></blockquote>\n\n"
        for _, title, link in not_subscribed:
            text += f"<blockquote><b><a href='{link}'>{title}</a></b></blockquote>\n"
        
        buttons.append([InlineKeyboardButton("🔄 Try accessing again", callback_data="check_fsub")])
        await message.reply(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    else:
        await message.reply("<blockquote><b>✅ You are subscribed to all required channels!</b></blockquote>")

@Bot.on_callback_query(filters.regex(r"^check_fsub$"))
async def check_fsub_callback(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    channels = await db.show_channels()
    if not channels:
        await callback.message.edit_text("<blockquote><b>✅ No force-sub channels configured.</b></blockquote>")
        await callback.answer("No channels to check")
        return

    not_subscribed = []
    buttons = []

    for ch_id in channels:
        try:
            member = await client.get_chat_member(ch_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                channel_info = await db.get_channel_info(ch_id)
                if channel_info:
                    title = channel_info.get('title', f"Channel {ch_id}")
                    link = quote(channel_info.get('invite_link', ''))
                    not_subscribed.append((ch_id, title, link))
                    buttons.append([InlineKeyboardButton(f"Join {title}", url=link)])
        except Exception as e:
            logger.error(f"Error checking membership for user {user_id} in channel {ch_id}: {e}")
            continue

    if not_subscribed:
        text = "<blockquote><b>❌ You must join the following channels:</b></blockquote>\n\n"
        for _, title, link in not_subscribed:
            text += f"<blockquote><b><a href='{link}'>{title}</a></b></blockquote>\n"

        buttons.append([InlineKeyboardButton("🔄 Try again", callback_data="check_fsub")])
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        await callback.answer("Please join the channels")
    else:
        await callback.message.edit_text("<blockquote><b>✅ Access granted! You are subscribed to all required channels.</b></blockquote>")
        await callback.answer("Access granted!")

@Bot.on_callback_query(filters.regex(r"^close$"))
async def close_callback(client: Client, callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.answer()
    except Exception as e:
        logger.error(f"Error closing message: {e}")
        await callback.answer("Failed to close", show_alert=True)
