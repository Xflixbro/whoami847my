import asyncio
import logging
import random
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, FloodWait
from bot import Bot
from config import *
from database.database import db
from helper_func import is_subscribed, get_messages, encode, decode, get_message_id, get_exp_time, shorten_url

logger = logging.getLogger(__name__)

EMOJI_MODE = True
REACTIONS = ["👍", "😍", "🔥", "🎉", "❤️", "⚡"]
STICKER_ID = "CAACAgUAAxkBAAJFeWd0372UWP-vgb_dWo55DCPZS9zJzAAJpEgACqXaJVxBrhzahNnwSHgQ"
MESSAGE_EFFECT_IDS = [5104841245755180586, 5107584321108051014, 5044134455711629726, 5046509860389126144, 5104859649142078462, 5046589136895476101]
BAN_SUPPORT = f"{BAN_SUPPORT_URL}"
TUT_VID = f"{TUT_VID_URL}"

async def not_joined(client: Client, message: Message):
    temp = await message.reply("<blockquote><b>Checking subscription...</b></blockquote>")
    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        if not await db.get_force_sub_enabled():
            await temp.delete()
            return

        all_channels = await db.show_channels()
        if not all_channels:
            await temp.delete()
            return

        for ch_id in all_channels:
            try:
                mode = await db.get_channel_mode(ch_id)
                if mode == "off":
                    continue

                if not await is_subscribed(client, user_id, ch_id):
                    data = await client.get_chat(ch_id)
                    member = await client.get_chat_member(ch_id, "me")
                    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                        logger.warning(f"Bot is not admin in {ch_id}, skipping...")
                        continue

                    name = data.title
                    if mode == "on":
                        invite = await client.create_chat_invite_link(
                            chat_id=ch_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                        )
                        link = invite.invite_link
                    else:
                        link = f"https://t.me/{data.username}" if data.username else await client.export_chat_invite_link(ch_id)

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1
                    await temp.edit(f"<blockquote><b>Checking {count}...</b></blockquote>")
            except Exception as e:
                logger.error(f"Error with chat {ch_id}: {e}")
                continue

        if not buttons:
            await temp.delete()
            return

        try:
            buttons.append([InlineKeyboardButton("Try Again", url=f"https://t.me/{client.username}?start={message.command[1]}")])
        except IndexError:
            pass

        await message.reply_photo(
            photo=FORCE_PIC,
            caption=FORCE_TEXT.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name or "",
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Error in not_joined: {e}")
        await temp.edit_text(f"<b>Error: Contact @MehediRk\nReason: {e}</b>")
    finally:
        await temp.delete()

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    if EMOJI_MODE:
        await message.react(emoji=random.choice(REACTIONS))
    banned_users = await db.get_ban_users()
    if user_id in banned_users:
        return await message.reply_text(
            "You are banned from this bot.\n\nContact support if you think this is a mistake.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Support", url=BAN_SUPPORT)]])
        )
    if not await is_subscribed(client, user_id):
        return await not_joined(client, message)

    if not await db.present_user(user_id):
        try:
            await db.add_user(user_id)
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            string = await decode(base64_string)
            argument = string.split("-")
            ids = []
            if len(argument) == 3:
                start = int(argument[1]) // abs(client.db_channel.id)
                end = int(argument[2]) // abs(client.db_channel.id)
                ids = range(start, end + 1) if start <= end else range(start, end - 1, -1)
            elif len(argument) == 2:
                ids = [int(argument[1]) // abs(client.db_channel.id)]

            m = await message.reply_text("<b>Checking...</b>")
            await asyncio.sleep(0.4)
            await m.edit_text("<b>Getting your files...</b>")
            await asyncio.sleep(0.5)
            await m.delete()

            messages = await get_messages(client, ids)
            animelord_msgs = []
            settings = await db.get_settings()
            PROTECT_CONTENT = settings.get('PROTECT_CONTENT', False)

            for msg in messages:
                caption = (
                    CUSTOM_CAPTION.format(
                        previouscaption="" if not msg.caption else msg.caption.html,
                        filename=msg.document.file_name
                    ) if msg.document and CUSTOM_CAPTION else
                    ("" if not msg.caption else msg.caption.html)
                )
                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None
                try:
                    copied_msg = await msg.copy(
                        chat_id=user_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    animelord_msgs.append(copied_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    copied_msg = await msg.copy(
                        chat_id=user_id,
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        protect_content=PROTECT_CONTENT
                    )
                    animelord_msgs.append(copied_msg)
                except Exception as e:
                    logger.error(f"Failed to copy message: {e}")

            auto_delete_mode = await db.get_auto_delete_mode()
            FILE_AUTO_DELETE = await db.get_del_timer()
            if auto_delete_mode and FILE_AUTO_DELETE > 0:
                notification_msg = await message.reply(
                    f"This file will be deleted in {get_exp_time(FILE_AUTO_DELETE).lower()}. Please save or forward it.",
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
                await asyncio.sleep(FILE_AUTO_DELETE)
                for snt_msg in animelord_msgs:
                    try:
                        await snt_msg.delete()
                    except Exception as e:
                        logger.error(f"Error deleting message {snt_msg.id}: {e}")
                try:
                    reload_url = f"https://t.me/{client.username}?start={message.command[1]}" if message.command else None
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Get File Again", url=reload_url)]]) if reload_url else None
                    await notification_msg.edit_text(
                        "Your file/video is deleted!\n\nClick below to get it again.",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Error updating notification: {e}")
            return
        except Exception as e:
            logger.error(f"Error processing start payload: {e}")

    m = await message.reply("<b>Welcome to my bot.\nHope you're doing well...</b>")
    await asyncio.sleep(0.4)
    await m.edit("<b>Checking...</b>")
    await asyncio.sleep(0.5)
    await m.edit("🎉")
    await asyncio.sleep(0.5)
    await m.edit("⚡")
    await asyncio.sleep(0.5)
    await m.edit("<b>Starting...</b>")
    await asyncio.sleep(0.4)
    await m.delete()

    if STICKER_ID:
        m = await message.reply_sticker(STICKER_ID)
        await asyncio.sleep(1)
        await m.delete()

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("More Channels", url="https://t.me/Anime_Lord_List")],
        [InlineKeyboardButton("About", callback_data="about"), InlineKeyboardButton("Help", callback_data="help")]
    ])

    try:
        selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
        await message.reply_photo(
            photo=selected_image,
            caption=START_TEXT.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name or "",
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=reply_markup,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Error sending start photo: {e}")
        await message.reply(
            START_TEXT.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name or "",
                username=f"@{message.from_user.username}" if message.from_user.username else None,
                mention=message.from_user.mention,
                id=user_id
            ),
            reply_markup=reply_markup,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

@Bot.on_message(filters.command('commands') & filters.private & filters.create(lambda _, __, m: m.from_user.id == OWNER_ID or db.admin_exist(m.from_user.id)))
async def commands_list(client: Bot, message: Message):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
    await message.reply_text(text=CMD_TEXT, reply_markup=reply_markup, quote=True, message_effect_id=random.choice(MESSAGE_EFFECT_IDS))
