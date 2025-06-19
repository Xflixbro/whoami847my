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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from bot import Bot
from config import *
from database.database import db


@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|rfs_ch_|rfs_toggle_|fsub_back|set_|remove_|channels|start|info|seeplans|source)"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user

    if data == "help":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('Official Channel', url='https://t.me/Anime_Lord_List'),
                    InlineKeyboardButton('Support Group', url='https://t.me/AnimeLord_Support')
                ],
                [
                    InlineKeyboardButton('Home', callback_data='home'),
                    InlineKeyboardButton("Close", callback_data='close')
                ]
            ])
            caption = HELP_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in help callback: {e}")
            await query.message.edit_text("An error occurred while processing your help request.")
        await query.answer()

    elif data == "about":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('Our Channels', callback_data='channels'),
                    InlineKeyboardButton("Bot Info", callback_data='info')
                ],
                [
                    InlineKeyboardButton('Source Code', callback_data='source'),
                    InlineKeyboardButton("Go Back", callback_data='home')
                ]
            ])
            caption = ABOUT_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in about callback: {e}")
            await query.message.edit_text("An error occurred while processing your about request.")
        await query.answer()

    elif data == "info":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('Official Channel', url='https://t.me/Anime_Lord_List'),
                    InlineKeyboardButton('Support Group', url='https://t.me/AnimeLord_Support')
                ],
                [
                    InlineKeyboardButton('Close', callback_data='close')
                ]
            ])
            caption = CREDIT_INFO.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in info callback: {e}")
            await query.message.edit_text("An error occurred while showing bot information.")
        await query.answer()

    elif data == "channels":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('Anime Channel 1', url='https://t.me/Anime_Lord_List'),
                    InlineKeyboardButton('Anime Channel 2', url='https://t.me/AnimeLord_Updates')
                ],
                [
                    InlineKeyboardButton('Movie Channel', url='https://t.me/AnimeLord_Movies'),
                    InlineKeyboardButton('Series Channel', url='https://t.me/AnimeLord_Series')
                ],
                [
                    InlineKeyboardButton('🏠 Start', callback_data='home'),
                    InlineKeyboardButton('❌ Close', callback_data='close')
                ]
            ])
            caption = ABOUT_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in channels callback: {e}")
            await query.message.edit_text("An error occurred while loading our channel list.")
        await query.answer()

    elif data == "home":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Help", callback_data="help"),
                    InlineKeyboardButton("About", callback_data="about")
                ],
                [
                    InlineKeyboardButton("Our Channel", url="https://t.me/Anime_Lord_List"),
                    InlineKeyboardButton("Premium Plans", callback_data="seeplans")
                ]
            ])
            caption = START_MSG.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in home callback: {e}")
            await query.message.edit_text("An error occurred while processing your home request.")
        await query.answer()

    elif data == "premium":
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
        await query.answer()

    elif data == "seeplans":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('Buy Now', url='https://t.me/Anime_Lord_List'),
                    InlineKeyboardButton('Close', callback_data='close')
                ]
            ])
            caption = PREPLANSS_TXT.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in seeplans callback: {e}")
            await query.message.edit_text("An error occurred while showing premium plans.")
        await query.answer()

    elif data == "source":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('GitHub Repository', url='https://github.com/AnimeLord-Bots/FileStore'),
                    InlineKeyboardButton('🏠 Start', callback_data='start')
                ]
            ])
            caption = CREDIT_INFO.format(
                first=user.first_name,
                last=user.last_name if user.last_name else "",
                username=None if not user.username else '@' + user.username,
                mention=user.mention,
                id=user.id
            )
            await query.message.edit_media(
                media=InputMediaPhoto(media=selected_image, caption=caption),
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error in source callback: {e}")
            await query.message.edit_text("An error occurred while showing source information.")
        await query.answer()

    elif data == "close":
        try:
            await query.message.delete()
            if query.message.reply_to_message:
                await query.message.reply_to_message.delete()
        except Exception as e:
            print(f"Error in close callback: {e}")
        await query.answer()

    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
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
        except Exception:
            await query.answer("Failed to get channel info", show_alert=True)

    elif data.startswith("rfs_toggle_"):
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

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "✅" if mode == "on" else "❌"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
            except:
                continue
        await query.message.edit_text(
            "Select a channel to toggle force-sub status:",
            reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()

    elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
        type = data.split("_")[1]
        print(f"Set image callback triggered for type: {type}")
        await db.set_temp_state(query.message.chat.id, f"set_{type}")
        await query.message.reply_text(f"Please send the image you want to set as {type} image.")
        await query.answer()

    elif data.startswith("remove_"):
        type = data.split("_")[1]
        images = await db.get_images(type)
        if not images:
            await query.message.reply_text(f"There are no {type} images set.")
        else:
            nums = list(range(1, len(images) + 1))
            text = f"Current {type} images: {', '.join(map(str, nums))}\nTo remove a single image, use /rev_{type} <number>\nTo remove all, use /rev_all_{type}"
            await query.message.reply_text(text)
        await query.answer()

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
