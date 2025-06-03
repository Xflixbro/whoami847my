import asyncio
import random
import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.types import InputMediaPhoto
from bot import Bot
from config import OWNER_ID, RANDOM_IMAGES, START_PIC, FSUB_LINK_EXPIRY
from database.database import db

logger = logging.getLogger(__name__)

MESSAGE_EFFECT_IDS = [5104841245755180586, 5107584321108051014, 5044134455711629726, 5046509860389126144, 5104859649142078462, 5046589136895476101]

async def show_channel_list(client: Client, chat_id: int, message_id: int = None):
    """Show the list of all force-sub channels."""
    settings_text = "<b>Force-Sub Channels List:</b>\n\n"
    channels = await db.show_channels()

    if not channels:
        settings_text += "<blockquote><i>No channels configured.</i></blockquote>"
    else:
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                member = await client.get_chat_member(ch_id, "me")
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Bot is not admin</i></b></blockquote>\n"
                    continue
                mode = await db.get_channel_mode(ch_id)
                status = "🟢 Enabled" if mode == "on" else "🔴 Disabled"
                link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(ch_id)
                settings_text += (
                    f"<blockquote><b><a href='{link}'>{chat.title}</a></b>\n"
                    f"- <b>ID:</b> <code>{ch_id}</code>\n"
                    f"- <b>Mode:</b> {status}</blockquote>\n"
                )
            except Exception as e:
                logger.error(f"Failed to fetch channel {ch_id}: {e}")
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Unavailable (Error: {e})</i></b></blockquote>\n"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Back to Menu", callback_data="fsub_back")]
    ])

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if message_id:
        try:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=buttons
            )
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

async def show_single_off_channels(client: Client, chat_id: int, message_id: int = None):
    """Show menu to toggle individual channel force-sub status."""
    channels = await db.show_channels()
    if not channels:
        await client.send_message(
            chat_id=chat_id,
            text="<b>No channels configured for force-sub.</b>",
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )
        return

    settings_text = "<b>Select a channel to toggle force-sub:</b>\n\n"
    buttons = []
    for ch_id in channels:
        try:
            chat = await client.get_chat(ch_id)
            mode = await db.get_channel_mode(ch_id)
            status = "🟢" if mode == "on" else "🔴"
            buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"single_off_{ch_id}")])
        except Exception as e:
            logger.error(f"Failed to fetch channel {ch_id}: {e}")
            buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Unavailable)", callback_data=f"single_off_{ch_id}")])

    buttons.append([InlineKeyboardButton("Back", callback_data="fsub_back")])

    if message_id:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
    else:
        await client.send_message(
            chat_id=chat_id,
            text=settings_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
            message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
        )

async def show_global_fsub_toggle(client: Client, chat_id: int, message_id: int = None):
    """Show global force-sub toggle settings."""
    fsub_enabled = await db.get_force_sub_enabled()
    mode_status = "Enabled ✅" if fsub_enabled else "Disabled ❌"

    settings_text = (
        "<b>Force Subscription Settings</b>\n\n"
        f"<blockquote><b>Force Sub Mode:</b> {mode_status}</blockquote>\n\n"
        "<b>Click below to change settings</b>"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Disable ❌" if fsub_enabled else "Enable ✅", callback_data="fsub_global_toggle")],
            [InlineKeyboardButton("Refresh", callback_data="fsub_global_refresh"), InlineKeyboardButton("Back", callback_data="fsub_back")]
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
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
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
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    """Show the force-sub settings menu with channel list and controls."""
    settings_text = "<b>›› Force Subscription Settings:</b>\n\n"
    fsub_enabled = await db.get_force_sub_enabled()
    channels = await db.show_channels()

    if not channels:
        settings_text += "<blockquote><i>No channels configured. Use 'Add Channels' to add a channel.</i></blockquote>"
    else:
        settings_text += "<blockquote><b>⚡ Force-sub Channels:</b></blockquote>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                member = await client.get_chat_member(ch_id, "me")
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Bot is not admin</i></b></blockquote>\n"
                    continue
                mode = await db.get_channel_mode(ch_id)
                status = "🟢 ON" if mode == "on" else "🔴 OFF"
                link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(ch_id)
                settings_text += (
                    f"<blockquote><b><a href='{link}'>{chat.title}</a></b>\n"
                    f"- ID: <code>{ch_id}</code>\n"
                    f"- Mode: {status}</blockquote>\n"
                )
            except Exception as e:
                logger.error(f"Failed to fetch channel {ch_id}: {e}")
                settings_text += f"<blockquote><b><code>{ch_id}</code> — <i>Invalid (Error: {e})</i></b></blockquote>\n"

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Add Channels", callback_data="fsub_add_channel"), InlineKeyboardButton("Remove Channels", callback_data="fsub_remove_channel")],
        [InlineKeyboardButton("Toggle Mode", callback_data="fsub_toggle_mode")],
        [InlineKeyboardButton("Channels List", callback_data="fsub_channels_list"), InlineKeyboardButton("Single Off", callback_data="fsub_single_off")],
        [InlineKeyboardButton("Fully Off", callback_data="fsub_global"), InlineKeyboardButton("Refresh", callback_data="fsub_refresh")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC

    if message_id:
        try:
            await client.edit_message_media(
                chat_id=chat_id,
                message_id=message_id,
                media=InputMediaPhoto(media=selected_image, caption=settings_text),
                reply_markup=buttons
            )
        except Exception as e:
            logger.error(f"Failed to edit message with image: {e}")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await client.send_photo(
                chat_id=chat_id,
                photo=selected_image,
                caption=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                message_effect_id=random.choice(MESSAGE_EFFECT_IDS)
            )

@Bot.on_message(filters.command('forcesub') & filters.private & filters.create(lambda _, __, m: m.from_user.id == OWNER_ID or db.admin_exist(m.from_user.id)))
async def force_sub_settings(client: Client, message: Message):
    """Handle /forcesub command to show settings."""
    await db.set_temp_state(message.chat.id, "")
    logger.info(f"Reset state for /forcesub in chat {message.chat.id}")
    await show_force_sub_settings(client, message.chat.id)

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    """Handle callback queries for force-sub settings."""
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    if data == "fsub_add_channel":
        await db.set_temp_state(chat_id, "awaiting_add_channel")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<b>Enter the channel ID.</b>\n\nAdd one channel at a time.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="fsub_back"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("Enter the channel ID")

    elif data == "fsub_remove_channel":
        await db.set_temp_state(chat_id, "awaiting_remove_channel")
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<b>Enter channel ID or type 'all' to remove all channels.</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="fsub_back"), InlineKeyboardButton("Close", callback_data="close")]
            ]),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("Enter channel ID or 'all'")

    elif data == "fsub_toggle_mode":
        channels = await db.show_channels()
        if not channels:
            await callback.message.reply_text("<b>No force-sub channels found.</b>")
            await callback.answer()
            return

        buttons = []
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                mode = await db.get_channel_mode(ch_id)
                status = "✅" if mode == "on" else "❌"
                buttons.append([InlineKeyboardButton(f"{status} {chat.title}", callback_data=f"rfs={ch_id}")])
            except Exception as e:
                logger.error(f"Failed to fetch channel {ch_id}: {e}")
                buttons.append([InlineKeyboardButton(f"⚠️ {ch_id} (Invalid)", callback_data=f"rfs={ch_id}")])

        buttons.append([InlineKeyboardButton("Back", callback_data="fsub_back")])

        await client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="<b>Select a channel to toggle force-sub mode:</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()

    elif data == "fsub_channels_list":
        await show_channel_list(client, chat_id, message_id)
        await callback.answer("Showing channels list")

    elif data == "fsub_single_off":
        await show_single_off_channels(client, chat_id, message_id)
        await callback.answer("Select channel to toggle")

    elif data == "fsub_global":
        await show_global_fsub_toggle(client, chat_id, message_id)
        await callback.answer("Showing global force-sub settings")

    elif data == "fsub_global_toggle":
        current_mode = await db.get_force_sub_enabled()
        new_mode = not current_mode
        await db.set_force_sub_enabled(new_mode)
        await show_global_fsub_toggle(client, chat_id, message_id)
        await callback.answer(f"Force-sub {'Enabled' if new_mode else 'Disabled'} globally")

    elif data == "fsub_global_refresh":
        await show_global_fsub_toggle(client, chat_id, message_id)
        await callback.answer("Settings refreshed")

    elif data == "fsub_refresh":
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Settings refreshed")

    elif data == "close":
        await db.set_temp_state(chat_id, "")
        await callback.message.delete()
        await callback.answer()

    elif data == "fsub_back":
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id, message_id)
        await callback.answer("Back to menu")

    elif data.startswith("single_off_"):
        ch_id = int(data.split("_")[2])
        try:
            current_mode = await db.get_channel_mode(ch_id)
            new_mode = "off" if current_mode == "on" else "on"
            await db.set_channel_mode(ch_id, new_mode)
            chat = await client.get_chat(ch_id)
            status = "✅" if new_mode == "on" else "❌"
            await callback.message.edit_text(
                f"<b>Force-sub toggled:</b>\n\n"
                f"<b>Channel:</b> <a href='https://t.me/{chat.username if chat.username else ch_id}'>{chat.title}</a>\n"
                f"<b>ID:</b> <code>{ch_id}</code>\n"
                f"<b>Status:</b> {status} {'Enabled' if new_mode == 'on' else 'Disabled'}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="fsub_single_off")]
                ]),
                parse_mode=ParseMode.HTML
            )
            await callback.answer(f"Channel {chat.title} {'enabled' if new_mode == 'on' else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to toggle channel {ch_id}: {e}")
            await callback.message.edit_text(
                f"<b>Error toggling channel {ch_id}:</b> {e}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Back", callback_data="fsub_single_off")]
                ])
            )
            await callback.answer("Error toggling channel")

@Bot.on_callback_query(filters.regex(r"^rfs="))
async def toggle_mode_callback(client: Client, callback: CallbackQuery):
    """Handle toggle mode for individual channels."""
    ch_id = int(callback.data.split("=")[1])
    try:
        current_mode = await db.get_channel_mode(ch_id)
        new_mode = "off" if current_mode == "on" else "on"
        await db.set_channel_mode(ch_id, new_mode)
        chat = await client.get_chat(ch_id)
        await callback.message.edit_text(
            f"<b>Force-sub mode toggled:</b>\n\n"
            f"<b>Channel:</b> <a href='https://t.me/{chat.username if chat.username else ch_id}'>{chat.title}</a>\n"
            f"<b>Mode:</b> {'🟢 ON' if new_mode == 'on' else '🔴 OFF'}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="fsub_toggle_mode")]
            ]),
            parse_mode=ParseMode.HTML
        )
        await callback.answer(f"Mode set to {'ON' if new_mode == 'on' else 'OFF'} for {chat.title}")
    except Exception as e:
        logger.error(f"Failed to toggle mode for channel {ch_id}: {e}")
        await callback.message.edit_text(
            f"<b>Error toggling mode for channel {ch_id}:</b> {e}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="fsub_toggle_mode")]
            ])
        )
        await callback.answer("Error toggling mode")

@Bot.on_message(filters.private & filters.create(lambda _, __, m: m.from_user.id == OWNER_ID or db.admin_exist(m.from_user.id)) & filters.text)
async def handle_text_input(client: Client, message: Message):
    """Handle text input for adding/removing channels."""
    state = await db.get_temp_state(message.chat.id)
    if state == "awaiting_add_channel":
        try:
            ch_id = int(message.text.strip())
            await client.get_chat(ch_id)
            member = await client.get_chat_member(ch_id, "me")
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await message.reply_text(
                    "<b>Bot must be an admin in the channel.</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="fsub_back")]])
                )
                return
            await db.add_channel(ch_id)
            await db.set_temp_state(message.chat.id, "")
            await message.reply_text(
                f"<b>Channel {ch_id} added to force-sub list.</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Settings", callback_data="fsub_back")]])
            )
        except ValueError:
            await message.reply_text("<b>Invalid channel ID. Please enter a valid number.</b>")
        except Exception as e:
            logger.error(f"Failed to add channel: {e}")
            await message.reply_text(f"<b>Error adding channel:</b> {e}")

    elif state == "awaiting_remove_channel":
        try:
            if message.text.lower() == "all":
                channels = await db.show_channels()
                for ch_id in channels:
                    await db.rem_channel(ch_id)
                await db.set_temp_state(message.chat.id, "")
                await message.reply_text(
                    "<b>All channels removed from force-sub list.</b>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Settings", callback_data="fsub_back")]])
                )
            else:
                ch_id = int(message.text.strip())
                if await db.channel_exist(ch_id):
                    await db.rem_channel(ch_id)
                    await db.set_temp_state(message.chat.id, "")
                    await message.reply_text(
                        f"<b>Channel {ch_id} removed from force-sub list.</b>",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Settings", callback_data="fsub_back")]])
                    )
                else:
                    await message.reply_text("<b>Channel not found in force-sub list.</b>")
        except ValueError:
            await message.reply_text("<b>Invalid input. Enter a valid channel ID or 'all'.</b>")
        except Exception as e:
            logger.error(f"Failed to remove channel: {e}")
            await message.reply_text(f"<b>Error removing channel:</b> {e}")
