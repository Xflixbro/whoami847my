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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from bot import Bot
from config import *
from database.database import db

logger = logging.getLogger(__name__)

# Try to import ADMINS, fallback to empty list if not found
try:
    from config import ADMINS
except ImportError:
    ADMINS = []
    logger.warning("ADMINS not found in config.py, defaulting to empty list")

# Define message effect IDs (used only for /fsettings initial message)
MESSAGE_EFFECT_IDS = [
    5104841245755180586,  # 🔥
    5107584321108051014,  # 👍
    5044134455711629726,  # ❤️
    5046509860389126442,  # 🎉
    5104858069142078462,  # 👎
    5046589136895476101,  # 💩
]

# States for conversation handler
SET_BUTTON_NAME = "SET_BUTTON_NAME"
SET_BUTTON_LINK = "SET_BUTTON_LINK"

async def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMINS

async def show_settings_message(client, message_or_callback, is_callback=False):
    settings = get_settings()
    # Create the settings text in the requested format
    settings_text = "<b>Fɪʟᴇs ʀᴇʟᴀᴛᴇᴅ sᴇᴛᴛɪɴɢs:</b>\n\n"
    settings_text += f"<blockquote><b>›› Pʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ: {'Eɴᴀʙʲʟᴇᴅ' if settings['PROTECT_CONTENT'] else 'Dɪsᴀʙʲʟᴇᴅ'} {'✅' if settings['PROTECT_CONTENT'] else '❌'}\n"
    settings_text += f"›› Hɪᴅᴇ ᴄᴀᴪᴛɪᴏɴ: {'Eɴᴀʙʲʟᴇᴅ' if settings['HIDE_CAPTION'] else 'Dɪsᴀʙʲʟᴇᴅ'} {'✅' if settings['HIDE_CAPTION'] else '❌'}\n"
    settings_text += f"›› Cʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ: {'Eɴᴀʙʲʟᴇᴅ' if not settings['DISABLE_CHANNEL_BUTTON'] else 'Dɪsᴀʙʲʟᴇᴅ'} {'✅' if not settings['DISABLE_CHANNEL_BUTTON'] else '❌'}\n"
    settings_text += f"›› Bᴜᴛᴛᴏɴ Nᴀᴍᴇ: {settings['BUTTON_NAME'] if settings['BUTTON_NAME'] else 'not set'}\n"
    settings_text += f"›› Bᴜᴛᴛᴏɴ Lɪɴᴋ: {settings['BUTTON_LINK'] if settings['BUTTON_LINK'] else 'not set'}</b></blockquote>\n\n"
    settings_text += "<b>Cʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ sᴇᴛᴛɪɴɢs</b>"

    # Create inline buttons for toggling settings
    buttons = [
        [
            InlineKeyboardButton("•ᴘᴄ", callback_data="toggle_protect_content"),
            InlineKeyboardButton("ʜᴄ•", callback_data="toggle_hide_caption"),
        ],
        [
            InlineKeyboardButton("•ᴄʙ", callback_data="toggle_channel_button"),
            InlineKeyboardButton("sʙ•", callback_data="set_button"),
        ],
        [
            InlineKeyboardButton("•ʀᴇꜰᴇʀsʜ•", callback_data="refresh_settings"),
            InlineKeyboardButton("•ʙᴀᴄᴋ•", callback_data="go_back"),
        ]
    ]

    # Select a random image
    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if is_callback:
        try:
            await message_or_callback.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            logger.debug(f"Edited settings message for user {message_or_callback.from_user.id}")
        except Exception as e:
            logger.error(f"Error editing message with photo: {e}")
            await message_or_callback.message.edit_text(
                text=settings_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    else:
        try:
            await message_or_callback.reply_photo(
                photo=selected_image,
                caption=settings_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
            logger.debug(f"Sent settings message to user {message_or_callback.from_user.id}")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await message_or_callback.reply_text(
                text=settings_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

async def safe_edit_media(message, image, caption, markup):
    """Safe media editor with fallback to text"""
    try:
        await message.edit_media(
            media=InputMediaPhoto(media=image, caption=caption),
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Media edit failed: {e}")
        try:
            await message.edit_text(caption, reply_markup=markup)
        except Exception as e:
            logger.error(f"Text edit failed: {e}")
            return False
    return True

@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|rfs_ch_|rfs_toggle_|fsub_back|set_|remove_|channels|start|info|seeplans|source|toggle_protect_content|toggle_hide_caption|toggle_channel_button|refresh_settings|go_back|set_button|cancel_button_input)"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user

    try:
        # File settings related callbacks
        if data == "toggle_protect_content":
            if not await is_admin(user.id):
                await query.answer("You need to be an admin to change this setting!", show_alert=True)
                return
            
            logger.info(f"Toggle protect content triggered by user {user.id}")
            await update_setting("PROTECT_CONTENT", not get_settings()["PROTECT_CONTENT"])
            await show_settings_message(client, query, is_callback=True)
            await query.answer("Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ ᴛᴏɢɢʟᴇᴅ!")

        elif data == "toggle_hide_caption":
            if not await is_admin(user.id):
                await query.answer("You need to be an admin to change this setting!", show_alert=True)
                return
            
            logger.info(f"Toggle hide caption triggered by user {user.id}")
            await update_setting("HIDE_CAPTION", not get_settings()["HIDE_CAPTION"])
            await show_settings_message(client, query, is_callback=True)
            await query.answer("Hɪᴅᴇ Cᴀᴪᴛɪᴏɴ ᴛᴏɢɢʟᴇᴅ!")

        elif data == "toggle_channel_button":
            if not await is_admin(user.id):
                await query.answer("You need to be an admin to change this setting!", show_alert=True)
                return
            
            logger.info(f"Toggle channel button triggered by user {user.id}")
            await update_setting("DISABLE_CHANNEL_BUTTON", not get_settings()["DISABLE_CHANNEL_BUTTON"])
            await show_settings_message(client, query, is_callback=True)
            await query.answer("Cʜᴀɴɴᴇʟ Bᴜᴛᴛᴏɴ ᴛᴏɢɢʟᴇᴅ!")

        elif data == "refresh_settings":
            logger.info(f"Refresh settings triggered by user {user.id}")
            await show_settings_message(client, query, is_callback=True)
            await query.answer("Sᴇᴛᴛɪɴɢs ʀᴇғʀᴇsʜᴇᴅ!")

        elif data == "go_back":
            logger.info(f"Go back triggered by user {user.id}")
            await query.message.delete()
            await query.answer("Bᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴍᴇɴᴜ!")

        elif data == "set_button":
            if not await is_admin(user.id):
                await query.answer("You need to be an admin to change button settings!", show_alert=True)
                return
            
            logger.info(f"Set Button callback triggered for user {user.id}")
            try:
                await db.set_temp_state(user.id, SET_BUTTON_NAME)
                await query.message.reply_text(
                    "বাটনের নাম দিন:",
                    quote=True,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• বাতিল •", callback_data="cancel_button_input")]
                    ])
                )
                logger.info(f"Sent 'Give me the button name' message to user {user.id}")
                await query.answer("দয়া করে বাটনের নাম দিন।")
            except FloodWait as e:
                logger.warning(f"FloodWait error for user {user.id}: Waiting for {e.x} seconds")
                await asyncio.sleep(e.x)
                await query.message.reply_text(
                    "বাটনের নাম দিন:",
                    quote=True,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("• বাতিল •", callback_data="cancel_button_input")]
                    ])
                await query.answer("দয়া করে বাটনের নাম দিন।")
            except Exception as e:
                logger.error(f"Error in set_button_start for user {user.id}: {e}")
                await query.message.reply_text(
                    "একটি ত্রুটি ঘটেছে। দয়া করে আবার চেষ্টা করুন বা /fsettings কমান্ড ব্যবহার করুন।",
                    quote=True
                )
                await query.answer("ত্রুটি ঘটেছে!", show_alert=True)
                await db.set_temp_state(user.id, "")

        elif data == "cancel_button_input":
            logger.info(f"Cancel button input triggered by user {user.id}")
            try:
                await db.set_temp_state(user.id, "")
                await query.message.reply_text("অ্যাকশন বাতিল করা হয়েছে!")
                await query.answer("বাতিল করা হয়েছে!")
            except Exception as e:
                logger.error(f"Error in cancel_button_input for user {user.id}: {e}")
                await query.message.reply_text(
                    "বাতিল করার সময় ত্রুটি ঘটেছে। দয়া করে আবার চেষ্টা করুন।",
                    quote=True
                )
                await query.answer("ত্রুটি ঘটেছে!", show_alert=True)

        # Original callbacks from cbb.py
        elif data == "help":
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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
                ]
            ])
            caption = START_MSG.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
            except Exception as e:
                logger.error(f"Premium callback error: {e}")
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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

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
            await safe_edit_media(query.message, selected_image, caption, reply_markup)

        elif data == "close":
            try:
                await query.message.delete()
                if query.message.reply_to_message:
                    await query.message.reply_to_message.delete()
            except Exception as e:
                logger.error(f"Close callback error: {e}")

        elif data.startswith("rfs_ch_"):
            try:
                cid = int(data.split("_")[2])
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "✅ On" if mode == "on" else "❌ Off"
                new_mode = "off" if mode == "on" else "on"
                buttons = [
                    [InlineKeyboardButton(f"Toggle {'off' if mode == 'on' else 'on'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                    [InlineKeyboardButton("Back", callback_data="fsub_back")]
                ]
                await query.message.edit_text(
                    f"Channel: {chat.title}\nCurrent Force-sub status: {status}",
                    reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as e:
                logger.error(f"RFS channel error: {e}")
                await query.answer("Failed to get channel info", show_alert=True)

        elif data.startswith("rfs_toggle_"):
            try:
                cid, action = data.split("_")[2:]
                cid = int(cid)
                mode = "on" if action == "on" else "off"
                await db.set_channel_mode(cid, mode)
                await query.answer(f"Force-sub set to {'on' if mode == 'on' else 'off'}")
                chat = await client.get_chat(cid)
                status = "✅ On" if mode == "on" else "❌ Off"
                new_mode = "off" if mode == "on" else "on"
                buttons = [
                    [InlineKeyboardButton(f"Toggle {'off' if mode == 'on' else 'on'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                    [InlineKeyboardButton("Back", callback_data="fsub_back")]
                ]
                await query.message.edit_text(
                    f"Channel: {chat.title}\nCurrent Force-sub status: {status}",
                    reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as e:
                logger.error(f"RFS toggle error: {e}")
                await query.answer("Failed to update settings", show_alert=True)

        elif data == "fsub_back":
            try:
                channels = await db.show_channels()
                buttons = []
                for cid in channels:
                    try:
                        chat = await client.get_chat(cid)
                        mode = await db.get_channel_mode(cid)
                        status = "✅" if mode == "on" else "❌"
                        buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
                    except Exception:
                        continue
                await query.message.edit_text(
                    "Select a channel to toggle force-sub status:",
                    reply_markup=InlineKeyboardMarkup(buttons))
            except Exception as e:
                logger.error(f"Fsub back error: {e}")
                await query.answer("Failed to load channels", show_alert=True)

        elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
            type = data.split("_")[1]
            logger.info(f"Set image callback triggered for type: {type}")
            try:
                await db.set_temp_state(query.message.chat.id, f"set_{type}")
                await query.message.reply_text(f"Please send the image you want to set as {type} image.")
            except Exception as e:
                logger.error(f"Set image error: {e}")
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
            except Exception as e:
                logger.error(f"Remove image error: {e}")
                await query.answer("Failed to get image list", show_alert=True)

    except Exception as e:
        logger.error(f"Unhandled error in callback handler: {e}")
        await query.answer("An unexpected error occurred", show_alert=True)
    
    await query.answer()

# Message handler for button input
async def button_input_filter(_, __, message):
    """Filter for messages based on user state."""
    user_id = message.from_user.id
    state = await db.get_temp_state(user_id)
    logger.info(f"Checking button_input_filter for user {user_id}: state={state}")
    return state in [SET_BUTTON_NAME, SET_BUTTON_LINK] and message.text

@Bot.on_message(filters.private & filters.create(button_input_filter))
async def handle_button_input(client, message):
    user_id = message.from_user.id
    state = await db.get_temp_state(user_id)
    
    if not await is_admin(user_id):
        await message.reply_text("You need to be an admin to change button settings!", quote=True)
        await db.set_temp_state(user_id, "")
        return
    
    logger.info(f"Handling button input for user {user_id} in state {state}")

    try:
        if state == SET_BUTTON_NAME:
            new_button_name = message.text.strip()
            logger.info(f"Received button name '{new_button_name}' from user {user_id}")
            await update_setting("BUTTON_NAME", new_button_name)
            logger.debug(f"Updated BUTTON_NAME to '{new_button_name}' for user {user_id}")

            await db.set_temp_state(user_id, SET_BUTTON_LINK)
            await message.reply_text(
                "বাটনের লিঙ্ক দিন:",
                quote=True,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("• বাতিল •", callback_data="cancel_button_input")]
                ])
            )
            logger.info(f"Sent 'Give me the button link' message to user {user_id}")

        elif state == SET_BUTTON_LINK:
            new_button_link = message.text.strip()
            logger.info(f"Received button link '{new_button_link}' from user {user_id}")
            await update_setting("BUTTON_LINK", new_button_link)
            logger.debug(f"Updated BUTTON_LINK to '{new_button_link}' for user {user_id}")

            await db.set_temp_state(user_id, "")
            await message.reply_text(
                "বাটন লিঙ্ক আপডেট করা হয়েছে! /fsettings কমান্ড ব্যবহার করে আপডেট দেখুন।",
                quote=True
            )
            logger.info(f"Sent confirmation message to user {user_id}")

    except Exception as e:
        logger.error(f"Error handling button input for user {user_id} in state {state}: {e}")
        await message.reply_text(
            "একটি ত্রুটি ঘটেছে। দয়া করে আবার চেষ্টা করুন বা /fsettings কমান্ড ব্যবহার করুন।",
            quote=True
        )
        await db.set_temp_state(user_id, "")
