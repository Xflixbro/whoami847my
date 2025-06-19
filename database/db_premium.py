#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import motor.motor_asyncio
from config import DB_URI, DB_NAME
from pytz import timezone
from datetime import datetime, timedelta

# Create an async client with Motor
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
collection = database['premium-users']

# ✅ FIXED: Check if the user is a premium user and the plan is still valid
async def is_premium_user(user_id):
    user = await collection.find_one({"user_id": user_id})
    if not user:
        return False

    expiration_timestamp = user.get("expiration_timestamp")
    if not expiration_timestamp:
        return False

    try:
        ist = timezone("Asia/Dhaka")
        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
        return expiration_time > datetime.now(ist)
    except Exception as e:
        print(f"[ERROR] Expiry check failed for user {user_id}: {e}")
        return False

# Remove premium user
async def remove_premium(user_id):
    await collection.delete_one({"user_id": user_id})

# Remove expired users
async def remove_expired_users():
    ist = timezone("Asia/Dhaka")
    current_time = datetime.now(ist)

    async for user in collection.find({}):
        expiration = user.get("expiration_timestamp")
        if not expiration:
            continue

        try:
            expiration_time = datetime.fromisoformat(expiration).astimezone(ist)
            if expiration_time <= current_time:
                await collection.delete_one({"user_id": user["user_id"]})
        except Exception as e:
            print(f"Error removing user {user.get('user_id')}: {e}")

# List active premium users
async def list_premium_users():
    ist = timezone("Asia/Dhaka")
    premium_users = collection.find({})
    premium_user_list = []

    async for user in premium_users:
        user_id = user["user_id"]
        expiration_timestamp = user["expiration_timestamp"]
        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(ist)
        remaining_time = expiration_time - datetime.now(ist)

        if remaining_time.total_seconds() > 0:
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            expiry_info = f"{days}d {hours}h {minutes}m {seconds}s left"
            formatted_expiry_time = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')
            premium_user_list.append(f"UserID: {user_id} - Expiry: {expiry_info} (Expires at {formatted_expiry_time})")

    return premium_user_list

# Add premium user
async def add_premium(user_id, time_value, time_unit):
    time_unit = time_unit.lower()
    ist = timezone("Asia/Dhaka")
    now = datetime.now(ist)

    if time_unit == 's':
        expiration_time = now + timedelta(seconds=time_value)
    elif time_unit == 'm':
        expiration_time = now + timedelta(minutes=time_value)
    elif time_unit == 'h':
        expiration_time = now + timedelta(hours=time_value)
    elif time_unit == 'd':
        expiration_time = now + timedelta(days=time_value)
    elif time_unit == 'y':
        expiration_time = now + timedelta(days=365 * time_value)
    else:
        raise ValueError("Invalid time unit. Use 's', 'm', 'h', 'd', or 'y'.")

    premium_data = {
        "user_id": user_id,
        "expiration_timestamp": expiration_time.isoformat(),
    }

    await collection.update_one(
        {"user_id": user_id},
        {"$set": premium_data},
        upsert=True
    )

    formatted_expiration = expiration_time.strftime('%Y-%m-%d %H:%M:%S %p IST')
    return formatted_expiration

# Check if a user has an active premium plan (for /myplan)
async def check_user_plan(user_id):
    user = await collection.find_one({"user_id": user_id})
    if user:
        expiration_timestamp = user["expiration_timestamp"]
        expiration_time = datetime.fromisoformat(expiration_timestamp).astimezone(timezone("Asia/Dhaka"))
        remaining_time = expiration_time - datetime.now(timezone("Asia/Dhaka"))

        if remaining_time.total_seconds() > 0:
            days, hours, minutes, seconds = (
                remaining_time.days,
                remaining_time.seconds // 3600,
                (remaining_time.seconds // 60) % 60,
                remaining_time.seconds % 60,
            )
            return f"Your premium plan is active. {days}d {hours}h {minutes}m {seconds}s left."
        else:
            return "Your premium plan has expired."
    else:
        return "You do not have a premium plan."
