import asyncio
import re
import logging
from typing import Optional
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ChatMemberUpdated
from pyrogram.enums import ParseMode, ChatAction, ChatType, ChatMemberStatus
from bot import Bot
from config import RANDOM_IMAGES, START_PIC, FSUB_LINK_EXPIRY, MESSAGE_EFFECT_IDS
from database.database import db
from helper_func import admin

# Set up logging
logger = logging.getLogger(__name__)

# Custom filter for channel ID input
async def channel_input_filter(_, _, message):
    chat_id: int = message.chat.id
    state: str = await db.get_temp_state(chat_id)
    if state == "awaiting_channel_input" and message.text:
        logger.info(f"Channel input received for chat {chat_id}: {message.text}")
        return True
    return False

# Custom filter for single channel toggle selection
async def single_toggle_filter(_, _, message):
    chat_id: int = message.chat.id
    state: str = await db.get_temp_state(chat_id)
    if state == "awaiting_single_toggle_input" and message.text:
        logger.info(f"Single toggle input received for chat {chat_id}: {message.text}")
        return True
    return False

# Show force subscription settings
async def show_force_subscription_settings(client: Client, chat_id: int, message_id: Optional[int] = None):
    force_sub_mode: bool = await db.get_force_sub_mode()
    channels: list = await db.show_channels()
    
    mode_status: str = "Enabled ✅" if force_sub_mode else "Disabled ❌" else ""
    settings_text: str = (
        f"» <b>Force Subscription Settings</b>\n\n"
        f"<blockquote>» <b>Force Sub Mode:</b> {mode_status}</blockquote>\n"
        f"<blockquote>» <b>Total Channels:</b> {len(channels)}</blockquote>\n\n"
        f"<b>Click Below Buttons To Change Settings</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• Add Channel •", callback_data="fsub_add"),
            InlineKeyboardButton("• Remove •", callback_data="fsub_remove")
        ],
        [
            InlineKeyboardButton("• Channels List", callback_data="fsub_list"),
            InlineKeyboardButton("• Single Off", callback_data="fsub_single_toggle")
        ],
        [
            InlineKeyboardButton("• Fully Off •", callback_data="fsub_fully_toggle"),
            InlineKeyboardButton("• Refresh", callback_data="fsub_refresh")
        ]
    ])

    selected_image: str = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        if message_id:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=keyboard
            )
        else:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    except Exception as e:
        logger.error(f"Failed to send/edit message with image: {e}")
        if message_id:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        else:
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

# Show fully off settings
async def show_fully_off_settings(client: Client, chat_id: int, message_id: int):
    force_sub_mode: bool = await db.get_force_sub_mode()
    mode_status: str = "Enabled ✅" if force_sub_mode else "Disabled ❌"
    
    settings_text: str = (
        f"» <b>Force Sub Fully Off Settings</b>\n\n"
        f"<blockquote>» <b>Force Sub Mode:</b> {mode_status}</blockquote>\n\n"
        f"<b>Click Below Buttons To Change Settings</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("• Disabled ❌" if force_sub_mode else "• Enabled ✅", callback_data="fsub_mode_toggle"),
            InlineKeyboardButton("• Refresh •", callback_data="fsub_fully_refresh")
        ],
        [
            InlineKeyboardButton("• Back 🔙", callback_data="fsub_back")
        ]
    ])

    selected_image: str = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        await client.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=InputMediaPhoto(media=selected_image, caption=settings_text),
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to edit message with image: {e}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=settings_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

# Show channels list
async def show_channels_list(client: Client, chat_id: int, message_id: int):
    channels: list = await db.show_channels()
    settings_text: str = "» <b>Force Sub Channels List</b>\n\n"
    
    if not channels:
        settings_text += "<blockquote><i>No channels configured yet.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode: str = await db.get_channel_mode(ch_id)
                link: str = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(ch_id)
                mode_status: str = "Enabled ✅" if mode == "on" else "Disabled ❌"
                settings_text += f"<blockquote><b><a href='{link}'>{chat.title}</a> - <code>{ch_id}</code> ({mode_status})</b></blockquote>\n"
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("• Back 🔙", callback_data="fsub_back")]
    ])

    selected_image: str = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    try:
        await client.edit_message_media(
            chat_id=chat_id,
            message_id=message_id,
            media=InputMediaPhoto(media=selected_image, caption=settings_text),
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to edit message with image: {e}")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=settings_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

@Bot.on_message(filters.command('forcesub') & filters.private & admin)
async def force_sub_settings(client: Client, message: Message):
    await db.set_temp_state(message.chat.id, "")
    logger.info(f"Reset state for chat {message.chat.id} before showing force-sub settings")
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    data: str = callback.data
    chat_id: int = callback.message.chat.id
    message_id: int = callback.message.id
    selected_image: str = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if data == "fsub_add":
        await db.set_temp_state(chat_id, "awaiting_channel_input")
        await db.set_temp_data(chat_id, "action", "add")
        logger.info(f"Set state to 'awaiting_channel_input' and action to 'add' for chat {chat_id}")
        try:
            await callback.message.reply_photo(
                photo=selected_image,
                caption=(
                    "<blockquote><b>Please provide the channel ID or username.</b></blockquote>\n"
                    "<blockquote><b>Example: -1001234567890 or @ChannelUsername</b></blockquote>"
                ),
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.message.reply(
                "<blockquote><b>Please provide the channel ID or username.</b></blockquote>\n"
                "<blockquote><b>Example: -1001234567890 or @ChannelUsername</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        await callback.answer("Enter the channel ID or username!")

    elif data == "fsub_remove":
        await db.set_temp_state(chat_id, "awaiting_channel_input")
        await db.set_temp_data(chat_id, "action", "remove")
        logger.info(f"Set state to 'awaiting_channel_input' and action to 'remove' for chat {chat_id}")
        try:
            await callback.message.reply_photo(
                photo=selected_image,
                caption=(
                    "<blockquote><b>Please provide the channel ID or username to remove.</b></blockquote>\n"
                    "<blockquote><b>Example: -1001234567890 or @ChannelUsername</b></blockquote>"
                ),
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.message.reply(
                "<blockquote><b>Please provide the channel ID or username to remove.</b></blockquote>\n"
                "<blockquote><b>Example: -1001234567890 or @ChannelUsername</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        await callback.answer("Enter the channel ID or username to remove!")

    elif data == "fsub_list":
        await show_channels_list(client, chat_id, message_id)
        await callback.answer("Channels List Displayed!")

    elif data == "fsub_single_toggle":
        await db.set_temp_state(chat_id, "awaiting_single_toggle_input")
        logger.info(f"Set state to 'awaiting_single_toggle_input' for chat {chat_id}")
        channels: list = await db.show_channels()
        settings_text: str = "<blockquote><b>Please provide the channel ID to toggle.</b></blockquote>\n"
        if channels:
            settings_text += "<blockquote><b>Available Channels:</b></blockquote>\n"
            for ch_id in channels:
                try:
                    chat = await client.get_chat(ch_id)
                    mode: str = await db.get_channel_mode(ch_id)
                    mode_status: str = "Enabled ✅" if mode == "on" else "Disabled ❌"
                    settings_text += f"<blockquote><b>{chat.title} - <code>{ch_id}</code> ({mode_status})</b></blockquote>\n"
                except Exception as e:
                    logger.error(f"Failed to fetch chat {ch_id}: {e}")
                    settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable</i></b></blockquote>\n"
        try:
            await callback.message.reply_photo(
                photo=selected_image,
                caption=settings_text,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await callback.message.reply(
                settings_text,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        await callback.answer("Enter the channel ID to toggle!")

    elif data == "fsub_fully_toggle":
        await show_fully_off_settings(client, chat_id, message_id)
        await callback.answer("Fully Off Settings Displayed!")

    elif data == "fsub_mode_toggle":
        current_mode: bool = await db.get_force_sub_mode()
        new_mode: bool = not current_mode
        await db.set_force_sub_mode(new_mode)
        await show_fully_off_settings(client, chat_id, message_id)
        await callback.answer(f"Force Sub Mode {'Enabled' if new_mode else 'Disabled'}!")

    elif data == "fsub_fully_refresh":
        await show_fully_off_settings(client, chat_id, message_id)
        await callback.answer("Settings Refreshed!")

    elif data == "fsub_refresh":
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Settings Refreshed!")

    elif data == "fsub_back":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Back to previous menu!")

@Bot.on_message(filters.private & admin & filters.create(channel_input_filter))
async def handle_channel_input(client: Client, message: Message):
    chat_id: int = message.chat.id
    input_text: str = message.text.strip()
    action: str = await db.get_temp_data(chat_id, "action")
    logger.info(f"Handling channel input for chat {chat_id}: {input_text}, action: {action}")

    # Extract channel ID from input
    try:
        if input_text.startswith("@"):
            chat = await client.get_chat(input_text)
            channel_id: int = chat.id
        elif input_text.startswith("-100"):
            channel_id: int = int(input_text)
        else:
            await message.reply(
                "<blockquote><b>Invalid channel ID or username. Please provide a valid ID or username.</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
            return
    except Exception as e:
        logger.error(f"Failed to resolve channel {input_text}: {e}")
        await message.reply(
            "<blockquote><b>Failed to find the channel. Ensure the bot is an admin in the channel.</b></blockquote>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        return

    if action == "add":
        try:
            chat = await client.get_chat(channel_id)
            if chat.type != ChatType.CHANNEL:
                await message.reply(
                    "<blockquote><b>Please provide a valid channel ID or username.</b></blockquote>",
                    parse_mode=ParseMode.HTML,
                    message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
                )
                return
            await db.add_channel(channel_id)
            await message.reply(
                f"<blockquote><b>Channel {chat.title} (<code>{channel_id}</code>) added successfully!</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to add channel {channel_id}: {e}")
            await message.reply(
                f"<blockquote><b>Failed to add channel: {str(e)}</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
    elif action == "remove":
        if not await db.channel_exist(channel_id):
            await message.reply(
                "<blockquote><b>Channel not found in the force-sub list.</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
            return
        try:
            chat = await client.get_chat(channel_id)
            await db.rem_channel(channel_id)
            await message.reply(
                f"<blockquote><b>Channel {chat.title} (<code>{channel_id}</code>) removed successfully!</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to remove channel {channel_id}: {e}")
            await message.reply(
                f"<blockquote><b>Failed to remove channel: {str(e)}</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

    await db.set_temp_state(chat_id, "")
    await db.set_temp_data(chat_id, "action", None)
    await show_force_sub_settings(client, chat_id)

@Bot.on_message(filters.private & admin & filters.create(single_toggle_filter))
async def handle_single_toggle_input(client: Client, message: Message):
    chat_id: int = message.chat.id
    input_text: str = message.text.strip()
    logger.info(f"Handling single toggle input for chat {chat_id}: {input_text}")

    # Extract channel ID from input
    try:
        if input_text.startswith("@"):
            chat = await client.get_chat(input_text)
            channel_id: int = chat.id
        elif input_text.startswith("-100"):
            channel_id: int = int(input_text)
        else:
            await message.reply(
                "<blockquote><b>Invalid channel ID or username. Please provide a valid ID or username.</b></blockquote>",
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
            return
    except Exception as e:
        logger.error(f"Failed to resolve channel {input_text}: {e}")
        await message.reply(
            "<blockquote><b>Failed to find the channel. Ensure the bot is an admin in the channel.</b></blockquote>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        return

    if not await db.channel_exist(channel_id):
        await message.reply(
            "<blockquote><b>Channel not found in the force-sub list.</b></blockquote>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        return

    try:
        current_mode: str = await db.get_channel_mode(channel_id)
        new_mode: str = "off" if current_mode == "on" else "on"
        await db.set_channel_mode(channel_id, new_mode)
        chat = await client.get_chat(channel_id)
        await message.reply(
            f"<blockquote><b>Channel {chat.title} (<code>{channel_id}</code>) force-sub mode set to {'Enabled ✅' if new_mode == 'on' else 'Disabled ❌'}!</b></blockquote>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
    except Exception as e:
        logger.error(f"Failed to toggle channel {channel_id}: {e}")
        await message.reply(
            f"<blockquote><b>Failed to toggle channel mode: {str(e)}</b></blockquote>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

    await db.set_temp_state(chat_id, "")
    await show_force_sub_settings(client, chat_id)

@Bot.on_chat_member_updated(filters.group | filters.channel)
async def member_has_joined(client: Client, member: ChatMemberUpdated):
    if (
        not member.new_chat_member
        or member.new_chat_member.status not in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR}
        or member.old_chat_member
    ):
        return
    user_id: int = member.from_user.id
    chat_id: int = member.chat.id
    if await db.reqChannel_exist(chat_id):
        await db.del_req_user(chat_id, user_id)
        logger.info(f"Removed user {user_id} from request list for channel {chat_id}")
