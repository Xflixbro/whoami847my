#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import os
from os import environ, getenv
import logging
from logging.handlers import RotatingFileHandler
from pyrogram import filters
from database.database import db  # Updated import

# MehediYT69
# --------------------------------------------
# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
#--------------------------------------------

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002170811388"))  # Your db channel Id
OWNER = os.environ.get("OWNER", "MehediYT69")  # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "7328629001"))  # Owner id
#--------------------------------------------
PORT = os.environ.get("PORT", "8080")
#--------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "animelord")
# --------------------------------------------
FSUB_LINK_EXPIRY = int(getenv("FSUB_LINK_EXPIRY", "10"))  # 0 means no expiry
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/CodeflixSupport")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
# --------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")

# --------------------------------------------
# List of images for random selection in /start, /help, /about
RANDOM_IMAGES = [
    "https://i.postimg.cc/JnJ32yfG/1813ee0c.jpg",
    "https://i.postimg.cc/0j0Y9T2v/28b1fa77.jpg",
    "https://i.postimg.cc/sxrPdjzK/169123a1.jpg",
    "https://i.postimg.cc/pTNzzWmx/6592fdce.jpg",
    "https://i.postimg.cc/Wbsm51X1/e6afff7a.jpg",
    "https://i.postimg.cc/8zV2KWxr/dc021327.jpg",
    "https://i.postimg.cc/Wb9ZS6d5/bca92b0b.jpg",
    "https://i.postimg.cc/9MtR9G3t/c4b45c9f.jpg",
    "https://i.postimg.cc/0yMzngRN/ce1ae80f.jpg",
    "https://i.postimg.cc/NFdKJBjK/f8ca42f6.jpg",
    "https://i.postimg.cc/5Njy9ctm/ec4acf97.jpg",
    "https://i.postimg.cc/Kj8zgwDx/04efc805.jpg",
    "https://i.postimg.cc/13jpRcP8/f2ce6fdf.jpg",
    "https://i.postimg.cc/L5JSSpVY/af94fb0f.jpg",
    "https://i.postimg.cc/YSQhc1SK/06dc3bf7.jpg",
    "https://i.postimg.cc/TwGhTpyy/99376c97.jpg",
    "https://i.postimg.cc/HxxD0gRZ/ae49a6f5.jpg",
    "https://i.postimg.cc/K8S26C3j/fdee09a7.jpg",
    "https://i.postimg.cc/90shFnxx/7963dd00.jpg",
    "https://i.postimg.cc/j5ZqKv09/1c847bb6.jpg",
]

SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "linkshortify.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/hwdownload/3")
SHORT_MSG = "<b>⌯ Here is Your Download Link, Must Watch Tutorial Before Clicking On Download...</b>"

SHORTENER_PIC = os.environ.get("SHORTENER_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
# --------------------------------------------

# --------------------------------------------
HELP_TXT = os.environ.get("HELP_TXT","<blockquote><b>ʜᴇʟʟᴏ {first}<b/></blockquote>\n\n<b><blockquote>◈ ᴛʜɪs ɪs ᴀɴ ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ ᴡᴏʀᴋ ғᴏʀ @MehediYT69\n\n❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs\n├/start : sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n├/about : ᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ\n├/commands : ꜰᴏʀ ɢᴇᴛ ᴀʟʟ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ʟɪꜱᴛ\n└/help : ʜᴇʟᴘ ʀᴇʟᴀᴛᴇᴅ ʙᴏᴛ\n\n sɪᴍᴘʟʏ ᴄʟɪᴄᴋ ᴏɴ ʟɪɴᴋ ᴀɴᴅ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜᴀᴛs ɪᴛ.....!\n\n ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ <a href=https://t.me/Anime_Lord_Bots>Aɴɪᴍᴇ Lᴏʀᴅ</a></blockquote></b>")
ABOUT_TXT = os.environ.get("ABOUT_TXT","<blockquote><b>ʜᴇʟʟᴏ {first}<b/></blockquote>\n\n<b><blockquote>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/Anime_Lord_Bots>MehediYT</a>\n◈ ꜰᴏᴜɴᴅᴇʀ ᴏꜰ : <a href=@who_am_i_69>WHO-AM-I</a>\n◈ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/Anime_Lord_Official>Aɴɪᴍᴇ Lᴏʀᴅ</a>\n◈ sᴇʀɪᴇs ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/Anime_Lord_Series>Aɴɪᴍᴇ Lᴏʀᴅ sᴇʀɪᴇs ғʟɪx</a>\n◈ ᴀᴅᴜʟᴛ ᴍᴀɴʜᴡᴀ : <a href=https://t.me/Anime_Lord_Hentai>Aɴɪᴍᴇ Lᴏʀᴅ Pᴏʀɴʜᴡᴀs</a>\n◈ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/Anime_Lord_Bots>Aɴɪᴍᴇ Lᴏʀᴅ</a></blockquote></b>")
# --------------------------------------------
START_MSG = os.environ.get("START_MESSAGE", "<blockquote><b>ʜᴇʟʟᴏ {first}</b></blockquote>\n\n<blockquote><b> ɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ ᴄʀᴇᴀᴛᴇᴅ ʙʏ  <a href=https://t.me/Anime_Lord_Official>Aɴɪᴍᴇ Lᴏʀᴅ</a>, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</blockquote></b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /auto_delete :</b> ᴍᴀɴᴀɢᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇᴛᴛɪɴɢs
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜴ ᴀᴅᴍɪɴs
<b>›› /addpremium :</b> ᴀᴅᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /delpremium :</b> ʀᴇᴍᴏᴠᴇ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /premiumusers :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀs
<b>›› /broadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
<b>›› /stats :</b> ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs
<b>›› /logs :</b> ɢᴇᴛ ʟᴏɢs ᴏꜰ ʙᴏᴛ
<b>›› /setvar :</b> sᴇᴛ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ᴠᴀʀɪᴀʙʟᴇ
<b>›› /getvar :</b> ɢᴇᴛ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ᴠᴀʀɪᴀʙʟᴇ
<b>›› /restart :</b> ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"""

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• ʙʏ @Anime_Lord_Official</b>")
# --------------------------------------------
# Set true if you want Disable your Channel Posts Share button
# --------------------------------------------
BOT_STATS_TEXT = "<b>BOT FUCKTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"

# ==========================(BUY PREMIUM)====================#
OWNER_TAG = os.environ.get("OWNER_TAG", "Aɴɪᴍᴇ Lᴏʀᴅ")
UPI_ID = os.environ.get("UPI_ID", "yourname@upi")  # Replace with your valid UPI ID
QR_PIC = os.environ.get("QR_PIC", "https://telegra.ph/file/3e83c69804826b3cba066.jpg")
SCREENSHOT_URL = os.environ.get("SCREENSHOT_URL", "t.me/mehediyt69")
# --------------------------------------------
# Time and its price
# 7 Days
PRICE1 = os.environ.get("PRICE1", "0 rs")
# 1 Month
PRICE2 = os.environ.get("PRICE2", "60 rs")
# 3 Month
PRICE3 = os.environ.get("PRICE3", "150 rs")
# 6 Month
PRICE4 = os.environ.get("PRICE4", "280 rs")
# 1 Year
PRICE5 = os.environ.get("PRICE5", "550 rs")

# ====================(END)========================#

# Default settings (loaded dynamically in bot.py)
PROTECT_CONTENT = False
HIDE_CAPTION = False
DISABLE_CHANNEL_BUTTON = True
BUTTON_NAME = None
BUTTON_LINK = None

# Function to update settings (used by file_settings.py)
async def update_setting(setting_name, value):
    await db.update_setting(setting_name, value)
    # Update local variables (optional, for immediate use)
    global PROTECT_CONTENT, HIDE_CAPTION, DISABLE_CHANNEL_BUTTON, BUTTON_NAME, BUTTON_LINK
    if setting_name == "PROTECT_CONTENT":
        PROTECT_CONTENT = value
    elif setting_name == "HIDE_CAPTION":
        HIDE_CAPTION = value
    elif setting_name == "DISABLE_CHANNEL_BUTTON":
        DISABLE_CHANNEL_BUTTON = value
    elif setting_name == "BUTTON_NAME":
        BUTTON_NAME = value
    elif setting_name == "BUTTON_LINK":
        BUTTON_LINK = value

# Function to get all settings (used to display in /fsettings)
def get_settings():
    return {
        "PROTECT_CONTENT": PROTECT_CONTENT,
        "HIDE_CAPTION": HIDE_CAPTION,
        "DISABLE_CHANNEL_BUTTON": DISABLE_CHANNEL_BUTTON,
        "BUTTON_NAME": BUTTON_NAME,
        "BUTTON_LINK": BUTTON_LINK
    }

LOG_FILE_NAME = "animelordbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Admin filter to check if user is an admin or owner
async def admin_filter(_, __, message):
    admin_ids = await db.get_all_admins()
    return message.from_user.id in admin_ids or message.from_user.id == OWNER_ID

admin = filters.create(admin_filter)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
