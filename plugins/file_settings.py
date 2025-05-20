from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Update
from config import PROTECT_CONTENT, HIDE_CAPTION, DISABLE_CHANNEL_BUTTON, BUTTON_NAME, BUTTON_LINK, update_setting, get_settings

# States for conversation handler
SET_BUTTON_NAME, SET_BUTTON_LINK = range(2)

async def show_settings_message(client, message_or_callback, is_callback=False):
    settings = get_settings()
    
    # Create the settings text in the requested format
    settings_text = "Fɪʟᴇs ʀᴇʟᴀᴛᴇᴅ sᴇᴛᴛɪɴɢs:\n\n"
    settings_text += f"›› Pʀᴏᴛᴇᴄᴛ ᴄᴏɴᴛᴇɴᴛ: {'Eɴᴀʙʟᴇᴅ' if settings['PROTECT_CONTENT'] else 'Dɪsᴀʙʟᴇᴅ'} {'✅' if settings['PROTECT_CONTENT'] else '❌'}\n"
    settings_text += f"›› Hɪᴅᴇ ᴄᴀᴘᴛɪᴏɴ: {'Eɴᴀʙʟᴇᴅ' if settings['HIDE_CAPTION'] else 'Dɪsᴀʙʟᴇᴅ'} {'✅' if settings['HIDE_CAPTION'] else '❌'}\n"
    settings_text += f"›› Cʜᴀɴɴᴇʟ ʙᴜᴛᴛᴏɴ: {'Eɴᴀʙʟᴇᴅ' if not settings['DISABLE_CHANNEL_BUTTON'] else 'Dɪsᴀʙʟᴇᴅ'} {'✅' if not settings['DISABLE_CHANNEL_BUTTON'] else '❌'}\n\n"
    settings_text += f"›› Bᴜᴛᴛᴏɴ Nᴀᴍᴇ: {settings['BUTTON_NAME'] if settings['BUTTON_NAME'] else 'not set'}\n"
    settings_text += f"›› Bᴜᴛᴛᴏɴ Lɪɴᴋ: {settings['BUTTON_LINK'] if settings['BUTTON_LINK'] else 'not set'}\n\n"
    settings_text += "Cʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs ᴛᴏ ᴄʜᴀɴɢᴇ sᴇᴛᴛɪɴɢs"

    # Create inline buttons for toggling settings
    buttons = [
        [
            InlineKeyboardButton("PC", callback_data="toggle_protect_content"),
            InlineKeyboardButton("HC", callback_data="toggle_hide_caption"),
            InlineKeyboardButton("CB", callback_data="toggle_channel_button"),
            InlineKeyboardButton("SB", callback_data="set_button"),
        ],
        [
            InlineKeyboardButton("REFRESH", callback_data="refresh_settings"),
            InlineKeyboardButton("back", callback_data="go_back"),
        ]
    ]

    if is_callback:
        await message_or_callback.message.edit_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await message_or_callback.reply_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_message(filters.command("fsettings") & filters.private)
async def fsettings_command(client, message):
    await show_settings_message(client, message)

@Client.on_callback_query(filters.regex("toggle_protect_content"))
async def toggle_protect_content(client, callback_query):
    await update_setting("PROTECT_CONTENT", not get_settings()["PROTECT_CONTENT"])
    await show_settings_message(client, callback_query, is_callback=True)
    await callback_query.answer("Pʀᴏᴛᴇᴄᴛ Cᴏɴᴛᴇɴᴛ ᴛᴏɢɢʟᴇᴅ!")

@Client.on_callback_query(filters.regex("toggle_hide_caption"))
async def toggle_hide_caption(client, callback_query):
    await update_setting("HIDE_CAPTION", not get_settings()["HIDE_CAPTION"])
    await show_settings_message(client, callback_query, is_callback=True)
    await callback_query.answer("Hɪᴅᴇ Cᴀᴘᴛɪᴏɴ ᴛᴏɢɢʟᴇᴅ!")

@Client.on_callback_query(filters.regex("toggle_channel_button"))
async def toggle_channel_button(client, callback_query):
    await update_setting("DISABLE_CHANNEL_BUTTON", not get_settings()["DISABLE_CHANNEL_BUTTON"])
    await show_settings_message(client, callback_query, is_callback=True)
    await callback_query.answer("Cʜᴀɴɴᴇʟ Bᴜᴛᴛᴏɴ ᴛᴏɢɢʟᴇᴅ!")

@Client.on_callback_query(filters.regex("refresh_settings"))
async def refresh_settings_message(client, callback_query):
    await show_settings_message(client, callback_query, is_callback=True)
    await callback_query.answer("Sᴇᴛᴛɪɴɢs ʀᴇғʀᴇsʜᴇᴅ!")

@Client.on_callback_query(filters.regex("go_back"))
async def go_back(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer("Bᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴍᴇɴᴜ!")

@Client.on_callback_query(filters.regex("set_button"))
async def set_button_start(client, callback_query):
    print("Set Button callback triggered")
    await callback_query.message.reply_text("Pʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ Bᴜᴛᴛᴏɴ Nᴀᴍᴇ:")
    await callback_query.answer()
    # Register the next step handler for Button Name
    client.add_handler(MessageHandler(set_button_name, filters.private & filters.user(callback_query.from_user.id)), group=1)

async def set_button_name(client, message):
    new_button_name = message.text.strip()
    await update_setting("BUTTON_NAME", new_button_name)
    await message.reply_text("Bᴜᴛᴛᴏɴ Nᴀᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ! Nᴏᴡ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ Bᴜᴛᴛᴏɴ Lɪɴᴋ:")
    # Register the next step handler for Button Link
    client.add_handler(MessageHandler(set_button_link, filters.private & filters.user(message.from_user.id)), group=1)

async def set_button_link(client, message):
    new_button_link = message.text.strip()
    await update_setting("BUTTON_LINK", new_button_link)
    await message.reply_text("Bᴜᴛᴛᴏɴ Lɪɴᴋ ᴜᴘᴅᴀᴛᴇᴅ! Uꜱᴇ /fsettings ᴛᴏ sᴇᴇ ᴛʜᴇ ᴜᴘᴅᴀᴛᴇᴅ sᴇᴛᴛɪɴɢs.")
    # Remove the handlers to clean up
    client.remove_handler(MessageHandler(set_button_name, filters.private & filters.user(message.from_user.id)), group=1)
    client.remove_handler(MessageHandler(set_button_link, filters.private & filters.user(message.from_user.id)), group=1)