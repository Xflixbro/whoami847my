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

# ====================== BOT CONFIGURATION ======================
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "15529802"))
API_HASH = os.environ.get("API_HASH", "92bcb6aa798a6f1feadbc917fccb54d3")

# ====================== CHANNEL & OWNER INFO ======================
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002162795137"))
OWNER = os.environ.get("OWNER", "Mrxeontg")
OWNER_ID = int(os.environ.get("OWNER_ID", "821215952"))
ADMINS = [821215952, 7475545668]  # Add more admin IDs as needed

# ====================== SERVER CONFIG ======================
PORT = os.environ.get("PORT", "8080")

# ====================== DATABASE CONFIG ======================
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://SeriesXeonbot:SeriesXeonbot@cluster0.sxdov5x.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "XFLIX")

# ====================== BOT SETTINGS ======================
FSUB_LINK_EXPIRY = int(getenv("FSUB_LINK_EXPIRY", "10"))
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/CodeflixSupport")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))

# ====================== MEDIA FILES ======================
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")

RANDOM_IMAGES = [
    "https://myappme.shop/img/file_302.jpg",
    "https://myappme.shop/img/file_303.jpg",
    "https://myappme.shop/img/file_304.jpg"
]

# ====================== SHORTLINK CONFIG ======================
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "publicearn.online")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "de08290b12d9e34191f3a057070a50a18187fff3")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/hwdownload/3")
SHORT_MSG = "<b>⌯ Here is Your Download Link, Must Watch Tutorial Before Clicking On Download...</b>"
SHORTENER_PIC = os.environ.get("SHORTENER_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")

# ====================== REFERRAL SYSTEM ======================
REFERRAL_REWARD_HOURS = 24
REFERRAL_REQUIREMENT = 5
REFERRAL_BONUS_DAYS = 2

START_MSG = os.environ.get("START_MESSAGE", """<b>Hello {first}!</b>

<b>I am a Premium File Store Bot, I can provide private files through a specific link!</b>

<b>🎁 Referral Bonus:</b>
• Get {hours} hours of premium for every {req} friends you refer
• No link shorteners during reward period

<b>Use /ref to get your referral link</b>""").format(
    first="{first}",
    hours=REFERRAL_REWARD_HOURS,
    req=REFERRAL_REQUIREMENT
)

REFERRAL_MSG = """<b>🎁 <u>Referral Program</u></b>

<b>How it works:</b>
• Share your referral link with friends
• When they join using your link, you get credit
• Every {required} successful referrals = {hours} hours of premium benefits
• Premium benefits bypass all link shorteners

<b>Your Referral Link:</b>
<code>{referral_link}</code>

<b>Your Stats:</b>
• Total Referrals: {ref_count}
• Next Reward: {remaining_refs} more referrals needed

<b>Current Status:</b>
{reward_status}

<b>Click below to share your link easily!</b>"""

PREPLANSS_TXT = """<b>👋 Hey {first}!</b>
    
<b>🎁 Premium Benefits:</b>
• No link shorteners
• Get direct files
• Ad-free experience
• Unlimited movies and series
• Full admin support
• Best value for money
• Priority content
• Exclusive discounts

<b>🎖️ Premium Plans:</b>
• 01 Month ➠ INR 249/$7
• 02 Month ➠ INR 349/$15
• 03 Month ➠ INR 449/$39
• 06 Month ➠ INR 649/$49
• 09 Month ➠ INR 899/$79

<b>🌟 Referral Program</b>
• Get {ref_hours} hours premium for every {ref_req} friends you refer
• No link shorteners during reward period
• Unlimited referral bonuses

<b>🏷️ <a href="https://t.me/Xeonflixadmin_bot">Click Here To Buy Premium</a></b>

<b>Note:</b> USD rates are set slightly higher due to international transaction and service fees.""".format(
    first="{first}",
    ref_hours=REFERRAL_REWARD_HOURS,
    ref_req=REFERRAL_REQUIREMENT
)

# ====================== OTHER MESSAGES ======================
SOURCE_TXT = """<b>⚠️ This is not an open source project
- Source code - <a href="https://t.me/+y6mFtiS5JQFkNThl">Here</a></b>"""
    
CREDIT_INFO = """
<b>⍟───[ My Credits ]───⍟
➥ Owner : <a href='t.me/Xeonflixadmin'>Xeon</a>
➥ Base Code : <a href='t.me/cosmic_freak'>Yato</a>
➥ Extra Features Code : <a href='t.me/MrXeonTG'>Gojo Satoru</a>
➥ Thanks to : <a href='tg://settings'>This Person</a></b>"""

HELP_TXT = os.environ.get("HELP_TXT", """<b>Hello {first}!</b>

<b>This is a File to Link bot working for @MehediYT69</b>

<b>Bot Commands:</b>
/start : Start the bot
/about : Our Information
/commands : For get all admin commands list
/help : Help related bot

Simply click on link and start the bot join both channels and try again that's it!

Developed by <a href="https://t.me/Anime_Lord_Bots">Anime Lord</a>""")

ABOUT_TXT = """<b>★ Developer : <a href="https://t.me/MrXeonTg">Mr Xeon</a>
★ My best friend : <a href='tg://settings'>This Person</a>
★ Library : <a href='https://docs.pyrogram.org/'>Pyrogram v2</a>
★ Language : <a href='https://docs.python.org/3/'>Python 3</a>
★ Database : <a href='https://www.mongodb.com/docs/'>Mongo DB</a>
★ Bot Server : <a href='https://heroku.com'>Heroku</a>
★ Build Status : v5.4.1 [Advance Features]</b>"""

FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", """<b>Hello {first}!</b>

<b>Join our channels and then click on reload button to get your requested file.</b>""")

CMD_TXT = """<b>» Admin Commands:</b>

<b>›› /start :</b> Start the bot & get posts
<b>›› /batch :</b> Create links for multiple posts
<b>›› /custom_batch :</b> Create custom batch from channel/group
<b>›› /genlink :</b> Create link for a single post
<b>›› /flink :</b> Set auto batch format
<b>›› /forcesub :</b> Get all force sub settings
<b>›› /admin :</b> Manage admins (add/remove/list)
<b>›› /user :</b> Get user-related tools
<b>›› /auto_delete :</b> Set auto-delete timer
<b>›› /fsettings :</b> Manage force subscriptions
<b>›› /premium_cmd :</b> Manage premium users
<b>›› /broadcast_cmd :</b> Broadcast messages
<b>›› /myplan :</b> Check your premium status & details
<b>›› /count :</b> Track shortener clicks & analytics
<b>›› /ref :</b> Get your referral link and stats
<b>›› /referral_stats :</b> View referral statistics (admin only)"""

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• By @Anime_Lord_Official</b>")

# ====================== PREMIUM CONFIG ======================
OWNER_TAG = os.environ.get("OWNER_TAG", "Anime Lord")
UPI_ID = os.environ.get("UPI_ID", "yourname@upi")
QR_PIC = os.environ.get("QR_PIC", "https://telegra.ph/file/3e83c69804826b3cba066.jpg")
SCREENSHOT_URL = os.environ.get("SCREENSHOT_URL", "t.me/mehediyt69")

PRICE1 = os.environ.get("PRICE1", "0 rs")
PRICE2 = os.environ.get("PRICE2", "60 rs")
PRICE3 = os.environ.get("PRICE3", "150 rs")
PRICE4 = os.environ.get("PRICE4", "280 rs")
PRICE5 = os.environ.get("PRICE5", "550 rs")

# ====================== BOT SETTINGS ======================
PROTECT_CONTENT = False
HIDE_CAPTION = False
DISABLE_CHANNEL_BUTTON = True
BUTTON_NAME = None
BUTTON_LINK = None

async def update_setting(setting_name, value):
    await db.update_setting(setting_name, value)
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

def get_settings():
    return {
        "PROTECT_CONTENT": PROTECT_CONTENT,
        "HIDE_CAPTION": HIDE_CAPTION,
        "DISABLE_CHANNEL_BUTTON": DISABLE_CHANNEL_BUTTON,
        "BUTTON_NAME": BUTTON_NAME,
        "BUTTON_LINK": BUTTON_LINK
    }

# ====================== LOGGING CONFIG ======================
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

# ====================== ADMIN FILTER ======================
async def admin_filter(_, __, message):
    if not message.from_user:
        return False
    admin_ids = await db.get_all_admins()
    return message.from_user.id in admin_ids or message.from_user.id == OWNER_ID

admin = filters.create(admin_filter)
