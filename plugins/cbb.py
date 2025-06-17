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

@Bot.on_callback_query(filters.regex(r"^(help|about|home|premium|close|rfs_ch_|rfs_toggle_|fsub_back|set_|remove_)"))
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user

    if data == "help":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='home'),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data='close')]
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
            print(f"ᴇʀʀᴏʀ ɪɴ ʜᴇʟᴘ ᴄᴀʟʟʙᴀᴄᴋ: {e}")
            await query.message.edit_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘᴅᴀᴛɪɴɢ ᴛʜᴇ ʜᴇʟᴘ ᴍᴇssᴀɢᴇ.")
        await query.answer()

    elif data == "about":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='home'),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data='close')]
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
            print(f"ᴇʀʀᴏʀ ɪɴ ᴀʙᴏᴜᴛ ᴄᴀʟʟʙᴀᴄᴋ: {e}")
            await query.message.edit_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴜᴘᴅᴀᴛɪɴɢ ᴛʜᴇ ᴀʙᴏᴜᴛ ᴍᴇssᴀɢᴇ.")
        await query.answer()

    elif data == "home":
        try:
            selected_image = random.choice(RANDOM_IMAGES)
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴍᴏʀᴇ ᴄʜᴀɴɴᴇʟs", url="https://t.me/Anime_Lord_List")],
                [InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="about"), InlineKeyboardButton("ʜᴇʟᴘ", callback_data="help")]
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
            print(f"ᴇʀʀᴏʀ ɪɴ ʜᴏᴍᴇ ᴄᴀʟʟʙᴀᴄᴋ: {e}")
            await query.message.edit_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ʀᴇᴛᴜʜʀɴɪɴɢ ᴛᴏ ʜᴏᴍᴇ.")
        await query.answer()

    elif data == "premium":
    await query.message.delete()
    await client.send_photo(
        chat_id=query.message.chat.id,
        photo=QR_PIC,
        caption=(
            f"рҹ‘Ӣ {query.from_user.username if query.from_user.username else 'user'}\n\n"
            f"рҹҺ–пёҸ Aбҙ бҙҖЙӘКҹбҙҖКҷКҹбҙҮ бҙҳКҹбҙҖЙҙs:\n\n"
            f"в—Ҹ {PRICE1} Т“бҙҸКҖ 0 бҙ…бҙҖКҸs бҙҳКҖЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n"
            f"в—Ҹ {PRICE2} Т“бҙҸКҖ 1 бҙҚбҙҸЙҙбҙӣКң бҙҳКҖЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n"
            f"в—Ҹ {PRICE3} Т“бҙҸКҖ 3 бҙҚбҙҸЙҙбҙӣКңs бҙҳКҖЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n"
            f"в—Ҹ {PRICE4} Т“бҙҸКҖ 6 бҙҚбҙҸЙҙбҙӣКңs бҙҳКҖЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n"
            f"в—Ҹ {PRICE5} Т“бҙҸКҖ 1 КҸбҙҮбҙҖКҖ бҙҳКҖЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n\n"
            f"рҹ’ө AКҷsбҙӢ бҙңбҙҳЙӘ ЙӘбҙ… бҙӣбҙҸ бҙҖбҙ…бҙҚЙӘЙҙ бҙҖЙҙбҙ… бҙҳбҙҖКҸ бҙӣКңбҙҮКҖбҙҮ - <code>{UPI_ID}</code>\n\n\n"
            f"вҷ»пёҸ PбҙҖКҸбҙҚбҙҮЙҙбҙӣ КҸбҙҸбҙң бҙЎЙӘКҹКҹ ЙўбҙҮбҙӣ ЙӘЙҙsбҙӣбҙҖЙҙбҙӣ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ\n\n\n"
            f"вҖјпёҸ Mбҙңsбҙӣ sбҙҮЙҙбҙ… sбҙ„КҖбҙҮбҙҮЙҙsКңбҙҸбҙӣ бҙҖТ“бҙӣбҙҮКҖ бҙҳбҙҖКҸбҙҚбҙҮЙҙбҙӣ & ЙӘТ“ бҙҖЙҙКҸбҙҸЙҙбҙҮ бҙЎбҙҖЙҙбҙӣ бҙ„бҙңsбҙӣбҙҸбҙҚ бҙӣЙӘбҙҚбҙҮ бҙҚбҙҮбҙҚКҷбҙҮКҖsКңЙӘбҙҳ бҙӣКңбҙҮЙҙ бҙҖsбҙӢ бҙҖбҙ…бҙҚЙӘЙҙ"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Aбҙ…бҙҚЙӘЙҙ 24/7", url=(SCREENSHOT_URL)
                ],
                [InlineKeyboardButton("CКҹбҙҸsбҙҮ", callback_data="close")],
            ]
        )
    )
    await query.answer()
    elif data == "close":
        try:
            # Delete the callback message and the original command message if it exists
            await query.message.delete()
            if query.message.reply_to_message:
                await query.message.reply_to_message.delete()
        except Exception as e:
            print(f"ᴇʀʀᴏʀ ɪɴ ᴄʟᴏsᴇ ᴄᴀʟʲʟʙᴀᴄᴋ: {e}")
        await query.answer()

    elif data.startswith("rfs_ch_"):
        cid = int(data.split("_")[2])
        try:
            chat = await client.get_chat(cid)
            mode = await db.get_channel_mode(cid)
            status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
            new_mode = "off" if mode == "on" else "on"
            buttons = [
                [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'off' if mode == 'on' else 'on'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
                [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="fsub_back")]
            ]
            await query.message.edit_text(
                f"Cʜᴀɴɴᴇʟ: {chat.title}\nCᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ: {status}",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception:
            await query.answer("Fᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴄʜᴀɴɴᴇʟ ɪɴғᴏ", show_alert=True)

    elif data.startswith("rfs_toggle_"):
        cid, action = data.split("_")[2:]
        cid = int(cid)
        mode = "on" if action == "on" else "off"
        await db.set_channel_mode(cid, mode)
        await query.answer(f"Fᴏʀᴄᴇ-sᴜʙ sᴇᴛ ᴛᴏ {'on' if mode == 'on' else 'off'}")
        chat = await client.get_chat(cid)
        status = "🟢 ᴏɴ" if mode == "on" else "🔴 ᴏғғ"
        new_mode = "off" if mode == "on" else "on"
        buttons = [
            [InlineKeyboardButton(f"ʀᴇǫ ᴍᴏᴅᴇ {'off' if mode == 'on' else 'on'}", callback_data=f"rfs_toggle_{cid}_{new_mode}")],
            [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="fsub_back")]
        ]
        await query.message.edit_text(
            f"Cʜᴀɴɴᴇʟ: {chat.title}\nCᴜʀʀᴇɴᴛ ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ: {status}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "fsub_back":
        channels = await db.show_channels()
        buttons = []
        for cid in channels:
            try:
                chat = await client.get_chat(cid)
                mode = await db.get_channel_mode(cid)
                status = "🟢" if mode == "on" else "🔴"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs_ch_{cid}")])
            except:
                continue
        await query.message.edit_text(
            "Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴛᴏɢɢʟᴇ ɪᴛs ғᴏʀᴄᴇ-sᴜʙ ᴍᴏᴅᴇ:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await query.answer()

    elif data.startswith("set_") and data.split("_")[1] in ["start", "force"]:
        type = data.split("_")[1]
        print(f"Set image callback triggered for type: {type}")
        await db.set_temp_state(query.message.chat.id, f"set_{type}")
        await query.message.reply_text(f"Pʟᴇᴀsᴇ sᴇɴᴅ ᴍᴇ ᴛʜᴇ {type} ɪᴍᴀɢᴇ.")
        await query.answer()

    elif data.startswith("remove_"):
        type = data.split("_")[1]
        images = await db.get_images(type)
        if not images:
            await query.message.reply_text(f"Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ {type} ɪᴍᴀɢᴇs sᴇᴛ.")
        else:
            nums = list(range(1, len(images) + 1))
            text = f"Cᴜʀʀᴇɴᴛ {type} ɪᴍᴀɢᴇs: {', '.join(map(str, nums))}\nTᴏ ʀᴇᴍᴏᴠᴇ ᴀ sɪɴɢʟᴇ ɪᴍᴀɢᴇ, ᴜsᴇ /rev_{type} <number>\nTᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ, ᴜsᴇ /rev_all_{type}"
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
#
#
