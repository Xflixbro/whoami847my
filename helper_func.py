#
# Copyright © 2025 by AnimeLord-Bots@Github, <https://github.com/AnimeLord-Bots>
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.

import base64
import re
import asyncio
import time
import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from config import *
from database.database import db
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from short_url import shorten_url

logger = logging.getLogger(__name__)

async def check_admin(filter, client, update):
    """Check if a user is an admin or owner."""
    try:
        user_id = update.from_user.id       
        return any([user_id == OWNER_ID, await db.admin_exist(user_id)])
    except Exception as e:
        logger.error(f"Exception in check_admin: {e}")
        return False

async def is_subscribed(client: Client, user_id: int):
    """Check if a user is subscribed to all required channels."""
    # Check if force-sub is globally enabled
    if not await db.get_force_sub_enabled():
        logger.debug(f"Force-sub is globally disabled for user {user_id}")
        return True

    channel_ids = await db.show_channels()

    if not channel_ids:
        logger.debug("No force-sub channels configured")
        return True

    if user_id == OWNER_ID:
        logger.debug(f"User {user_id} is owner, skipping subscription check")
        return True

    for cid in channel_ids:
        try:
            mode = await db.get_channel_mode(cid)
            if mode == "off":
                logger.debug(f"Channel {cid} is disabled for force-sub")
                continue

            if not await is_sub(client, user_id, cid):
                # Retry once if join request might be processing
                if mode == "on":
                    await asyncio.sleep(1)  # Reduced timeout
                    if await is_sub(client, user_id, cid):
                        continue
                logger.debug(f"User {user_id} not subscribed to channel {cid}")
                return False
        except Exception as e:
            logger.error(f"Error checking subscription for channel {cid}: {e}")
            continue  # Skip invalid channels

    logger.debug(f"User {user_id} is subscribed to all required channels")
    return True

async def is_sub(client: Client, user_id: int, channel_id: int):
    """Check if a user is a member of a specific channel."""
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
        logger.error(f"[!] Error in is_sub for channel {channel_id}, user {user_id}: {e}")
        return False

async def encode(string):
    try:
        string_bytes = string.encode("utf-8")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        base64_string = base64_bytes.decode("utf-8").strip("=")
        return base64_string
    except Exception as e:
        logger.error(f"Error encoding string: {e}")
        return ""

async def decode(base64_string):
    try:
        base64_string = base64_string.strip("=")
        base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("utf-8")
        string_bytes = base64.urlsafe_b64decode(base64_bytes) 
        string = string_bytes.decode("utf-8")
        return string
    except Exception as e:
        logger.error(f"Error decoding base64 string: {e}")
        return ""

async def get_messages(client: Client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temp_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=msgs_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=msgs_ids
            )
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            pass
        total_messages += len(temp_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client: Client, message):
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
    return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, remainder, 60) if remainder < 3 else divmod(seconds, 24)
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
    periods = [('days', ' 86400), ('days', hours', 3600), ('hours', mins', 60), ('mins', secs', 1)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value = seconds // period_seconds
            seconds = seconds % period_seconds
            result.append(f"{int(period_value)} {period_name}")
    return result and ", ".join(result) or "0 secs"

async def get_shortlink(client, url, api, link):
    try:
        short_link = await shorten_url(url, link, api_key=api)
        return short_link
    except Exception as e:
        logger.error(f"Error shortening link: {e}")
        return link

subscribed = filters.create(is_subscribed)
admin = filters.create(check_admin)

#
# 
