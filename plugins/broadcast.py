from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from bot import Bot
from config import ADMINS, OWNER_ID, RANDOM_IMAGES, START_PIC, MESSAGE_EFFECT_IDS
from helper_func import admin
from database.database import db
import random
import logging
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom filter for broadcast states
async def broadcast_state_filter(_, __, message):
    if not message.chat.type == "private":
        return False
    state = await db.get_temp_state(message.chat.id)
    return state in ["awaiting_broadcast_input", "awaiting_pbroadcast_input", "awaiting_dbroadcast_message", "awaiting_dbroadcast_duration"]

# Custom filter to exclude link generator states
async def exclude_link_generator_states(_, __, message):
    state = await db.get_temp_state(message.chat.id)
    # Exclude messages if user is in link generator states
    return state not in ["awaiting_first_message", "awaiting_second_message", "awaiting_format", "awaiting_db_post", "awaiting_caption"]

# Show broadcast settings with buttons and message effects
async def show_broadcast_settings(client: Client, chat_id: int, message_id: int = None):
    settings_text = "<b>Broadcast Settings:</b>\n\n"
    settings_text += "<blockquote><b>Available Broadcast Options:</b></blockquote>\n\n"
    settings_text += "<blockquote><b>1. Broadcast - Send a message to all users.</b></blockquote>\n"
    settings_text += "<blockquote><b>2. Pin - Send and pin a message to all users.</b></blockquote>\n"
    settings_text += "<blockquote><b>3. Delete - Send a message with auto-delete after a specified time.</b></blockquote>\n"

    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Broadcast", callback_data="cast_broadcast"),
                InlineKeyboardButton("Pin", callback_data="cast_pbroadcast")
            ],
            [
                InlineKeyboardButton("Delete", callback_data="cast_dbroadcast")
            ],
            [
                InlineKeyboardButton("Refresh", callback_data="cast_refresh"),
                InlineKeyboardButton("Close", callback_data="cast_close")
            ]
        ]
    )

    selected_image = random.choice(RANDOM_IMAGES) if RANDOM_IMAGES else START_PIC
    selected_effect = random.choice(MESSAGE_EFFECT_IDS) if MESSAGE_EFFECT_IDS else None

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
        else:
            try:
                await client.send_photo(
                    chat_id=chat_id,
                    photo=selected_image,
                    caption=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    message_effect_id=selected_effect
                )
            except PeerIdInvalid:
                await client.send_message(
                    chat_id=chat_id,
                    text=settings_text,
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    message_effect_id=selected_effect
                )
    except Exception as e:
        logger.error(f"Failed to show broadcast settings: {e}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>Error: Failed to show broadcast settings. Please try again.</b>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

# Command to show broadcast settings
@Bot.on_message(filters.command('cast') & filters.private & admin)
async def cast_settings(client: Client, message: Message):
    await show_broadcast_settings(client, message.chat.id)

# Callback handler for broadcast settings buttons
@Bot.on_callback_query(filters.regex(r"^cast_"))
async def cast_callback(client: Client, callback: CallbackQuery):
    data = callback.data
    chat_id = callback.message.chat.id
    message_id = callback.message.id

    try:
        if data == "cast_broadcast":
            await db.set_temp_state(chat_id, "awaiting_broadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="<code>Please send a message to broadcast</code>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("Please send a message to broadcast.")

        elif data == "cast_pbroadcast":
            await db.set_temp_state(chat_id, "awaiting_pbroadcast_input")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="<code>Please send a message to broadcast and pin</code>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("Please send a message to broadcast and pin.")

        elif data == "cast_dbroadcast":
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_message")
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="<code>Please send a message to broadcast with auto-delete</code>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            await callback.answer("Please send a message to broadcast with auto-delete.")

        elif data == "cast_refresh":
            await show_broadcast_settings(client, chat_id, message_id)
            await callback.answer("Settings refreshed!")

        elif data == "cast_close":
            await db.set_temp_state(chat_id, "")
            await callback.message.delete()
            await callback.answer("Settings closed!")

        elif data == "cast_back":
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id, message_id)
            await callback.answer("Back to settings!")

    except Exception as e:
        logger.error(f"Failed to handle callback {data}: {e}")
        await client.send_message(
            chat_id=chat_id,
            text="<b>Error: Failed to process callback. Please try again.</b>",
            parse_mode=ParseMode.HTML
        )
        await db.set_temp_state(chat_id, "")

# Handle broadcast input
@Bot.on_message(filters.private & admin & filters.create(broadcast_state_filter) & filters.create(exclude_link_generator_states))
async def handle_broadcast_input(client: Client, message: Message):
    chat_id = message.chat.id
    state = await db.get_temp_state(chat_id)
    logger.info(f"Received broadcast input for chat {chat_id} in state {state}")

    try:
        # Send immediate acknowledgment
        ack_msg = await message.reply("<i>Message received, processing...</i>", quote=True)

        if state == "awaiting_broadcast_input":
            query = await db.full_userbase()
            broadcast_msg = message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>", quote=True)
            await ack_msg.delete()
            for user_id in query:
                try:
                    await client.get_users(user_id)
                    await broadcast_msg.copy(user_id)
                    successful += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    await broadcast_msg.copy(user_id)
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
                except PeerIdInvalid:
                    await db.del_user(user_id)
                    unsuccessful += 1
                    logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
                except Exception as e:
                    unsuccessful += 1
                    logger.error(f"Failed to send message to {user_id}: {e}")
                total += 1

            status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

            await pls_wait.edit(status)
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_pbroadcast_input":
            query = await db.full_userbase()
            broadcast_msg = message
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast processing...</i>", quote=True)
            await ack_msg.delete()
            for user_id in query:
                try:
                    await client.get_users(user_id)
                    sent_msg = await broadcast_msg.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    sent_msg = await broadcast_msg.copy(user_id)
                    await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
                except PeerIdInvalid:
                    await db.del_user(user_id)
                    unsuccessful += 1
                    logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
                except Exception as e:
                    unsuccessful += 1
                    logger.error(f"Failed to send or pin message to {user_id}: {e}")
                total += 1

            status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

            await pls_wait.edit(status)
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)

        elif state == "awaiting_dbroadcast_message":
            await db.set_temp_state(chat_id, "awaiting_dbroadcast_duration")
            await db.set_temp_data(chat_id, "broadcast_message", message)
            await ack_msg.delete()
            await message.reply(
                "<b>Give me the duration in seconds.</b>",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Back", callback_data="cast_back"),
                        InlineKeyboardButton("Close", callback_data="cast_close")
                    ]
                ]),
                quote=True
            )

        elif state == "awaiting_dbroadcast_duration":
            try:
                duration = int(message.text)
            except ValueError:
                await ack_msg.delete()
                await message.reply("<b>Please use a valid duration in seconds.</b>", quote=True)
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            broadcast_msg = await db.get_temp_data(chat_id, "broadcast_message")
            if not broadcast_msg:
                await ack_msg.delete()
                await message.reply("<b>Error: No message found to broadcast.</b>", quote=True)
                await db.set_temp_state(chat_id, "")
                await show_broadcast_settings(client, chat_id)
                return

            query = await db.full_userbase()
            total = 0
            successful = 0
            blocked = 0
            deleted = 0
            unsuccessful = 0

            pls_wait = await message.reply("<i>Broadcast with auto-delete processing...</i>", quote=True)
            await ack_msg.delete()
            for user_id in query:
                try:
                    await client.get_users(user_id)
                    sent_msg = await broadcast_msg.copy(user_id)
                    await asyncio.sleep(duration)
                    await sent_msg.delete()
                    successful += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    sent_msg = await broadcast_msg.copy(user_id)
                    await asyncio.sleep(duration)
                    await sent_msg.delete()
                    successful += 1
                except UserIsBlocked:
                    await db.del_user(user_id)
                    blocked += 1
                except InputUserDeactivated:
                    await db.del_user(user_id)
                    deleted += 1
                except PeerIdInvalid:
                    await db.del_user(user_id)
                    unsuccessful += 1
                    logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
                except Exception as e:
                    unsuccessful += 1
                    logger.error(f"Failed to send or delete message to {user_id}: {e}")
                total += 1

            status = f"""<b><u>Broadcast with auto-delete completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

            await pls_wait.edit(status)
            await db.set_temp_state(chat_id, "")
            await db.set_temp_state(chat_id, "")
            await show_broadcast_settings(client, chat_id)

    except Exception as e:
        logger.error(f"Failed to process broadcast input: {e}")
        await message.reply_text(
            f"<blockquote><b>Failed to process broadcast:</b></blockquote>\n<i>{e}</i>",
            parse_mode=ParseMode.HTML,
            quote=True
        )
        await db.set_temp_state(chat_id, "")
        await show_broadcast_settings(client, chat_id)

# Command to broadcast a pinned message
@Bot.on_message(filters.command('pbroadcast') & filters.private & admin)
async def send_pin_text(client: Client, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast processing...</i>", quote=True)
        for user_id in query:
            try:
                await client.get_users(user_id)
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(user_id)
                await client.pin_chat_message(chat_id=user_id, message_id=sent_msg.id, quote=True)
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send or pin message to {user_id}: {e}")
            total += 1

        status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)
    else:
        msg = await message.reply("<code>Please reply to a message to broadcast</code>", quote=True)
        await asyncio.sleep(8)
        await msg.delete()

# Command to broadcast a message
@Bot.on_message(filters.command('broadcast') & filters.private & admin)
async def send_text(client: Client, message: Message):
    if message.reply_to_message:
        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast processing...</i>", quote=True)
        for user_id in query:
            try:
                await client.get_users(user_id)
                await broadcast_msg.copy(user_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(user_id)
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send message to {user_id}: {e}")
            total += 1

        status = f"""<b><u>Broadcast completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)
    else:
        msg = await message.reply("<code>Please reply to a message to broadcast</code>", quote=True)
        await asyncio.sleep(8)
        await msg.delete()

# Command to broadcast with auto-delete
@Bot.on_message(filters.command('dbroadcast') & filters.private & admin)
async def delete_broadcast(client: Client, message: Message):
    if message.reply_to_message:
        try:
            duration = int(message.command[1])
        except (IndexError, ValueError):
            await message.reply("<b>Please use a valid duration in seconds.</b> Usage: /dbroadcast {duration}", quote=True)
            return

        query = await db.full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcast with auto-delete processing...</i>", quote=True)
        for user_id in query:
            try:
                await client.get_users(user_id)
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                sent_msg = await broadcast_msg.copy(user_id)
                await asyncio.sleep(duration)
                await sent_msg.delete()
                successful += 1
            except UserIsBlocked:
                await db.del_user(user_id)
                blocked += 1
            except InputUserDeactivated:
                await db.del_user(user_id)
                deleted += 1
            except PeerIdInvalid:
                await db.del_user(user_id)
                unsuccessful += 1
                logger.warning(f"Removed invalid user ID {user_id} from database due to PeerIdInvalid")
            except Exception as e:
                unsuccessful += 1
                logger.error(f"Failed to send or delete message to {user_id}: {str(e)}")
            total += 1

        status = f"""<b><u>Broadcast with auto-delete completed</u></b>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code>"""

        await pls_wait.edit(status)
    else:
        msg = await message.reply("Please reply to a message to broadcast with auto-delete.", quote=True)
        await asyncio.sleep(8)
        await msg.delete()
