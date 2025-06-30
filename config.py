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
from database.database import db

# --------------------------------------------
# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "15529802"))
API_HASH = os.environ.get("API_HASH", "92bcb6aa798a6f1feadbc917fccb54d3")
#--------------------------------------------

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002162795137"))  # Your db channel Id
OWNER = os.environ.get("OWNER", "Mrxeontg")  # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "821215952"))  # Owner id
# List of admin user IDs who can change file settings
ADMINS = [821215952, 7475545668]  # Default is just the owner, add more like [821215952, 123456789]
#--------------------------------------------
PORT = os.environ.get("PORT", "8080")
#--------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://SeriesXeonbot:SeriesXeonbot@cluster0.sxdov5x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "XFLIX")
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
    "https://myappme.shop/img/file_302.jpg",
    "https://myappme.shop/img/file_303.jpg",
    "https://myappme.shop/img/file_304.jpg"
]

SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "publicearn.online")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "de08290b12d9e34191f3a057070a50a18187fff3")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/hwdownload/3")
SHORT_MSG = "<b>⌯ Here is Your Download Link, Must Watch Tutorial Before Clicking On Download...</b>"

SHORTENER_PIC = os.environ.get("SHORTENER_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
# --------------------------------------------

# Referral System Configuration
REFERRAL_REWARD_HOURS = 24  # Hours of premium per successful referral
REFERRAL_REQUIREMENT = 5    # Number of referrals needed for reward
REFERRAL_BONUS_DAYS = 2     # Bonus days for special promotions

START_MSG = os.environ.get("START_MESSAGE", """<blockquote><b>ʜᴇʟʟᴏ {first}</b></blockquote>

<blockquote><b>ɪ ᴀᴍ ᴘʀᴇᴍɪᴜᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ ᴘʀᴏᴠɪᴅᴇ ᴘʀɪᴠᴀᴛᴇ ꜰɪʟᴇꜱ ᴛʜʀᴏᴜɢʜ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ʟɪɴᴋ..!</b></blockquote>

<blockquote><b>🎁 ʀᴇꜰᴇʀʀᴀʟ ʙᴏɴᴜꜱ:</b>
• ɢᴇᴛ {hours} ʜᴏᴜʀꜱ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ ᴇᴠᴇʀʏ {req} ꜰʀɪᴇɴᴅꜱ ʏᴏᴜ ʀᴇꜰᴇʀ
• ɴᴏ ʟɪɴᴋ ꜱʜᴏʀᴛᴇɴᴇʀꜱ ᴅᴜʀɪɴɢ ʀᴇᴡᴀʀᴅ ᴘᴇʀɪᴏᴅ</blockquote>

<b>ᴜꜱᴇ /ref ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ</b>""".format(
    hours=REFERRAL_REWARD_HOURS,
    req=REFERRAL_REQUIREMENT
))

REFERRAL_MSG = """<b>🎁 <u>Referral Program</u></b>

<blockquote>🔹 <b>How it works:</b>
• Share your referral link with friends
• When they join using your link, you get credit
• Every {required} successful referrals = {hours} hours of premium benefits
• Premium benefits bypass all link shorteners</blockquote>

<blockquote>✨ <b>Your Referral Link:</b>
<code>{referral_link}</code></blockquote>

<blockquote>📊 <b>Your Stats:</b>
• Total Referrals: {ref_count}
• Next Reward: {remaining_refs} more referrals needed</blockquote>

<blockquote>⏳ <b>Current Status:</b>
{reward_status}</blockquote>

<b>Click below to share your link easily!</b>"""

PREPLANSS_TXT = """<b>👋 ʜᴇʏ {first}
    
<blockquote>🎁 ᴘʀᴇᴍɪᴜᴍ ʙᴇɴɪꜰɪᴛꜱ

❏ ɴᴏ ʟɪɴᴋ ꜱʜᴏʀᴛᴇɴᴇʀ
❏ ɢᴇᴛ ᴅɪʀᴇᴄᴛ ғɪʟᴇs   
❏ ᴀᴅ-ғʀᴇᴇ ᴇxᴘᴇʀɪᴇɴᴄᴇ                                        
❏ ᴜɴʟɪᴍɪᴛᴇᴅ ᴍᴏᴠɪᴇs ᴀɴᴅ sᴇʀɪᴇs                                                                        
❏ ꜰᴜʟʟ ᴀᴅᴍɪɴ sᴜᴘᴘᴏʀᴛ
❏ ʙᴇꜱᴛ ᴠᴀʟᴜᴇ ꜰᴏʀ ᴍᴏɴᴇʏ
❏ ᴘʀɪᴏʀɪᴛʏ ᴄᴏɴᴛᴇɴᴛ
❏ ᴇxᴄʟᴜꜱɪᴠᴇ ᴅɪꜱᴄᴏᴜɴᴛꜱ </blockquote>

<blockquote>🎖️ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 

❏ 𝟶𝟷 ᴍᴏɴᴛʜ ➠ INR 249/$7
❏ 𝟶𝟸 ᴍᴏɴᴛʜ ➠ INR 349/$15
❏ 𝟶𝟹 ᴍᴏɴᴛʜ ➠ INR 449/$39
❏ 𝟶𝟼 ᴍᴏɴᴛʜ ➠ INR 649/$49
❏ 09 ᴍᴏɴᴛʜ ➠ INR 899/$79 </blockquote>

<blockquote>🌟 <b>Referral Program</b>
• Get {ref_hours} hours premium for every {ref_req} friends you refer
• No link shorteners during reward period
• Unlimited referral bonuses</blockquote>

🏷️ <a href="https://t.me/Xeonflixadmin_bot">𝗖𝗹𝗶𝗰𝗸 𝗛𝗲𝗿𝗲 𝗧𝗼 𝗕𝘂𝘆 𝗣𝗿𝗲𝗺𝗶𝘂𝗺</a>

ɴᴏᴛᴇ: ᴜꜱᴅ ʀᴀᴛᴇꜱ ᴀʀᴇ ꜱᴇᴛ ꜱʟɪɢʜᴛʟʏ ʜɪɢʜᴇʀ ᴅᴜᴇ ᴛᴏ ɪɴᴛᴇʀɴᴀᴛɪᴏɴᴀʟ ᴛʀᴀɴꜱᴀᴄᴛɪᴏɴ ᴀɴᴅ ꜱᴇʀᴠɪᴄᴇ ꜰᴇᴇꜱ.</b>""".format(
    first="{first}",
    ref_hours=REFERRAL_REWARD_HOURS,
    ref_req=REFERRAL_REQUIREMENT
)

SOURCE_TXT = """<b>
⚠️ ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ᴀɴ ᴏᴘᴇɴ sᴏᴜʀᴄᴇ ᴘʀᴏᴊᴇᴄᴛ
- ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ - <a href="https://t.me/+y6mFtiS5JQFkNThl">ʜᴇʀᴇ</a></b>"""
    
CREDIT_INFO = """
<b>⍟───[ ᴍʏ ᴄʀᴇᴅɪᴛꜱ ]───⍟
➥ ᴏᴡɴᴇʀ : <a href='t.me/Xeonflixadmin'>xᴇᴏɴ</a>
➥ ʙᴀꜱᴇ ᴄᴏᴅᴇ : <a href='t.me/cosmic_freak'>ʏᴀᴛᴏ</a>
➥ ᴇxᴛʀᴀ ꜰᴇᴀᴛᴜʀᴇꜱ ᴄᴏᴅᴇ : <a href='t.me/MrXeonTG'>ɢᴏᴊᴏ ꜱᴀᴛᴏʀᴜ</a>
➥ ᴛʜᴀɴᴋꜱ ᴛᴏ : <a href='tg://settings'>ᴛʜɪs ᴘᴇʀsᴏɴ</a>​</b>"""

# --------------------------------------------
HELP_TXT = os.environ.get("HELP_TXT","<blockquote><b>ʜᴇʟʟᴏ {first}<b/></blockquote>\n\n<b><blockquote>◈ ᴛʜɪs ɪs ᴀɴ ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ ᴡᴏʀᴋ ғᴏʀ @MehediYT69\n\n❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs\n├/start : sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n├/about : ᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ\n├/commands : ꜰᴏʀ ɢᴇᴛ ᴀʟʟ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ʟɪꜱᴛ\n└/help : ʜᴇʟᴘ ʀᴇʟᴀᴛᴇᴅ ʙᴏᴛ\n\n sɪᴍᴘʟʏ ᴄʟɪᴄᴋ ᴏɴ ʟɪɴᴋ ᴀɴᴅ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜᴀᴛs ɪᴛ.....!\n\n ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ <a href=https://t.me/Anime_Lord_Bots>Aɴɪᴍᴇ Lᴏʀᴅ</a></blockquote></b>")

ABOUT_TXT = """<blockquote expandable>★ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href="https://t.me/MrXeonTg">ᴍʀ xᴇᴏɴ</a>
★ ᴍʏ ʙᴇsᴛ ғʀɪᴇɴᴅ : <a href='tg://settings'>ᴛʜɪs ᴘᴇʀsᴏɴ</a>
★ ʟɪʙʀᴀʀʏ : <a href='https://docs.pyrogram.org/'>Pʏʀᴏɢʀᴀᴍ ᴠ2</a>
★ ʟᴀɴɢᴜᴀɢᴇ : <a href='https://docs.python.org/3/'>Pʏᴛʜᴏɴ 3</a>
★ ᴅᴀᴛᴀʙᴀsᴇ : <a href='https://www.mongodb.com/docs/'>Mᴏɴɢᴏ ᴅʙ</a>
★ ʙᴏᴛ sᴇʀᴠᴇʀ : <a href='https://heroku.com'>ʜᴇʀᴏᴋᴜ</a>
★ ʙᴜɪʟᴅ ꜱᴛᴀᴛᴜꜱ : ᴠ5.4.1 [ᴀᴅᴠᴀɴᴄᴇ ғᴇᴀᴛᴜʀᴇs]</blockquote>"""

# --------------------------------------------
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "<blockquote><b>ʜᴇʟʟᴏ {first}</b></blockquote>\n\n<blockquote><b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b></blockquote>")

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /start :</b> sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ & ɢᴇᴛ ᴘᴏsᴛs
<b>›› /batch :</b> ᴄʀᴇᴀᴛᴇ ʟɪɴᴋs ғᴏʀ ᴍᴜʟᴛɪᴘʟᴇ ᴘᴏsᴛs
<b>›› /custom_batch :</b> ᴄʀᴇᴀᴛᴇ ᴄᴜsᴛᴏᴍ ʙᴀᴛᴄʜ ғʀᴏᴍ ᴄʜᴀɴɴᴇʟ/ɢʀᴏᴜᴘ
<b>›› /genlink :</b> ᴄʀᴇᴀᴛᴇ ʟɪɴᴋ ғᴏʀ ᴀ sɪɴɢʟᴇ ᴘᴏsᴛ
<b>›› /flink :</b> ꜱᴇᴛ ᴀᴜᴛᴏ ʙᴀᴛᴄʜ ꜰᴏʀᴍᴀᴛ
<b>›› /forcesub :</b> ɢᴇᴛ ᴀʟʟ ғᴏʀᴄᴇ sᴜʙ sᴇᴛᴛɪɴɢs
<b>›› /admin :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴀᴅᴍɪɴs (ᴀᴅᴅ/ʀᴇᴍᴏᴠᴇ/ʟɪsᴛ)
<b>›› /user :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ɢᴇᴛ ᴜsᴇʀ-ʀᴇʟᴀᴛᴇᴅ ᴛᴏᴏʟs
<b>›› /auto_delete :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ sᴇᴛ ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇʀ
<b>›› /fsettings :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴍᴀɴᴀɢᴇ ғᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴs
<b>›› /premium_cmd :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs
<b>›› /broadcast_cmd :</b> ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀᴢᴇs
<b>›› /myplan :</b> ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴛᴀᴛᴜs & ᴅᴇᴛᴀɪʟs
<b>›› /count :</b> ᴛʀᴀᴄᴋ sʜᴏʀᴛɴᴇʀ ᴄʟɪᴄᴋs & ᴀɴᴀʟʏᴛɪᴄs
<b>›› /ref :</b> ɢᴇᴛ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ ᴀɴᴅ sᴛᴀᴛs
<b>›› /referral_stats :</b> ᴠɪᴇᴡ ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛɪsᴛɪᴄs (ᴀᴅᴍɪɴ ᴏɴʟʏ)"""

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• ʙʏ @Anime_Lord_Official</b>")

# ==========================(BUY PREMIUM)====================#
OWNER_TAG = os.environ.get("OWNER_TAG", "Aɴɪᴍᴇ Lᴏʀᴅ")
UPI_ID = os.environ.get("UPI_ID", "yourname@upi")  # Replace with your valid UPI ID
QR_PIC = os.environ.get("QR_PIC", "https://telegra.ph/file/3e83c69804826b3cba066.jpg")
SCREENSHOT_URL = os.environ.get("SCREENSHOT_URL", "t.me/mehediyt69")

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
