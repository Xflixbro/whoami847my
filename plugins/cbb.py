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
import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType
from pyrogram.types import InputMediaPhoto, ChatMemberUpdated, ChatJoinRequest, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import *
from database.database import db
from helper_func import get_readable_time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

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
    try:
        logger.info(f"Showing auto-delete settings for chat {chat_id}")
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
            except Exception as e:
                logger.error(f"Failed to edit media for auto-delete settings: {e}")
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
            except Exception as e:
                logger.error(f"Failed to send photo for auto-delete settings: {e}")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                )
    except Exception as e:
        logger.error(f"Error in show_auto_delete_settings: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=f"<b>Error loading auto-delete settings:</b> {e}",
            parse_mode=ParseMode.HTML
        )

# Function to show force-sub settings
async def show_force_sub_settings(client: any, chat_id: int, message_id: int = None):
    try:
        logger.info(f"Showing force-sub settings for chat {chat_id}")
        settings = await db.get_settings()
        logger.debug(f"Settings retrieved: {settings}")
        force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
        mode_status = "🟢 Enabled" if force_sub_enabled else "🔴 Disabled"
        
        settings_text = (
            f"<b>›› Force Sub Settings</b>\n\n"
            f"<blockquote><b>Force Sub Mode:</b> {mode_status}</blockquote>\n\n"
        )
        
        channels = await db.show_channels()
        logger.debug(f"Channels retrieved: {channels}")
        if not channels:
            settings_text += "<blockquote><i>No channels configured yet.</i></blockquote>"
        else:
            settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
            for ch_id in channels[:5]:
                try:
                    chat = await client.get_chat(ch_id)
                    temp_off = await db.get_channel_temp_off(ch_id)
                    status = "🔴 Off" if temp_off else "🟢 On"
                    try:
                        link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                    except Exception as link_error:
                        logger.error(f"Failed to export invite link for channel {ch_id}: {link_error}")
                        link = "N/A"
                    settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code> ({status})</b></blockquote>\n"
                except Exception as e:
                    logger.error(f"Failed to process channel {ch_id}: {e}")
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
            except Exception as e:
                logger.error(f"Failed to edit message for force-sub settings: {e}")
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
            except Exception as e:
                logger.error(f"Failed to send photo for force-sub settings: {e}")
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
    except Exception as e:
        logger.error(f"Error in show_force_sub_settings: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=f"<b>❌ Error loading force-sub settings:</b> {e}",
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('auto_delete') & filters.private & admin)
async def auto_delete_settings(client: Bot, message: Message):
    logger.info(f"/auto_delete command by user {message.from_user.id}")
    await db.set_temp_state(message.chat.id, "")
    await show_auto_delete_settings(client, message.chat.id)

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Bot, message: Message):
    logger.info(f"/forcesub command by user {message.from_user.id}")
    await db.set_temp_state(message.chat.id, "")
    await show_force_sub_settings(client, message.chat.id)

# Non-admin callback handler
@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|channels|start|info|seeplans|source)"))
async def cb_handler_non_admin(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user
    logger.info(f"Non-admin callback {data} by user {user.id}")

    async def safe_edit_media(image, caption, markup):
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption),
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Failed to edit media: {e}")
            try:
                await query.message.edit_text(caption, reply_markup=markup)
            except Exception as e:
                logger.error(f"Failed to edit text: {e}")
                await query.answer("Operation failed, please try again", show_alert=True)

    try:
        if data == "help":
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('• ʜᴏᴍᴇ •', callback_data='home'),
                    InlineKeyboardButton("• ᴄʟᴏꜱᴇ •", callback_data='close')
                ],
                [
                    InlineKeyboardButton("• ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ •", callback_data="auto_delete"),
                    InlineKeyboardButton("• ғᴏʀᴄᴇ ꜱᴜʙ •", callback_data="forcesub")
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
            await query.answer("Help Menu")

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
            await query.answer("Home Menu")

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
            await query.answer("About Menu")

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
            await query.answer("Credit Info")

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
            await query.answer("Channels Menu")

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
                await query.answer("Premium Plans")
            except Exception as e:
                logger.error(f"Failed to show premium plans: {e}")
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
            await query.answer("See Plans")

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
            await query.answer("Source Info")

        elif data == "close":
            try:
                await query.message.delete()
                if query.message.reply_to_message:
                    await query.message.reply_to_message.delete()
                await query.answer("Closed")
            except Exception as e:
                logger.error(f"Failed to close message: {e}")
                await query.answer("Failed to close", show_alert=True)

        elif data == "forcesub":
            await query.answer("This feature is only available to admins.", show_alert=True)

    except Exception as e:
        logger.error(f"Unexpected error in non-admin callback {data}: {e}")
        await query.answer(f"An unexpected error occurred: {e}", show_alert=True)

# Admin callback handler
@Bot.on_callback_query(filters.regex(r"^(rfs_ch_|rfs_toggle_|fsub_|auto_|set_|remove_|forcesub)") & admin)
async def cb_handler_admin(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user
    logger.info(f"Admin callback {data} by user {user.id}")

    async def safe_edit_media(image, caption, markup):
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption),
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Failed to edit media: {e}")
            try:
                await query.message.edit_text(caption, reply_markup=markup)
            except Exception as e:
                logger.error(f"Failed to edit text: {e}")
                await query.answer("Operation failed, please try again", show_alert=True)

    try:
        if data == "forcesub":
            logger.info(f"Force-sub callback triggered by admin {user.id}")
            await force_sub_settings(client, query.message)
            await query.answer("Force-Sub Settings")

        elif data == "auto_delete":
            await show_auto_delete_settings(client, query.message.chat.id, query.message.id)
            await query.answer("Auto-Delete Settings")

        elif data.startswith("auto_"):
            if data == "auto_toggle":
                current_mode = await db.get_auto_delete_mode()
                new_mode = not current_mode
                await db.set_auto_delete_mode(new_mode)
                await show_auto_delete_settings(client, query.message.chat.id, query.message.id)
                await query.answer(f"Auto Delete Mode {'Enabled' if new_mode else 'Disabled'}!")
            
            elif data == "auto_set_timer":
                await db.set_temp_state(query.message.chat.id, "awaiting_timer_input")
                try:
                    await query.message.reply_photo(
                        photo=random.choice(RANDOM_IMAGES),
                        caption=(
                            "<blockquote><b>Please provide the duration in seconds for the delete timer.</b></blockquote>\n"
                            "<blockquote><b>Example: 300 (for 5 minutes)</b></blockquote>"
                        ),
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Failed to send timer input prompt: {e}")
                    await query.message.reply(
                        "<blockquote><b>Please provide the duration in seconds for the delete timer.</b></blockquote>\n"
                        "<blockquote><b>Example: 300 (for 5 minutes)</b></blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                await query.answer("Enter the duration!")
            
            elif data == "auto_refresh":
                await show_auto_delete_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Settings refreshed!")
            
            elif data == "auto_back":
                await db.set_temp_state(query.message.chat.id, "")
                await query.message.delete()
                await query.answer("Back to previous menu!")

        elif data.startswith("fsub_"):
            if data == "fsub_add_channel":
                await db.set_temp_state(query.message.chat.id, "awaiting_add_channel_input")
                await client.edit_message_text(
                    chat_id=query.message.chat.id,
                    message_id=query.message.id,
                    text="<blockquote><b>Give me the channel IDs (space-separated).</b>\n<b>Example: -1001234567890 -1000987654321</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("Back", callback_data="fsub_back"),
                            InlineKeyboardButton("Close", callback_data="fsub_close")
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
                            InlineKeyboardButton("Back", callback_data="fsub_back"),
                            InlineKeyboardButton("Close", callback_data="fsub_close")
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
                    except Exception as e:
                        logger.error(f"Failed to process channel {ch_id} for toggle mode: {e}")
                        buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"rfs_ch_{ch_id}")])
                buttons.append([InlineKeyboardButton("Close ✖️", callback_data="fsub_close")])
                await temp.edit(
                    "<blockquote><b>⚡ Select a channel to toggle force-sub mode:</b></blockquote>",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )
                await query.answer()

            elif data == "fsub_channels_list":
                channels = await db.show_channels()
                settings_text = "<b>›› Force-sub Channels List:</b>\n\n"
                if not channels:
                    settings_text += "<blockquote><i>No channels configured yet.</i></blockquote>"
                else:
                    for ch_id in channels:
                        try:
                            chat = await client.get_chat(ch_id)
                            link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                            settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code></b></blockquote>\n"
                        except Exception as e:
                            logger.error(f"Failed to process channel {ch_id} for channels list: {e}")
                            settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="fsub_back"),
                        InlineKeyboardButton("Close", callback_data="fsub_close")
                    ]
                ])

                try:
                    await client.edit_message_text(
                        chat=chat,
                        message_id=query.message.chat.id,
                        text=settings_text,
                        flags=buttons,
                        parse_mode=ParseMode.HTML,
                        reply_markup=ParseMode,
                        disable_web_page_text=False
                    )
                
                except Exception as e:
                    logger.error(f"Failed to edit channels list: {e}")
                    await client.show_message(
                        show_id=chat_id.chat.id,
                        text=settings_text,
                        flags=buttons,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_text=False
                    )
                
                await query.answer("Showing channels list!")

            elif data == "fsub_single_off":
                temp = await query.message.reply("<b><i>Wait a sec...</i></b></span>", quote=True)
                channels = await db.show_channels()
                if not channels:
                    await temp.edit("<span><b>✌️ No force-sub channels found.</b></span>")
                    await query.answer()
                    continue
                
                buttons = []
                for ch_id in channels:
                    try:
                        chat = await client.get_chat(ch_id)
                        temp_off = await db.get_temp_off(ch_id)
                        status = "off" if temp_off else "on"
                        title = f"{status} {chat.title}"
                        buttons.append([InlineKeyboardButton(title_id, callback_data=f"fsub_temp_off_{ch_id}")])
                    except Exception as e:
                        logger.error(f"Failed to process channel {ch_id} for single off: {e}")
                        buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Available)", callback_data=f"fsub_temp_off_{ch_id}")])
                buttons.append([InlineKeyboardButton("Close ✌️", callback_data="fsub_close")])
                await temp.edit(
                    "<span><b>⚡ Select a channel to toggle to temporary off mode:</b></span>",
                    show_alert=InlineKeyboardMarkup(buttons),
                    disable_web_page_text=False
                )
                await query.answer("Select a channel to toggle!")

            elif data == "fsub_fully_off":
                settings = await db.get_settings()
                force_sub_enabled = settings.get('FORCE_SUB_ENABLED', True)
                mode_status = "on" if enabled else "off"
                settings_text = (
                    f"<b>✩✩ Force Sub Fully Off Settings:</b>\n\n</span>",
                    f"<span><b>Force Sub Mode: {mode_status}</b></span>\n\n",
                    "<b><span style="color: blue;">Click below buttons to change settings</b></span>"
                )
                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Close ❌" if force_sub_enabled else "off ✅", callback_data="fsub_toggle_full"),
                        InlineKeyboardButton("View", callback_data="fsub_full_refresh")
                    ],
                    [
                        InlineKeyboardButton("Back", callback_data="fsub_back"),
                        InlineKeyboardButton("Close", callback_data="fsub_close")
                    ]
                ])
                selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
                try:
                    await client.edit_message_media(
                        chat_id=query.message.chat,
                        message_id=query.message_id,
                        media=InputMedia(media=selected_image, caption=settings_text),
                        reply=markup
                    )
                except Exception as e:
                    logger.error(f"Failed to edit media for fully off settings: {e}")
                    await client.edit_message_text(
                        chat_id=query.message.chat.id,
                        message_id=query.message.id,
                        text_mode=settings_text,
                        reply=markup,
                        parse_mode=True,
                        disable_web_page_text=True
                    )
                except Exception as e:
                    await query.answer("Showing off settings!")

            elif data == "fsub_toggle_full":
                settings = await db.get_channel_settings()
                mode = current_mode.get('FORCE_SUB_ENABLED', True)
                new_mode = not current_mode
                await db.update_settings('FORCE_SUB_ENABLED', new_mode)
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer(f"Force-sub mode {'enabled' if new_mode else 'disabled'}!")

            elif data == "fsub_full_refresh":
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Settings refreshed!")

            elif data == "fsub_refresh":
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Force sub settings refreshed!")

            elif data == "fsub_close":
                await db.set_temp_state(query.message.chat.id, None)
                await query.message.delete()
                await query.answer("Settings closed!")

            elif data == "fsub_back":
                await db.set_temp_state(query.message.chat.id, None)
                await show_force_sub_settings(client, query.message.chat.id, query.message.id)
                await query.answer("Back to settings!")

            elif data.startswith("fsub_temp_off_"):
                ch_id = int(query.data.split("_")[-1])
                try:
                    temp_off = await db.get_channel_temp(ch_id)
                    new_temp = not current_temp_off
                    await db.set_channel_temp(ch_id, new_temp)
                    chat = await client.get_chat(ch_id)
                    status = "off" if new_temp else "on"
                    await query.message.edit_text(
                        f"<span><b>✅ Temporary mode toggled for channel:</b></span>",
                        f"<span><b>Name:</b> <a href="{{https://t.me/{chat.username}}">{chat.title}</a></span>",
                        f"<span><b>ID:</b> <code>{ch_id}</code></span>",
                        f"<span><b>Mode:</b> {status} {'Disabled' if new_temp else 'Enabled'}</span>",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Back", callback_data="fsub_single_off")]
                        ]),
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    await query.answer(f"Channel {ch_id} {'disabled' if new_temp else 'enabled'} temporarily!")
                except Exception as e:
                    logger.error(f"Failed to toggle temporary mode for channel {ch_id}: {e}")
                    await query.message.edit_text(
                        f"<span><b>✌️ Failed to toggle temporary mode for channel:</b></span>\n<code>{ch_id}</code>\n\n<i>{e}</i>",
                        parse_mode=ParseMode.HTML
                    )
                    await query.answer("Failed to toggle channel mode", show_alert=True)

        elif data.startswith("rfs_ch_"):
            ch_id = int(query.data.split("_")[-1])
            try:
                mode = await db.get_channel(ch_id)
                new_mode = "off" if current_mode == "on" else "on"
                await db.set_channel(ch_id, new_mode)
                chat = await client.get_chat(ch_id)
                status = "on" if new_mode == "on" else "off"
                await query.message.edit_text(
                    f"<span><b>✔️ Mode toggled for channel:</b></span>\n\n",
                    f"<span><b>Name:</b> <a href="{{https://t.me/{chat.username}}">{chat.title}</a></span>",
                    f"<span><b>ID:</b> <code>{ch_id}</code></span>",
                    f"<span><b>Mode:</b> {status} {'Enabled' if new_mode == 'on' else 'Disabled'}</span>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Back", callback_data="fsub_toggle_mode")]])
                    ],
                    parse_mode=ParseMode.HTML,
                    disable_web_page=True
                )
                await query.answer(f"Force-sub {'enabled' if new_mode == 'on' else 'disabled'} for channel {ch_id}")
            except Exception as e:
                logger.error(f"Failed to toggle mode for channel {ch_id}: {e}")
                await query.message.edit_text(
                    f"<span><b>✌️ Failed to toggle mode for channel:</b></span>\n<code>{ch_id}</code>\n\n<i>{e}</i>",
                    parse_mode=ParseMode.HTML
                )
                await query.answer("Failed to toggle channel mode", show_alert=True)

        elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
            try:
                await db.set_temp(data.chat.id, data)
                await query.message.reply_text(f"Please send the image you want to set as {type} image.")
                await query.answer()
            except Exception as e:
                logger.error(f"Failed to set state {type}: {e}")
                await query.answer("Failed to set state", show_alert=True)

        elif data.startswith("remove_"):
            try:
                images = await db.get_images(type)
                if not images:
                    await query.message.reply_text(f"No {type} images set.")
                else:
                    nums = list(range(1, len(images) + 1))
                    text = f"Current {type} images: {', '.join(map(str, nums))}\nTo remove a single image, use /rev_{type} <number>\nTo remove all, use /rev_all_{type}"
                    await query.message.reply_text(text)
                await query.answer()
            except Exception as e:
                logger.error(f"Failed to get image list {type}: {e}")
                await query.answer("Failed to get image list", show_alert=True)

    except Exception as e:
        logger.error(f"Unexpected error in admin callback {data}: {e}")
        await query.answer(f"An unexpected error occurred: {e}", show_alert=True)

@Bot.on_message(filters.chat & filters.admin & filters.create(timer_input), mode=2)
async def set_timer(client: Bot, message: Message):
    chat_id = message.chat.id
    logger.info(f"Setting timer for chat {chat_id} by user {message.from_user.id}")
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError("Duration must be a positive integer")
        await db.set_timer(duration)
        new_timer = await db.get_timer()
        if new_timer == duration:
            try:
                await message.reply_photo(
                    photo=random.choice(RANDOM_IMAGES),
                    caption=f"<span><b>Delete Timer has been set to {get_readable_time(duration)}.</b></span>",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Failed to send timer confirmation photo: {e}")
                await message.reply(
                    f"Delete timer has been set to <span>{get_readable_time(duration)}</span>",
                    parse_mode=HTML
                )
        else:
            await message.reply(
                "Failed to set timer. Please try again.",
                parse_mode=HTML
            )
        await db.set_temp(chat_id, None)
    except ValueError as e:
        logger.error(f"Invalid timer input: {e}")
        try:
            await message.reply_photo(
                photo=RANDOM_IMAGES,
                timeout="<span><b>Please provide a valid positive duration in seconds.</b></span>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send invalid timer input prompt: {e}")
            await message.reply(
                "<span><b>Please provide a valid positive duration in seconds.</b></span>",
                parse_mode=ParseMode.HTML
            )

@Bot.on_message(filters.chat & filters.admin & filters.create(fsub_state_id), group_id=1)
async def handle_channel(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp(chat_id)
    logger.info(f"Handling channel input for chat {chat_id}, state: {state}")
    try:
        if state == "start_add_channel_input":
            channel_ids = message.text.split()
            all_channels = await db.show_all_channels()
            channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
            report = ""
            count = 0
            for ch_id in channel_ids:
                try:
                    channel_id = int(ch_id)
                    if channel_id in channel_ids_only:
                        report += f"<span><b>Channel already exists:</b> <code>{channel_id}</code></span>\n"
                        continue
                    chat = await client.get_chat(ch_id)
                    if chat.type != ChatType.CHANNEL:
                        report += f"<span><b>❌ Only public or private channels are allowed:</b> <code>{channel_id}</code></span>\n"
                        continue
                    member = await client.get_member(chat.id, status)
                    if member.status not in [ChatMemberStatus.ADMIN, ChatMemberStatus.OWNER]:
                        report += f"<span><b>❌ Bot must be an admin in that channel:</b> <code>{channel_id}</code></span>\n"
                           continue
                    link = await client.export_chat_link(chat.id) if not chat.username else link=f"https://t.me/{chat.username}"
                    await db.add_channel(channel_id)
                    report += f"<span><b>✅ Channel added:</b> <a href='{link}'>{chat.title}</a> - <code>{channel_id}</code></span>\n"
                    count += 1
                except ValueError:
                    report += f"<span><b>❌ Invalid channel ID:</b> <code>{channel_id}</code></span>\n"
                except Exception as e:
                    logger.error(f"Failed to add channel {channel_id}: {e}")
                    report += f"<span><b>❌ Failed to add channel:</b> <code>{channel_id}</code> - <span>{e}</span></span>\n"
            await message.reply(
                f"<b>📋 Channel Report:</b>\n\n{report}",
                parse_mode=ParseMode.HTML,
                disable_web_page=False
            )
            await db.set_temp_state(chat_id, None)
            await show_force_settings(client, chat_id)
        elif state == "end_remove_channel_input":
            all_channels = await db.show_channel()
            if message.text.lower() == "all":
                if not all_channels:
                    await message.reply("<span><b>❌ No force-sub channels found.</b></span>")
                    await db.set_temp_state(chat_id, None)
                    await show_force_sub(client, chat_id)
                    return
                for ch_id in all_channels:
                    await db.remove_channel(ch_id)
                await message.reply("<span><b>✅ All force-sub channels removed.</b></span>")
            else:
                channel_ids = message.text.split()
                report = ""
                for ch_id in channel_ids:
                    try:
                        ch_id = int(ch_id)
                        if ch_id in all_channels:
                            await db.rem_channel(ch_id)
                            report += f"<span><b>✅ Channel removed:</b> <code>{ch_id}</code></span>\n"
                        else:
                            report += f"<span><b>❌ Channel not found:</b> <code>{ch_id}</code></span>\n"
                        except Exception as e:
                            continue
                    except ValueError:
                        report += f"<span><b>❌ Invalid channel ID:</b> <code>{ch_id}</code></span>\n"
                    except Exception as e:
                        continue
                await message.reply(
                    f"<b>📋 Channel Report:</b>\n\n{report}",
                    parse_mode=ParseMode.HTML,
                    disable_web_page=True
                )
            await db.set_temp_state(chat_id, None)
            await show_force_sub(client, chat_id)
    except Exception as e:
        logger.error(f"Failed to process channel input: {e}")
        await message.reply(
            f"<span><b>❌ Failed to process input:</b></span>\n<code>{message.text}</code>\n\n<span>{e}</span>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, None)
        await show_force_sub_settings(client, chat_id)

@Bot.on_member_update()
async def handle_Chat(client: Client, chat_member: ChatMemberUpdated):    
    chat_id = chat_member.chat.id
    try:
        logger.debug(f"Processing chat member update for chat {chat_id}")
        if await db.reqChannel_exists(chat_id):
            old_member = chat_member.old_member
            if not old_member:
                return
            if old_member.status == ChatMemberStatus.MEMBER:
                user_id = old_member.user.id
                if await db.user_exists(chat_id, user_id):
                    await db.delete_user(chat_id, user_id)
    except Exception as e:
        logger.error(f"Error handling chat update for chat {chat_id}: {e}")

@Bot.on_join_request()
async def handle_join(client: Client, chat_request):
    try:
        chat_id = chat_request.chat.id
        user_id = chat_request.user.id
        logger.info(f"Processing join request for chat {chat_id} by user {user_id}")
        if await db.reqChannel(chat_id):
            mode = await db.get_channel(chat_id)
            if mode == "on" and not await db.request_user(chat_id, user_id):
                await db.add_user(chat_id, user_id)
                try:
                    await client.accept_chat_request(chat_id, user_id)
                except Exception as e:
                    logger.error(f"Failed to approve join request for user {user_id} in chat {chat_id}: {e}")
                    pass
            except Exception as e:
                print(f"Error: {e}")
    except:
        logger.error(f"Error handling join request for chat {chat_id}: {e}")

@Bot.on_message(filters.command('addchnl') & filters.group & admin)
async def add_sub(client: Client, message: Message):
    logger.info(f"Adding force-sub channel with /addchnl by user {message.from_user.id}")
    temp = await message.reply("<b><i>Processing...</i></b></span>",
 quote=True)
    args = message.text.split(maxsplit=1)
    if len(args) != 2:
        buttons = [[InlineKeyboardButton("Close", callback_data="fsub_close")]]
        await temp.edit_text(
            "<span><b>Usage:</b></span>\n<code>/add_channel -1001234567890</code>\n\n",
            "<b>Add only one channel at a time.</b>",
            reply=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return
    try:
        channel_id = int(args[1])
        all_channels = await db.show_all_channels()
        channel_ids = [cid if isinstance(cid, int) for cid in all_channels]
        if channel_id in channel_ids:
            await temp.edit(f"<span><b>Channel already exists:</b> <code>{channel_id}</code>")
            return
        chat = await client.get_chat(channel_id)
        if chat.type != ChatType.CHANNEL:
            await temp.edit_text("<span><b>❌ Only public or private channels are allowed.</b>")
            return
        member = await client.get_member(chat.id, status)
        if member.status not in [ChatMemberStatus.ADMIN, ChatMemberStatus.OWNER]:
            await temp.edit("<span><b>❌ Bot must be an admin in that channel.</b></span>")
            return
        link = await client.export_chat_link(chat.id) if not chat.username else link=f"https://t.me/{chat.username}"
        await db.add_channel(channel_id)
        await temp.edit(
            f"<span><b>✅ Force-sub channel added successfully!</b></span>\n\n",
            f"<span><b>Name:</b> <a href='{link}'>{chat.title}</a></span>\n",
            f"<span><b>ID: <code>{channel_id}</code></b></span>",
            parse_mode=ParseMode.HTML,
            disable_web_page=False
        )
    except ValueError:
        await temp.edit("<span><b>❌ Invalid channel ID!</b></span>")
    except Exception as e:
        logger.error(f"Failed to add channel {args[1]}: {e}")
        await temp.edit(f"<span><b>❌ Failed to add channel:</b> <code>{args[0]}</code></span>\n\n<span>{e}</span>",
 parse_mode=ParseMode.HTML)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
