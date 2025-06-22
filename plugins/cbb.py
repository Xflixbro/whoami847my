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
from pyrogram.enums import ParseMode
from bot import Bot
from config import *
from database.database import db
from helper_func import get_readable_time
from datetime import datetime

@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|rfs_ch_|rfs_toggle_|fsub_back|set_|remove_|channels|start|info|seeplans|source|useless_|uselessmenu|auto_)"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user

    async def safe_edit_media(image, caption, markup):
        """Safe media editor with fallback to text"""
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(media=image, caption=caption),
                reply_markup=markup
            )
        except Exception as e:
            print(f"Media edit failed: {e}")
            try:
                await query.message.edit_text(caption, reply_markup=markup)
            except Exception as e:
                print(f"Text edit failed: {e}")
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
                    InlineKeyboardButton('• ᴜꜱᴇʟᴇꜱꜱ ꜰᴇᴀᴛᴜʀᴇꜱ •', callback_data='useless_menu')
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
                    InlineKeyboardButton("• ᴜꜱᴇʟᴇꜱꜱ ꜰᴇᴀᴛᴜʀᴇꜱ •", callback_data="useless_menu")
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
            except Exception as e:
                print(f"Premium callback error: {e}")
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
            except Exception as e:
                print(f"Close callback error: {e}")

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
                print(f"RFS channel error: {e}")
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
                print(f"RFS toggle error: {e}")
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
                print(f"Fsub back error: {e}")
                await query.answer("Failed to load channels", show_alert=True)

        elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
            type = data.split("_")[1]
            print(f"Set image callback triggered for type: {type}")
            try:
                await db.set_temp_state(query.message.chat.id, f"set_{type}")
                await query.message.reply_text(f"Please send the image you want to set as {type} image.")
            except Exception as e:
                print(f"Set image error: {e}")
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
                print(f"Remove image error: {e}")
                await query.answer("Failed to get image list", show_alert=True)

        # Useless Features Section
        elif data == "useless_menu":
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• User Stats •", callback_data="useless_users"),
                    InlineKeyboardButton("• Bot Stats •", callback_data="useless_stats")
                ],
                [
                    InlineKeyboardButton("• Auto Delete •", callback_data="useless_auto_delete"),
                    InlineKeyboardButton("• Close •", callback_data="close")
                ],
                [
                    InlineKeyboardButton("• Back •", callback_data="home")
                ]
            ])
            caption = (
                "» <b>Useless Features Menu</b>\n\n"
                "<blockquote>» <b>Here are some useless features you can play with</b></blockquote>\n\n"
                "<b>Select an option below:</b>"
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "useless_users":
            selected_image = random.choice(RANDOM_IMAGES)
            users = await db.full_userbase()
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Back •", callback_data="useless_menu"),
                    InlineKeyboardButton("• Close •", callback_data="close")
                ]
            ])
            caption = f"{len(users)} Uꜱᴇʀꜱ ᴀʀᴇ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ"
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "useless_stats":
            now = datetime.now()
            delta = now - client.uptime
            uptime = get_readable_time(delta.seconds)
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Back •", callback_data="useless_menu"),
                    InlineKeyboardButton("• Close •", callback_data="close")
                ]
            ])
            caption = BOT_STATS_TEXT.format(uptime=uptime)
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "useless_auto_delete":
            auto_delete_mode = await db.get_auto_delete_mode()
            delete_timer = await db.get_del_timer()
            
            mode_status = "Eɴᴀʙʟᴇᴅ ✅" if auto_delete_mode else "Dɪsᴀʙʟᴇᴅ ❌"
            timer_text = get_readable_time(delete_timer)

            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("• Dɪsᴀʙʟᴇᴅ ❌" if auto_delete_mode else "• Eɴᴀʙʟᴇᴅ ✅", callback_data="auto_toggle"),
                    InlineKeyboardButton(" Sᴇᴛ Tɪᴍᴇʀ •", callback_data="auto_set_timer")
                ],
                [
                    InlineKeyboardButton("• Rᴇғʀᴇꜱʜ", callback_data="useless_auto_delete"),
                    InlineKeyboardButton("• Back •", callback_data="useless_menu")
                ]
            ])
            caption = (
                "» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢꜱ</b>\n\n"
                f"<blockquote>» <b>Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ:</b> {mode_status}</blockquote>\n"
                f"<blockquote>» <b>Dᴇʟᴇᴛᴇ Tɪᴍᴇʀ:</b> {timer_text}</blockquote>\n\n"
                "<b>Cʟɪᴄᴋ Bᴇʟᴏᴡ Bᴜᴛᴛᴏɴꜱ Tᴏ Cʜᴀɴɢᴇ Sᴇᴛᴛɪɴɢꜱ</b>"
            )
            await safe_edit_media(selected_image, caption, reply_markup)

        elif data == "auto_toggle":
            current_mode = await db.get_auto_delete_mode()
            new_mode = not current_mode
            await db.set_auto_delete_mode(new_mode)
            await query.answer(f"Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Mᴏᴅᴇ {'Eɴᴀʙʟᴇᴅ' if new_mode else 'Dɪꜱᴀʙʟᴇᴅ'}!")
            # Refresh the auto delete settings
            await cb_handler(client, CallbackQuery(id=query.id, from_user=user, chat_instance=query.chat_instance, message=query.message, data="useless_auto_delete"))

        elif data == "auto_set_timer":
            await db.set_temp_state(query.message.chat.id, "awaiting_timer_input")
            await query.answer("Eɴᴛᴇʀ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ")
            await query.message.reply_text(
                "Pʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴅᴜʀᴀᴛɪᴏɴ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ꜰᴏʀ ᴛʜᴇ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ.\n"
                "Eхᴀᴄᴀᴍᴘʟᴇ: 300 (ꜰᴏʀ 5 ᴍɪɴᴜᴛᴇꜱ)"
            )

    except Exception as e:
        print(f"Unhandled error in callback handler: {e}")
        await query.answer("An unexpected error occurred", show_alert=True)
    
    await query.answer()

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
