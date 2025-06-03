import asyncio
import base64
import logging
import random
import re
import string
import time
from datetime import datetime, timedelta
from typing import List, Optional
from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from database.database import db
from config import SHORTLINK_URL, SHORTLINK_API, FSUB_LINK_EXPIRY

logger = logging.getLogger(__name__)

# Chat data cache
chat_data_cache = {}

async def is_subscribed(client: Client, user_id: int) -> bool:
    """
    Check if a user is subscribed to all required force-sub channels.
    Returns True if subscribed to all active channels or if force-sub is disabled.
    """
    try:
        force_sub_enabled: bool = await db.get_force_sub_mode()
        if not force_sub_enabled:
            return True

        channel_ids: List[int] = await db.show_channels()
        if not channel_ids:
            return True

        for channel_id in channel_ids:
            mode: str = await db.get_channel_mode(channel_id)
            if mode != "on":
                continue
            try:
                member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
                if member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
                    continue
                else:
                    return False
            except UserNotParticipant:
                return False
            except ChatAdminRequired:
                logger.error(f"Bot is not an admin in channel {channel_id}")
                await db.rem_channel(channel_id)
                continue
            except Exception as e:
                logger.error(f"Error checking subscription for user {user_id} in channel {channel_id}: {e}")
                continue
        return True
    except Exception as e:
        logger.error(f"Error in is_subscribed for user {user_id}: {e}")
        return False

async def is_sub(client: Client, user_id: int, channel_id: int) -> bool:
    """
    Check if a user is subscribed to a specific channel.
    """
    try:
        member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id} in channel {channel_id}: {e}")
        return False

async def get_messages(client: Client, message_ids: List[int]):
    messages = []
    for message_id in message_ids:
        try:
            message = await client.get_messages(chat_id=client.db_channel.id, message_ids=message_id)
            if message:
                messages.append(message)
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            continue
    return messages

def get_readable_time(seconds: int) -> str:
    periods = [('year', 31536000), ('month', 2592000), ('day', 86400), ('hour', 3600), ('minute', 60), ('second', 1)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)} {period_name}{'s' if period_value != 1 else ''}")
    return ', '.join(result) if result else '0 seconds'

async def get_shortlink(url: str, api: str, link: str) -> str:
    """
    Generate a short link using the provided shortener API.
    """
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/api?api={api}&url={link}") as response:
                data = await response.json()
                if data.get("status") == "success":
                    return data.get("shortenedUrl")
                else:
                    logger.error(f"Shortlink API error: {data.get('message')}")
                    return link
    except Exception as e:
        logger.error(f"Error generating shortlink: {e}")
        return link

def get_exp_time(seconds: int) -> str:
    periods = [('Year', 31536000), ('Month', 2592000), ('Day', 86400), ('Hour', 3600), ('Minute', 60)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)} {period_name}{'s' if period_value != 1 else ''}")
            break
    return ' '.join(result) if result else f"{seconds} Seconds"

async def decode(base64_string: str) -> str:
    try:
        decoded_bytes = base64.b64decode(base64_string + "=" * (-len(base64_string) % 4))
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decoding base64 string: {e}")
        raise

def encode(string: str) -> str:
    try:
        encoded_bytes = base64.b64encode(string.encode('utf-8')).decode('utf-8')
        return encoded_bytes.rstrip("=")
    except Exception as e:
        logger.error(f"Error encoding string: {e}")
        raise
