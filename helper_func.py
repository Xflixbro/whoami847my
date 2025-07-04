#(©)AnimeLord_Bots
#Mehediyt69 on Tg #Dont remove this line

import base64
import re
import asyncio
import time
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import *
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from shortzy import Shortzy
from pyrogram.errors import FloodWait
from database.database import *
import psutil
from datetime import datetime

async def generate_stats_message(client):
    """Generate a comprehensive stats message"""
    try:
        # Get database stats
        db_stats = await db.get_bot_stats()
        
        # Get system information
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        ram_usage = f"{memory.used/1024/1024:.2f} MB / {memory.total/1024/1024:.2f} MB"
        
        # Get uptime
        uptime = datetime.now() - client.uptime
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Format storage
        storage_used = db_stats['storage_used']
        storage_str = f"{storage_used/1024/1024:.2f} MB" if storage_used < 1024*1024*1024 else f"{storage_used/1024/1024/1024:.2f} GB"
        
        stats_text = f"""
<b>📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs 📊</b>

<u>📈 Usᴀɢᴇ Sᴛᴀᴛs</u>
» ᴛᴏᴛᴀʟ ᴜsᴇʀs: <code>{db_stats['total_users']}</code>
» ᴛᴏᴛᴀʟ ꜰɪʟᴇs: <code>{db_stats['total_files']}</code>
» ᴜsᴇᴅ sᴛᴏʀᴀɢᴇ: <code>{storage_str}</code>

<u>🤖 Bᴏᴛ Dᴇᴛᴀɪʟs 🤖</u>
» ᴜᴘᴛɪᴍᴇ: <code>{uptime_str}</code>
» ʀᴀᴍ: <code>{ram_usage} ({memory.percent}%)</code>
» ᴄᴘᴜ: <code>{cpu_usage}%</code>
"""
        return stats_text
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        return "⚠️ Error fetching bot statistics"


async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await db.admin_exist(user_id)])
    except Exception as e:
        print(f"! Exception in check_admin: {e}")
        return False

async def is_subscribed(client, user_id):
    settings = await db.get_settings()
    if not settings.get('FORCE_SUB_ENABLED', True):
        return True

    channel_ids = await db.show_channels()

    if not channel_ids:
        return True

    if user_id == OWNER_ID:
        return True

    for cid in channel_ids:
        if await db.get_channel_temp_off(cid):
            continue
        if not await is_sub(client, user_id, cid):
            mode = await db.get_channel_mode(cid)
            if mode == "on":
                await asyncio.sleep(2)
                if await is_sub(client, user_id, cid):
                    continue
            return False

    return True

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        logger.debug(f"[SUB] User {user_id} in {channel_id} with status {status}")
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }
    except UserNotParticipant:
        mode = await db.get_channel_mode(channel_id)
        logger.debug(f"[NOT SUB] User {user_id} not in {channel_id}, mode={mode}")
        if mode == "on":
            exists = await db.req_user_exist(channel_id, user_id)
            logger.debug(f"[REQ] User {user_id} join request for {channel_id}: {exists}")
            return exists
        logger.debug(f"[NOT SUB] User {user_id} not in {channel_id} and mode != on")
        return False
    except Exception as e:
        logger.error(f"[!] Eʀʀᴏʀ ɪɴ ɪꜱ_ꜱᴜʙ(): {e}")
        return False

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = r"https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

def get_exp_time(seconds):
    periods = [('days', 86400), ('hours', 3600), ('mins', 60), ('secs', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)} {period_name}'
    return result

async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    link = await shortzy.convert(link)
    return link

subscribed = filters.create(is_subscribed)
admin = filters.create(check_admin)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
