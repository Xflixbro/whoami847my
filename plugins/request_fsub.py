import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Chat, ChatMemberStatus, ParseMode
from config import MESSAGE_EFFECT_IDS, OWNER_IDS, ADMINS_IDS
from database import Database
from helper_func import admin
import logging

# Logging setup
logging.basicConfig(
    filename="animelordbot.txt",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

Bot = Client("AnimeLordBot")
db = Database()

@Bot.on_message(filters.command("forcesub") & admin)
async def force_sub_command(client: Client, message):
    logger.info(f"Force-sub command received from {message.from_user.id}")
    await show_force_sub_settings(client, message.chat.id)

async def show_force_sub_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>›› Rᴇǫᴜᴇsᴛ Fꜱᴜʙ Sᴇᴛᴛɪɴɢs:</b>\n\n"
    try:
        channels = await db.show_channels()
    except Exception as e:
        logger.error(f"Failed to fetch channels: {e}")
        channels = []

    if not channels:
        settings_text += "<i>Nᴏ ᴄʜᴀɴɴᴇʟs ᴄᴏɴғɪɢᴜʀᴇᴅ ʏᴇᴛ. Uꜱᴇ 'ᴀᴅᴅ Cʜᴀɴɴᴇʟs' ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.</i>"
    else:
        settings_text += "<blockquote><b>⚡ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟs:</b></blockquote>\n\n"
        for ch_id in channels:
            try:
                chat = await client.get_chat(ch_id)
                link = await client.export_chat_invite_link(ch_id) if not chat.username else f"https://t.me/{chat.username}"
                settings_text += f"<blockquote><b>•</b> <a href='{link}'>{chat.title}</a> [<code>{ch_id}</code>]</blockquote>\n"
            except Exception as e:
                logger.error(f"Failed to fetch chat {ch_id}: {e}")
                settings_text += f"<blockquote><b>•</b> <code>{ch_id}</code> — <i>Uɴᴀᴠᴀɪʟᴀʙʟᴇ</i></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("•ᴀᴅᴅ Cʜᴀɴɴᴇʟs", callback_data="fsub_add_channel"),
                InlineKeyboardButton("ʀᴇᴍovᴇ Cʜᴀɴɴᴇʟs•", callback_data="fsub_remove_channel")
            ],
            [
                InlineKeyboardButton("Tᴏɢɢʟᴇ Mᴏᴅᴇ•", callback_data="fsub_toggle_mode"),
                InlineKeyboardButton("•ʀᴇꜰᴇʀsʜ•", callback_data="fsub_refresh")
            ],
            [
                InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
            ]
        ]
    )

    selected_effect = None
    try:
        if MESSAGE_EFFECT_IDS:
            selected_effect = random.choice(MESSAGE_EFFECT_IDS)
    except Exception as e:
        logger.error(f"Failed to select message effect: {e}")

    try:
        if message_id:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            logger.info("Edited force-sub settings message")
        else:
            await client.send_message(
                chat_id=chat_id,
                text=settings_text,
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                message_effect_id=selected_effect
            )
            logger.info(f"Sent force-sub settings message with effect {selected_effect}")
    except Exception as e:
        logger.error(f"Failed to send/edit settings message: {e}")
        await client.send_message(
            chat_id=chat_id,
            text=settings_text,
            reply_markup=buttons,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        logger.info("Sent force-sub settings message as fallback")

@Bot.on_callback_query(filters.regex(r"^fsub_"))
async def force_sub_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    if data == "fsub_add_channel":
        try:
            await db.set_temp_state(chat_id, "awaiting_add_channel_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID.</b></blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("•ʙᴀᴄᴋ•", callback_data="fsub_back"),
                        InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID.</b></blockquote>")
        except Exception as e:
            logger.error(f"Failed to process fsub_add_channel: {e}")
            await callback.answer("❌ Error setting up channel input. Try again.")

    elif data == "fsub_remove_channel":
        try:
            await db.set_temp_state(chat_id, "awaiting_remove_channel_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="<blockquote><b>Gɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴏʀ ᴛʏᴘᴇ 'all' ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ᴄʜᴀɴɴᴇʟs.</b></blockquote>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("•ʙᴀᴄᴋ•", callback_data="fsub_back"),
                        InlineKeyboardButton("•ᴄʟosᴇ•", callback_data="fsub_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("<blockquote><b>Pʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ID ᴏʀ ᴛʏᴘᴇ '[<code>all</code>]'.</b></blockquote>")
        except Exception as e:
            logger.error(f"Failed to process fsub_remove_channel: {e}")
            await callback.answer("❌ Error setting up channel removal. Try again.")

    elif data == "fsub_toggle_mode":
        try:
            channels = await db.show_channels()
            if not channels:
                await callback.answer("No channels configured!")
                return
            for ch_id in channels:
                await db.toggle_mode(ch_id)
            await show_force_sub_settings(client, chat_id, message_id)
            await callback.answer("Mode toggled successfully!")
        except Exception as e:
            logger.error(f"Failed to toggle mode: {e}")
            await callback.answer("❌ Error toggling mode. Try again.")

    elif data == "fsub_refresh":
        try:
            await show_force_sub_settings(client, chat_id, message_id)
            await callback.answer("Refreshed!")
        except Exception as e:
            logger.error(f"Failed to refresh settings: {e}")
            await callback.answer("❌ Error refreshing settings. Try again.")

    elif data == "fsub_back":
        try:
            await db.set_temp_state(chat_id, "")
            await show_force_sub_settings(client, chat_id, message_id)
            await callback.answer("Back to settings!")
        except Exception as e:
            logger.error(f"Failed to go back: {e}")
            await callback.answer("❌ Error going back. Try again.")

    elif data == "fsub_close":
        try:
            await callback.message.delete()
            await callback.answer("Settings closed!")
        except Exception as e:
            logger.error(f"Failed to close settings: {e}")
            await callback.answer("❌ Error closing settings. Try again.")

@Bot.on_message(filters.private & filters.regex(r"^-?\d+$|^all$") & admin)
async def handle_channel_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    
    logger.info(f"Received input: {message.text} from chat {chat_id}, current state: {state}")

    if not state:
        await message.reply("<blockquote><b>❌ No action is pending. Use /forcesub to start.</b></blockquote>")
        return

    try:
        if state == "awaiting_add_channel_input":
            channel_id = int(message.text)
            all_channels = await db.show_channels()
            channel_ids_only = [cid if isinstance(cid, int) else cid[0] for cid in all_channels]
            if channel_id in channel_ids_only:
                await message.reply(f"<blockquote><b>❌ Cʜᴀɴɴᴇʟ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs:</b></blockquote>\n <blockquote><code>{channel_id}</code></blockquote>")
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)
                return

            try:
                chat = await client.get_chat(channel_id)
                if chat.type != ChatType.CHANNEL:
                    await message.reply("<b>❌ Oɴʟʏ ᴘᴜʙʟɪᴄ ᴏʀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀʟʟᴏᴡᴇᴅ.</b>")
                    await db.set_temp_state(chat_id, "")
                    await show_force_sub_settings(client, chat_id)
                    return

                member = await client.get_chat_member(chat.id, "me")
                if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                    await message.reply("<b>❌ Bᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.</b>")
                    await db.set_temp_state(chat_id, "")
                    await show_force_sub_settings(client, chat_id)
                    return

                link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
                
                await db.add_channel(channel_id)
                await message.reply(
                    f"<blockquote><b>✅ Fᴏʀᴄᴇ-sᴜʙ Cʜᴀɴɴᴇʟ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b></blockquote>\n\n"
                    f"<blockquote><b>Nᴀᴍᴇ:</b> <a href='{link}'>{chat.title}</a></blockquote>\n"
                    f"<blockquote><b>Iᴅ:</b> <code>{channel_id}</code></blockquote>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)

            except Exception as e:
                logger.error(f"Failed to add channel {channel_id}: {e}")
                await message.reply(
                    f"<blockquote><b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ:</b></blockquote>\n<code>{channel_id}</code>\n\n<i>{str(e)}</i>",
                    parse_mode=ParseMode.HTML
                )
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)

        elif state == "awaiting_remove_channel_input":
            all_channels = await db.show_channels()
            if message.text.lower() == "all":
                if not all_channels:
                    await message.reply("<blockquote><b>❌ Nᴏ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ.</b></blockquote>")
                    await db.set_temp_state(chat_id, "")
                    await show_force_sub_settings(client, chat_id)
                    return
                for ch_id in all_channels:
                    await db.rem_channel(ch_id)
                await message.reply("<blockquote><b>✅ Aʟʟ ғᴏʀᴄᴇ-sᴜʙ ᴄʜᴀɴɴᴇʟs ʀᴇᴍᴏᴠᴇᴅ.</b></blockquote>")
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)
                return

            try:
                ch_id = int(message.text)
                if ch_id in all_channels:
                    await db.rem_channel(ch_id)
                    await message.reply(f"<blockquote><b>✅ Cʜᴀɴɴᴇʟ ʀᴇᴍᴏᴠᴇᴅ:</b></blockquote>\n <code>{ch_id}</code>")
                else:
                    await message.reply(f"<blockquote><b>❌ Cʜᴀɴɴᴇʟ ɴᴏᴛ ғᴏᴜɴᴅ:</b></blockquote>\n <code>{ch_id}</code>")
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)

            except ValueError:
                await message.reply("<blockquote><b>❌ Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ɪᴅ! Uꜱᴇ a valid ID or 'all'.</b></blockquote>")
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)
            except Exception as e:
                logger.error(f"Error removing channel {message.text}: {e}")
                await message.reply(f"<blockquote><b>❌ Eʀʀᴏʀ:</b></blockquote>\n <code>{str(e)}</code>")
                await db.set_temp_state(chat_id, "")
                await show_force_sub_settings(client, chat_id)

    except Exception as e:
        logger.error(f"Unexpected error in handle_channel_input for input {message.text}: {e}")
        await message.reply(
            f"<blockquote><b>❌ Uɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ:</b></blockquote>\n<code>{str(e)}</code>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")
        await show_force_sub_settings(client, chat_id)
