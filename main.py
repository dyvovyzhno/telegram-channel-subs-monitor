# main.py

import asyncio
import logging

import sentry_sdk

from config import settings
from firebase_methods import (
    get_last_hash_from_firebase,
    send_missing_events_to_channel,
    store_action_to_firebase,
)
from logging_config import setup_logging
from telethon_methods import get_admin_actions, get_last_message_hash, setup_telethon

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize Sentry at the top
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,  # Adjust this rate as per your needs
)

client = None


async def job():
    try:
        global client

        logger.info("Fetching new admin actions")

        # Ensure client is properly set up
        if client is None:
            client = await setup_telethon()
            if not client:
                logger.error("Error setting up the client")
                return
            logger.info("Telethon client set up successfully")

        # Get the latest hash from the Telegram channel
        last_message_hash = await get_last_message_hash(client, settings.CHAT_URL)

        # Get the latest hash from Firebase
        last_firestore_hash = get_last_hash_from_firebase()

        # Compare the two hashes
        if last_message_hash != last_firestore_hash:
            # Fetch and send missing events to the channel
            await asyncio.sleep(2)
            send_missing_events_to_channel(last_message_hash)
        else:
            # Logic for fetching and storing admin actions
            actions = await get_admin_actions(client)
            for action in actions:
                store_action_to_firebase(action.to_dict())
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception("Error in job: %s", e)


async def wait_for_five_minutes():
    await asyncio.sleep(300)  # Sleep for 300 seconds (5 minutes)


async def scheduler():
    while True:
        await job()
        await wait_for_five_minutes()


if __name__ == "__main__":
    asyncio.run(scheduler())
