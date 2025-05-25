#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

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
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Used for checking if a user is admin ~Owner also treated as admin level
async def check_admin(filter, client, update):
    try:
        user_id = update.from_user.id
        is_owner = user_id == OWNER_ID
        is_admin = await db.admin_exist(user_id)
        logger.info(f"Checking admin status for user {user_id}: is_owner={is_owner}, is_admin={is_admin}")
        return is_owner or is_admin
    except Exception as e:
        logger.error(f"Exception in check_admin: {e}")
        return False

async def is_subscribed(client, user_id):
    channel_ids = await db.show_channels()

    if not channel_ids:
        logger.info(f"No channels found for subscription check for user {user_id}")
        return True

    if user_id == OWNER_ID:
        logger.info(f"User {user_id} is OWNER, bypassing subscription check")
        return True

    for cid in channel_ids:
        if not await is_sub(client, user_id, cid):
            # Retry once if join request might be processing
            mode = await db.get_channel_mode(cid)
            if mode == "on":
                await asyncio.sleep(2)  # give time for @on_chat_join_request to process
                if await is_sub(client, user_id, cid):
                    continue
            logger.info(f"User {user_id} is not subscribed to channel {cid}")
            return False

    logger.info(f"User {user_id} is subscribed to all required channels")
    return True

async def is_sub(client, user_id, channel_id):
    try:
        member = await client.get_chat_member(channel_id, user_id)
        status = member.status
        logger.info(f"User {user_id} in channel {channel_id} with status {status}")
        return status in {
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.MEMBER
        }

    except UserNotParticipant:
        mode = await db.get_channel_mode(channel_id)
        if mode == "on":
            exists = await db.req_user_exist(channel_id, user_id)
            logger.info(f"User {user_id} join request for channel {channel_id}: {exists}")
            return exists
        logger.info(f"User {user_id} not in channel {channel_id} and mode != on")
        return False

    except Exception as e:
        logger.error(f"Error in is_sub(): {e}")
        return False

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")  # Handle links generated before padding fix
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temp_ids = message_ids[total_messages:total_messages + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temp_ids
            )
        except FloodWait as e:
            logger.warning(f"FloodWait in get_messages: waiting for {e.value} seconds")
            await asyncio.sleep(e.value)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temp_ids
            )
        except Exception as e:
            logger.error(f"Error in get_messages: {e}")
            pass
        total_messages += len(temp_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    try:
        if message.forward_from_chat:
            if message.forward_from_chat.id == client.db_channel.id:
                logger.info(f"Message forwarded from db channel, ID: {message.forward_from_message_id}")
                return message.forward_from_message_id
            else:
                logger.warning(f"Message forwarded from different channel: {message.forward_from_chat.id}")
                return 0
        elif message.forward_sender_name:
            logger.warning("Message forwarded from hidden sender")
            return 0
        elif message.text:
            # Updated regex to handle various Telegram link formats
            pattern = r"https://t\.me/(?:c/)?(?:@)?([a-zA-Z0-9_]+|-?\d+)/(\d+)"
            matches = re.match(pattern, message.text.strip())
            if not matches:
                logger.warning(f"Invalid link format: {message.text}")
                return 0
            channel_identifier, msg_id = matches.groups()
            msg_id = int(msg_id)
            # Check if the channel identifier is a username or ID
            if channel_identifier.startswith('-') or channel_identifier.isdigit():
                # It's a channel ID
                expected_channel_id = str(client.db_channel.id)
                if channel_identifier.startswith('-'):
                    channel_id = channel_identifier
                else:
                    channel_id = f"-100{channel_identifier}"
                if channel_id == expected_channel_id:
                    logger.info(f"Valid channel ID link: {channel_id}, Message ID: {msg_id}")
                    return msg_id
                else:
                    logger.warning(f"Link channel ID {channel_id} does not match db channel {expected_channel_id}")
                    return 0
            else:
                # It's a username
                channel_username = f"@{channel_identifier}" if not channel_identifier.startswith('@') else channel_identifier
                if channel_username.lower() == client.db_channel.username.lower():
                    logger.info(f"Valid channel username link: {channel_username}, Message ID: {msg_id}")
                    return msg_id
                else:
                    logger.warning(f"Link username {channel_username} does not match db channel {client.db_channel.username}")
                    return 0
        else:
            logger.warning("Message does not contain valid forward or link")
            return 0
    except Exception as e:
        logger.error(f"Error in get_message_id: {e}")
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
    try:
        shortzy = Shortzy(api_key=api, base_site=url)
        short_link = await shortzy.convert(link)
        logger.info(f"Generated short link: {short_link}")
        return short_link
    except Exception as e:
        logger.error(f"Error in get_shortlink: {e}")
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
