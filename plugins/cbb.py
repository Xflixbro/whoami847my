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
from pyrogram.enums import ParseMode, ChatAction, ChatMemberStatus, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest
from bot import Bot
from config import *
from database.database import db

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
    mode_status = "Eɴᴀʙʟᴇᴅ ✅" if auto_delete_mode else "Dɪsᴀʙʟᴇᴅ ❌"
    timer_text = get_readable_time(delete_timer)
    settings_text = (
        "» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢꜱ</b>\n\n"
        f"<blockquote>» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ:</b> {mode_status}</blockquote>\n"
        f"<blockquote>» <b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ:</b> {timer_text}</blockquote>\n\n"
        "<b>Cʟɪᴄᴋ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴꜱ Tᴏ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢꜱ</b>"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("• Dɪsᴀʙʟᴇᴅ ❌" if auto_delete_mode else "• Eɴᴀʙʟᴇᴅ ✅", callback_data="auto_toggle"),
                InlineKeyboardButton(" Sᴇᴛ Tɪᴍᴇʀ •", callback_data="auto_set_timer")
            ],
            [
                InlineKeyboardButton("• Rᴇғʀᴇꜱʜ", callback_data="auto_refresh"),
                InlineKeyboardButton("Bᴀᴄᴋ •", callback_data="auto_back")
            ]
        ]
    )
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
async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    settings = await db.get_settings()
    force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
    mode_status = "🟢 Enabled" if force_sub_enabled else "🔴 Disabled"
    settings_text = f"<b>›› Request Fsub Settings:</b>\n\n<blockquote><b>Force Sub Mode: {mode_status}</b></blockquote>\n\n"
    channels = await db.show_channels()
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet. Use 𖤓 Add Channels 𖤓 to add channels.</i></blockquote>"
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
                InlineKeyboardButton("• Single Off •", callback_data="fsub_single_off"),
                InlineKeyboardButton(" Fully Off •", callback_data="fsub_fully_off")
            ],
            [
                InlineKeyboardButton(" Channels List •", callback_data="fsub_channels_list")
            ],
            [
                InlineKeyboardButton("• Refresh ", callback_data="fsub_refresh"),
                InlineKeyboardButton(" Close•", callback_data="fsub_close")
            ]
        ]
    )
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
    await db.set_temp_state(message.chat.id, "")
    await show_auto_delete_settings(client, message.chat.id)

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Client, message: Message):
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|rfs_ch_|rfs_toggle_|fsub_|auto_|set_|remove_|channels|start|info|seeplans|source)"))
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
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home'),
                    InlineKeyboardButton("• ᴄʟᴏꜱᴇ •", callback_data='close')
                ]
            ])
            caption = HELP_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "about":
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ᴄʜᴀɴɴᴇʟꜱ •', callback_data='channels'),
                    InlineKeyboardButton("• ᴄʀᴇᴅɪᴛ •", callback_data='info')
                ],
                [
                    InlineKeyboardButton('• ꜱᴏᴜʀᴄᴇ •', callback_data='source'),
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

        elif data == "home":
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                InlineKeyboardButton("• ʜᴇʟᴘ •", callback_data="help"),
                InlineKeyboardButton("• ᴀʙᴏᴜᴛ •", callback_data="about")
                ],
                [
                InlineKeyboardButton("• ᴄʜᴀɴɴᴇʟꜱ •", url="https://t.me/CornXvilla"),
                InlineKeyboardButton("• ᴘʀᴇᴍɪᴜᴍ •", callback_data="seeplans")
                ],
                [
                InlineKeyboardButton("• ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ •", callback_data="auto_delete"),
                InlineKeyboardButton("• ғᴏʀᴄᴇ ꜱᴜʙ •", callback_data="forcesub")
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

        elif data == "premium":
            try:
                await query.message.delete()
                await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo=QR_PIC,
                    caption=(
                        f"👋 {query.from_user.username if query.from_user.username else 'user'}\n\n"
                        f"💸 Premium Plans:\n\n"
                        f"○ {PRICE1} For 0 months premium\n\n"
                        f"○ {PRICE2} For 1 month premium\n\n"
                        f"○ {PRICE3} For 3 months premium\n\n"
                        f"○ {PRICE4} For 6 months premium\n\n"
                        f"○ {PRICE5} For 1 year premium\n\n\n"
                        f"💰 After payment send screenshot to - <code>{UPI_ID}</code>\n\n\n"
                        f"⚠️ Premium users get unlimited file storage\n\n\n"
                        f"⌛ Message screenshot with payment details & UTR number"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Help", callback_data="help"),
                            InlineKeyboardButton("See Plans", callback_data="seeplans")
                        ],
                        [
                            InlineKeyboardButton("Bot Info", callback_data="info"),
                            InlineKeyboardButton("24/7 Support", url=SCREENSHOT_URL)
                        ]
                    ])
                )
            except Exception:
                await query.answer("Failed to show premium plans", show_alert=True)

        elif data == "seeplans":
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

        elif data == "source":
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ᴏᴡɴᴇʀ •', url='https://t.me/MrXeonTG'),
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home')
                ]
            ])
            caption = SOURCE_TXT.format(
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

        elif data.startswith("auto_"):
            if data == "auto_toggle":
                current_mode = await db.get_auto_delete_mode()
                new_mode = not current_mode
                await db.set_auto_delete_mode(new_mode)
                await show_auto_delete_settings(client, query.message.chat.id, query.message.id)
                await query.answer(f"<blockquote><b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ {'Eɴᴀʙʟᴇᴅ' if new_mode else 'Dɪꜱᴀʙʟᴇᴅ'}!</b></blockquote>")
            
            elif data == "auto_set_timer":
                await db.set_temp_state(query.message.chat.id, "awaiting_timer_input")
                try:
                    await query.message.reply_photo(
                        photo=random.choice(RANDOM_IMAGES),
                        caption=(
                            "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ꜰᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                            "<blockquote><b>Eхᴀᴄᴀᴍᴘʟᴇ: 300 (ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ)</b></blockquote>"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    await query.message.reply(
                        "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ꜰᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.</b></blockquote>\n"
                        "<blockquote><b>Eхᴀᴄᴀᴍᴘʟᴇ: 300 (ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ)</b></blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                await query.answer("<blockquote><b>Eɴᴛᴇʀ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ!</b></blockquote>")
            
            elif data == "auto_refresh":
                await show_auto_delete_settings(client, query.message.chat.id, query.message.id)
                await query.answer("<blockquote><b>Sᴇᴛᴛɪɴɢꜱ ʀᴇꜰʀᴇꜱʜᴇᴅ!</b></blockquote>")
            
            elif data == "auto_back":
                await db.set_temp_state(query.message.chat.id, "")
                await query.message.delete()
                await query.answer("<blockquote><b>Bᴀᴄᴋ ᴛᴏ ᴘʀᴇᴠɪᴏᴜꜱ ᴍᴇɴᴜ!</b></blockquote>")

        elif data.startswith("fsub_"):
            if data == "fsub_add_channel":
                await db.set_temp_state(query.message.chat.id, "awaiting_add_channel_input")
                await client.edit_message_text(
                    chat_id=query.message.chat.id,
                    message_id=query.message.id,
                    text="<blockquote><b>Give me the channel IDs (space-separated).</b>\n<b>Example: -1001234567890 -1000987654321</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("•Back•", callback_data="fsub_back"),
                            InlineKeyboardButton("•Close•", callback_data="fsub_close")
                        ]
                    ]),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await query.answer("Provide the channel IDs (space-separated).")

            elif data == "fsub_remove_channel":
                await db.set_temp_state(query.message.chat.id, "awaiting_remove_channel_input")
                await client.edit_message_text(
                    chat_id=query.message.chat.id,
                    message_id=query.message.id,
                    text="<blockquote><b>Give me the channel IDs (space-separated) or type '<code>all</code>' to remove all channels.</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("•Back•", callback_data="fsub_back"),
                            InlineKeyboardButton("•Close•", callback_data="fsub_close")
                        ]
                    ]),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await query.answer("Provide the channel IDs (space-separated) or type 'all'.")

            elif data == "fsub_toggle_mode":
                temp = await query.message.reply("<b><i>Wait a sec...</i></b>", quote=True)
                channels = await db.show_channels()
                if not channels:
                    await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
                    await query.answer()
                    return
                buttons = []
                for ch_id in channels:
                    try:
                        chat = await client.get_chat(ch_id)
                        mode = await db.get_channel_mode(ch_id)
                        status = "🟢" if mode == "on" else "🔴"
                        title = f"{status} {chat.title}"
                        buttons.append([InlineKeyboardButton(title, callback_data=f"rfs_ch_{ch_id}")])
                    except Exception:
                        buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])
                buttons.append([InlineKeyboardButton("Close ✖️", callback_data="fsub_close")])
                await temp.edit(
                    "<blockquote><b>⚡ Select a channel to toggle force-sub mode:</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                await query.answer()

            elif data == "fsub_channels_list":
                await show_channels_list(client, query.message.chat.id, query.message.id)
                await query.answer("Showing channels list!")

            elif data == "fsub_single_off":
                temp = await query.message.reply("<b><i>Wait a sec...</i></b>", quote=True)
                channels = await db.show_channels()
                if not channels:
                    await temp.edit("<blockquote><b>❌ No force-sub channels found.</b></blockquote>")
                    await query.answer()
                    return
                buttons = []
                for ch_id in channels:
                    try:
                        chat = await client.get_chat(ch_id)
                        temp_off = await db.get_channel_temp_off(ch_id)
                        status = "🔴 Off" if temp_off else "🟢 On"
                        title = f"{status} {chat.title}"
                        buttons.append([InlineKeyboardButton(title, callback_data=f"fsub_temp_off_{ch_id}")])
                    except Exception:
                        buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"fsub_temp_off_{ch_id}")])
                buttons.append([InlineKeyboardButton("Close ✖️", callback_data="fsub_close")])
                await temp.edit(
                    "<blockquote><b>⚡ Select a channel to toggle temporary off mode:</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                await query.answer()

            elif data == "fsub_fully_off":
                await show_fully_off_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Showing fully off settings!")

            elif data == "fsub_toggle_full":
                settings = await db.get_settings()
                current_mode = settings.get('FORCE_SUB_ENABLED', True)
                new_mode = not current_mode
                await db.update_setting('FORCE_SUB_ENABLED', new_mode)
                await show_fully_off_settings(client, query.message.chat.id, query.message.id)
                await query.answer(f"Force-sub mode {'enabled' if new_mode else 'disabled'}!")

            elif data == "fsub_full_refresh":
                await show_fully_off_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Settings refreshed!")

            elif data == "fsub_refresh":
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Settings refreshed!")

            elif data == "fsub_close":
                await db.set_temp_state(query.message.chat.id, "")
                await query.message.delete()
                await query.answer("Settings closed!")

            elif data == "fsub_back":
                await db.set_temp_state(query.message.chat.id, "")
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Back to settings!")

            elif data.startswith("fsub_temp_off_"):
                ch_id = int(query.data.split("_")[-1])
                try:
                    current_temp_off = await db.get_channel_temp_off(ch_id)
                    new_temp_off = not current_temp_off
                    await db.set_channel_temp_off(ch_id, new_temp_off)
                    chat = await client.get_chat(ch_id)
                    status = "🔴 Off" if new_temp_off else "🟢 On"
                    await query.message.edit_text(
                        f"<blockquote><b>✅ Temporary mode toggled for channel:</b></blockquote>\n\n"
                        f"<blockquote><b>Name:</b> <a href='https://t.me/{chat.username}'>{chat.title}</a></blockquote>\n"
                        f"<blockquote><b>ID:</b> <code>{ch_id}</code></blockquote>\n"
                        f"<blockquote><b>Mode:</b> {status} {'Disabled' if new_temp_off else 'Enabled'}</blockquote>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("• Back •", callback_data="fsub_single_off")]
                        ]),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    await query.answer(f"Channel {ch_id} {'disabled' if new_temp_off else 'enabled'} temporarily!")
                except Exception as e:
                    await query.message.edit_text(
                        f"<blockquote><b>❌ Failed to toggle temporary mode for channel:</b></blockquote>\n<code>{ch_id}</code>\n\n<i>{e}</i>",
                        parse_mode=ParseMode.HTML
                    )
                    await query.answer()

        elif data.startswith("rfs_ch_"):
            ch_id = int(query.data.split("_")[-1])
            try:
                current_mode = await db.get_channel_mode(ch_id)
                new_mode = "off" if current_mode == "on" else "on"
                await db.set_channel_mode(ch_id, new_mode)
                chat = await client.get_chat(ch_id)
                status = "🟢" if new_mode == "on" else "🔴"
                await query.message.edit_text(
                    f"<blockquote><b>✅ Mode toggled for channel:</b></blockquote>\n\n"
                    f"<blockquote><b>Name:</b> <a href='https://t.me/{chat.username}'>{chat.title}</a></blockquote>\n"
                    f"<blockquote><b>ID:</b> <code>{ch_id}</code></blockquote>\n"
                    f"<blockquote><b>Mode:</b> {status} {'Enabled' if new_mode == 'on' else 'Disabled'}</blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• Back •", callback_data="fsub_toggle_mode")]
                    ]),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await query.answer(f"Force-sub {'enabled' if new_mode == 'on' else 'disabled'} for channel {ch_id}")
            except Exception as e:
                await query.message.edit_text(
                    f"<blockquote><b>❌ Failed to toggle mode for channel:</b></blockquote>\n<code>{ch_id}</code>\n\n<i>{e}</i>",
                    parse_mode=ParseMode.HTML
                )
                await query.answer()

        elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
            type = data.split("_")[1]
            try:
                await db.set_temp_state(query.message.chat.id, f"set_{type}")
                await query.message.reply_text(f"Please send the image you want to set as {type} image.")
            except Exception:
                await query.answer("Failed to set state", show_alert=True)

        elif data.startswith("remove_"):
            type = data.split("_")[1]
            try:
                images = await db.get_images(type)
                if not images:
                    await query.message.reply_text(f"There are no {type} images set.")
                else:
                    nums = list(range(1, len(images) + 1))
                    text = f"Current {type} images: {', '.join(map(str, nums))}\nTo remove a single image, use /rev_{type} <number>\nTo remove all, use /rev_all_{type}"
                    await query.message.reply_text(text)
            except Exception:
                await query.answer("Failed to get image list", show_alert=True)

    except Exception as e:
        await query.answer("An unexpected error occurred", show_alert=True)
    
    await query.answer()

@Bot.on_message(filters.private & admin & filters.create(timer_input_filter), group=2)
async def set_timer(client: Bot, message: Message):
    chat_id = message.chat.id
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError("Duration must be a positive integer")
        await db.set_del_timer(duration)
        new_timer = await db.get_del_timer()
        if new_timer == duration:
            try:
                await message.reply_photo(
                    photo=random.choice(RANDOM_IMAGES),
                    caption=f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                await message.reply(
                    f"<blockquote><b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ ʜᴀꜱ ʙᴇᴇɴ ꜱᴇᴛ ᴛᴏ {get_readable_time(duration)}.</b></blockquote>",
                    parse_mode=ParseMode.HTML
                )
        else:
            await message.reply(
                "<blockquote><b>Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        await db.set_temp_state(chat_id, "")
    except ValueError:
        try:
            await message.reply_photo(
                photo=random.choice(RANDOM_IMAGES),
                caption="<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴘᴏꜱɪᴛɪᴠᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await message.reply(
                "<blockquote><b>Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴘᴏꜱɪᴛɪᴠᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )

@Bot.on_message(filters.private & admin & filters.create(fsub_state_filter), group=1)
async def handle_channel_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    try:
        if state == "awaiting_add_channel_input":
            channel_ids = message.text.split()
            all_channels = await db.show_channels()
            channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
            report = ""
            success_count = 0
            for channel_id in channel_ids:
                try:
                    channel_id = int(channel_id)
                    if channel_id in channel_ids_only:
                        report += f"<blockquote><b>Channel already exists:</b> <code>{channel_id}</code></blockquote>\n"
                        continue
                    chat = await client.get_chat(channel_id)
                    if chat.type != ChatType.CHANNEL:
                        report += f"<blockquote><b>❌ Only public or private channels are allowed:</b> <code>{channel_id}</code></blockquote>\n"
                        continue
                    member = await client.get_chat_member(chat.id, "me")
                    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                        report += f"<blockquote><b>❌ Bot must be an admin in that channel:</b> <code>{channel_id}</code></blockquote>\n"
                        continue
                    link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
                    await db.add_channel(channel_id)
                    report += f"<blockquote><b>✅ Channel added:</b> <a href='{link}'>{chat.title}</a> - <code>{channel_id}</code></blockquote>\n"
                    success_count += 1
                except ValueError:
                    report += f"<blockquote><b>❌ Invalid channel ID:</b> <code>{channel_id}</code></blockquote>\n"
                except Exception as e:
                    report += f"<blockquote><b>❌ Failed to add channel:</b> <code>{channel_id}</code> - <i>{e}</i></blockquote>\n"
            await message.reply(
                f"<b>📋 Add Channel Report:</b>\n\n{report}",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
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
                channel_ids = message.text.split()
                report = ""
                for ch_id in channel_ids:
                    try:
                        ch_id = int(ch_id)
                        if ch_id in all_channels:
                            await db.rem_channel(ch_id)
                            report += f"<blockquote><b>✅ Channel removed:</b> <code>{ch_id}</code></blockquote>\n"
                        else:
                            report += f"<blockquote><b>❌ Channel not found:</b> <code>{ch_id}</code></blockquote>\n"
                    except ValueError:
                        report += f"<blockquote><b>❌ Invalid channel ID:</b> <code>{ch_id}</code></blockquote>\n"
                await message.reply(
                    f"<b>📋 Remove Channel Report:</b>\n\n{report}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id)
    except Exception as e:
        await message.reply(
            f"<blockquote><b>❌ Failed to process input:</b></blockquote>\n<code>{message.text}</code>\n\n<i>{e}</i>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)

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
