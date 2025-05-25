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
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from helper_func import encode, to_small_caps_with_html, get_message_id
from database.database import db
from admin import check_admin

async def handle_db_post_input(client, message, selected_image):
    # Extract message IDs from user input
    try:
        msg_ids = [int(i.strip()) for i in message.text.strip().split() if i.strip().isdigit()]
        if not msg_ids:
            await message.reply_text("Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅs.", quote=True)
            return
    except ValueError:
        await message.reply_text("Iɴᴠᴀʟɪᴅ Iᴅ ғᴏʀᴍᴀᴛ. Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ɴᴜᴍʙᴇʀs ᴏɴʟʏ.", quote=True)
        return

    chat_id = CHANNEL_ID
    valid_ids = []
    
    # Check each message ID and skip missing ones
    for msg_id in msg_ids:
        try:
            msg = await client.get_messages(chat_id, msg_id)
            if msg and (msg.video or msg.document):
                valid_ids.append(msg_id)
            else:
                print(f"Skipping ID {msg_id}: No video or document found.")
        except Exception as e:
            print(f"Error checking ID {msg_id}: {e}")
            continue

    if not valid_ids:
        await message.reply_text("Nᴏ ᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇs ғᴏᴜɴᴅ ᴡɪᴛʜ ᴠɪᴅᴇᴏ ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛ.", quote=True)
        return

    # Create encoded links for valid IDs
    links = []
    for msg_id in valid_ids:
        base64_string = await encode(f"https://t.me/c/{str(chat_id)[4:]}/{msg_id}?thread={msg_id}")
        short_link = f"https://{SHORTLINK_URL}/en/{base64_string}"
        links.append(short_link)

    # Prepare output message with links
    caption = f"<b>Here are the links for the provided message IDs:</b>\n\n"
    for i, link in enumerate(links, 1):
        caption += f"{i}. {link}\n"
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Dᴏɴᴇ", callback_data="flink_done")]
    ])

    # Send output with random image and buttons
    await message.reply_photo(
        photo=selected_image,
        caption=caption,
        reply_markup=reply_markup,
        quote=True
    )

@Client.on_callback_query(filters.regex(r"^flink_done$"))
async def flink_done_output_callback(client: Client, query):
    # Handle "Done" button click
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
        await query.answer("Pʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ!")
    except Exception as e:
        print(f"Error in flink_done callback: {e}")
        await query.answer("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴄᴏᴍᴘʟᴇᴛɪɴɢ ᴛʜᴇ ᴘʀᴏᴄᴇss.")

@Client.on_message(filters.command("flink") & filters.private & check_admin)
async def flink_command(client: Client, message: filters.Message):
    # Handle /flink command
    selected_image = random.choice(RANDOM_IMAGES)
    await message.reply_photo(
        photo=selected_image,
        caption="Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ Iᴅs ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʀᴇᴀᴛᴇ ʟɪɴᴋs ғᴏʀ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
        ]),
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
    )
    try:
        response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ Iᴅs.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        await handle_db_post_input(client, response, selected_image)
    except asyncio.TimeoutError:
        await message.reply_text("Tɪᴍᴇᴏᴜᴛ! Nᴏ ʀᴇsᴘᴏɴsᴇ ʀᴇᴄᴇɪᴠᴇᴅ ᴡɪᴛʜɪɴ 5 ᴍɪɴᴜᴛᴇs.")
    except Exception as e:
        print(f"Error in flink_command: {e}")
        await message.reply_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_message(filters.command("batch") & filters.private & check_admin)
async def batch_command(client: Client, message: filters.Message):
    # Handle /batch command
    selected_image = random.choice(RANDOM_IMAGES)
    await message.reply_photo(
        photo=selected_image,
        caption="Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
        ]),
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
    )
    try:
        first_response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        first_msg_id = await get_message_id(client, first_response)
        if not first_msg_id:
            await first_response.reply_text("Iɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        await first_response.reply_photo(
            photo=selected_image,
            caption="Nᴏᴡ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
            ])
        )
        last_response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        last_msg_id = await get_message_id(client, last_response)
        if not last_msg_id:
            await last_response.reply_text("Iɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        if first_msg_id >= last_msg_id:
            await last_response.reply_text("Tʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ ᴍᴜsᴛ ʙᴇ ʟᴇss ᴛʜᴀɴ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.", quote=True)
            return

        base64_string = await encode(f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{first_msg_id}?thread={first_msg_id}")
        short_link = f"https://{SHORTLINK_URL}/en/{base64_string}"
        
        # Use normal font for link instead of Small Caps
        caption = f"<b>Here is the batch link for messages {first_msg_id} to {last_msg_id}:</b>\n\n{short_link}"
        
        await last_response.reply_photo(
            photo=selected_image,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Dᴏɴᴇ", callback_data="batch_done")]
            ]),
            quote=True
        )
    except asyncio.TimeoutError:
        await message.reply_text("Tɪᴍᴇᴏᴜᴛ! Nᴏ ʀᴇsᴘᴏɴsᴇ ʀᴇᴄᴇɪᴠᴇᴅ ᴡɪᴛʜɪɴ 5 ᴍɪɴᴜᴛᴇs.")
    except Exception as e:
        print(f"Error in batch_command: {e}")
        await message.reply_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʰʀʀᴇᴅ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_callback_query(filters.regex(r"^batch_done$"))
async def batch_done_output_callback(client: Client, query):
    # Handle "Done" button click for batch
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
        await query.answer("Bᴀᴛᴄʜ ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ!")
    except Exception as e:
        print(f"Error in batch_done callback: {e}")
        await query.answer("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴄᴏᴍᴘʟᴇᴛɪɴɢ ᴛʜᴇ ᴘʀᴏᴄᴇss.")

@Client.on_message(filters.command("genlink") & filters.private & check_admin)
async def genlink_command(client: Client, message: filters.Message):
    # Handle /genlink command
    selected_image = random.choice(RANDOM_IMAGES)
    await message.reply_photo(
        photo=selected_image,
        caption="Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ Iᴅ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ʟɪɴᴋ ғᴏʀ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
        ]),
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
    )
    try:
        response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ Iᴅ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        msg_id = await get_message_id(client, response)
        if not msg_id:
            await response.reply_text("Iɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        base64_string = await encode(f"https://t.me/c/{str(CHANNEL_ID)[4:]}/{msg_id}?thread={msg_id}")
        short_link = f"https://{SHORTLINK_URL}/en/{base64_string}"
        
        # Use normal font for link instead of Small Caps
        caption = f"<b>Here is the link for message {msg_id}:</b>\n\n{short_link}"
        
        await response.reply_photo(
            photo=selected_image,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Dᴏɴᴇ", callback_data="genlink_done")]
            ]),
            quote=True
        )
    except asyncio.TimeoutError:
        await message.reply_text("Tɪᴮᴍᴇᴏᴜᴛ! Nᴏ ʀᴇsᴘᴏɴsᴇ ʀᴇᴄᴇɪᴠᴇᴅ ᴡɪᴛʜɪɴ 5 ᴍɪɴᴜᴛᴇs.")
    except Exception as e:
        print(f"Error in genlink_command: {e}")
        await message.reply_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_callback_query(filters.regex(r"^genlink_done$"))
async def genlink_done_output_callback(client: Client, query):
    # Handle "Done" button click for genlink
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
        await query.answer("Gᴇɴʟɪɴᴋ ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ!")
    except Exception as e:
        print(f"Error in genlink_done callback: {e}")
        await query.answer("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴄᴏᴍᴘʟᴇᴛɪɴɢ ᴛʜᴇ ᴘʀᴏᴄᴇss.")

@Client.on_message(filters.command("custom_batch") & filters.private & check_admin)
async def custom_batch_command(client: Client, message: filters.Message):
    # Handle /custom_batch command
    selected_image = random.choice(RANDOM_IMAGES)
    await message.reply_photo(
        photo=selected_image,
        caption="Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ Iᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ (ᴇ.ɢ., @ChannelName ᴏʀ -100123456789).",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
        ]),
        message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
    )
    try:
        channel_response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ Iᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        chat_id = channel_response.text.strip()
        if not chat_id:
            await channel_response.reply_text("Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ Iᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        await channel_response.reply_photo(
            photo=selected_image,
            caption="Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
            ])
        )
        first_response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        first_msg_id = await get_message_id(client, first_response)
        if not first_msg_id:
            await first_response.reply_text("Iɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅ. Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        await first_response.reply_photo(
            photo=selected_image,
            caption="Nᴏᴡ sᴇɴᴅ ᴍᴇ ᴛʜᴇ ʟᴀsᴐᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cᴀɴᴄᴇʟ", callback_data="close")]
            ])
        )
        last_response = await client.ask(
            chat_id=message.chat.id,
            text="Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.",
            timeout=300,
            filters=filters.text & filters.user(message.from_user.id)
        )
        last_msg_id = await get_message_id(client, last_response)
        if not last_msg_id:
            await last_response.reply_text("Iɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ Iᴅ. Pʟᴇᴀsᴇ ᴛʰʀʏ ᴀɢᴀɪɴ.", quote=True)
            return

        if first_msg_id >= last_msg_id:
            await last_response.reply_text("Tʜᴇ ғɪʀsᴛ ᴍᴇssᴀɢᴇ Iᴅ ᴍᴜsᴛ ʙᴇ ʟᴇss ᴛʜᴀɴ ᴛʜᴇ ʟᴀsᴛ ᴍᴇssᴀɢᴇ Iᴅ.", quote=True)
            return

        base64_string = await encode(f"https://t.me/c/{str(chat_id)[4:]}/{first_msg_id}?thread={first_msg_id}")
        short_link = f"https://{SHORTLINK_URL}/en/{base64_string}"
        
        # Use normal font for link instead of Small Caps
        caption = f"<b>Here is the custom batch link for messages {first_msg_id} to {last_msg_id} in {chat_id}:</b>\n\n{short_link}"
        
        await last_response.reply_photo(
            photo=selected_image,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Dᴏɴᴇ", callback_data="custom_batch_done")]
            ]),
            quote=True
        )
    except asyncio.TimeoutError:
        await message.reply_text("Tɪᴍᴇᴏᴜᴛ! Nᴏ ʀᴇsᴘᴏɴsᴇ ʀᴇᴄᴇɪᴠᴇᴅ ᴡɪᴛʜɪɴ 5 ᴍɪɴᴜᴛᴇs.")
    except Exception as e:
        print(f"Error in custom_batch_command: {e}")
        await message.reply_text("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴘʀᴏᴄᴇssɪɴɢ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_callback_query(filters.regex(r"^custom_batch_done$"))
async def custom_batch_done_output_callback(client: Client, query):
    # Handle "Done" button click for custom_batch
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
        await query.answer("Cᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇᴅ!")
    except Exception as e:
        print(f"Error in custom_batch_done callback: {e}")
        await query.answer("Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴄᴏᴍᴘʟᴇᴛɪɴɢ ᴛʜᴇ ᴘʀᴏᴄᴇss.")

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
