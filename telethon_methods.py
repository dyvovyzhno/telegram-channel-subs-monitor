# telethon_methods.py

import asyncio
import re

import sentry_sdk
from decouple import config
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetAdminLogRequest, GetFullChannelRequest
from telethon.tl.types import (
    Channel,
    ChannelAdminLogEventActionParticipantJoin,
    ChannelAdminLogEventActionParticipantLeave,
    InputChannel,
)

from models.admin_action import AdminAction

API_ID = config("API_ID", default="", cast=int)
if not API_ID:
    raise ValueError("API_ID is not set!")
API_HASH = str(config("API_HASH", default=""))
if not API_HASH:
    raise ValueError("API_HASH is not set!")
PHONE_NUMBER = str(config("PHONE_NUMBER", default=""))
if not PHONE_NUMBER:
    raise ValueError("PHONE_NUMBER is not set!")
CHANNEL_ID_TO_MONITOR = config("CHANNEL_ID_TO_MONITOR", default="")
if not CHANNEL_ID_TO_MONITOR:
    raise ValueError("CHANNEL_ID_TO_MONITOR is not set!")


async def setup_telethon():
    try:
        client = TelegramClient("anon", API_ID, API_HASH)

        if not client.is_connected():
            await client.connect()

        if not await client.is_user_authorized():
            await client.send_code_request(PHONE_NUMBER)
            # Blocking input is acceptable here: auth only happens once, before the
            # scheduler loop starts — no concurrent tasks on the loop to stall.
            verification_code = input("Enter the code: ")  # noqa: ASYNC250
            try:
                await client.sign_in(PHONE_NUMBER, verification_code)
            except SessionPasswordNeededError:
                two_step_verif_password = input(  # noqa: ASYNC250
                    "Two-step verification is enabled. Please enter your password: "
                )
                await client.sign_in(password=two_step_verif_password)

        return client

    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise


async def get_admin_actions(client):
    # Get channel entity to fetch the InputChannel later
    channel = await client.get_entity(CHANNEL_ID_TO_MONITOR)
    if not isinstance(channel, Channel):
        print("The provided ID does not belong to a channel!")
        return []

    if channel.access_hash is None:
        print("Error: Channel access hash is None!")
        return []

    # Get total channel members count
    input_channel = InputChannel(channel.id, channel.access_hash)
    full_channel = await client(GetFullChannelRequest(input_channel))
    total_channel_members = full_channel.full_chat.participants_count

    # Get admin actions
    result = await client(
        GetAdminLogRequest(
            channel=InputChannel(channel.id, channel.access_hash),
            q="",  # Empty means get all actions
            max_id=0,
            min_id=0,
            limit=100,  # Adjust as needed
        )
    )

    # Convert actions to a format suitable for Firebase storage
    actions_data = []
    for entry in result.events:
        await asyncio.sleep(2)
        user = await client.get_entity(entry.user_id)
        user_username = "@" + user.username if user.username else ""
        user_firstname = user.first_name if user.first_name else ""
        user_lastname = user.last_name if user.last_name else ""
        user_phone = getattr(user, "phone", "") or ""

        # Determine the action - Joined or Left
        if isinstance(entry.action, ChannelAdminLogEventActionParticipantJoin):
            # if str(entry.action) == 'ChannelAdminLogEventActionParticipantJoin()':
            action_str = "Joined"
        elif isinstance(entry.action, ChannelAdminLogEventActionParticipantLeave):
            # elif str(entry.action) == 'ChannelAdminLogEventActionParticipantLeave()':
            action_str = "Left"
        else:
            action_str = str(entry.action)  # Fallback, should not reach here for your scenario

        action = AdminAction(
            action_str,
            entry.date.strftime("%Y-%m-%d %H:%M:%S"),
            entry.user_id,
            user_username,
            user_firstname,
            user_lastname,
            total_channel_members,
            0,  # total_joined placeholder
            0,  # total_left placeholder
            user_phone,
        )
        actions_data.append(action)

    return actions_data


async def get_last_message_hash(client, channel_id):
    await asyncio.sleep(2)
    try:
        # get chat entity
        entity = await client.get_entity(channel_id)

        # Fetching the last 10 messages
        await asyncio.sleep(2)
        messages = await client.get_messages(entity, limit=10)

        # message could be accessed by message[0].message

        # If there are no messages, return None
        if not messages:
            return None

        # find first message with hash
        hash_match = None
        for message in messages:
            hash_match = re.search(r"([a-fA-F0-9]{64})", message.message or "")
            if hash_match:
                break

        # If a hash is found, return it, otherwise return None
        if hash_match:
            return hash_match.group(1)
        else:
            return None

    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None
