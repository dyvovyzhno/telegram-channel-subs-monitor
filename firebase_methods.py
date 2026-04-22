# firebase_methods.py

import logging

import firebase_admin
from firebase_admin import credentials, firestore
from google.api_core.retry import Retry
from google.cloud.firestore import FieldFilter, Query
from sentry_sdk import capture_exception

from bot_methods import send_message_to_channel
from config import settings

logger = logging.getLogger(__name__)

# Fail fast if Firestore is unreachable instead of hanging the whole scheduler.
# deadline bounds total wait across retries; timeout is per-attempt.
_FIRESTORE_TIMEOUT = 10.0
_FIRESTORE_RETRY = Retry(deadline=30.0)


# Initialize Firebase Admin SDK.
# Prefer a path supplied via env; fall back to the legacy file in the working dir
# so existing deployments keep running without .env changes.
_cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS or "serviceAccountKey.json"
cred = credentials.Certificate(_cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()


def setup_firebase():
    """Optional method to setup Firebase, if there are additional setup steps required."""
    pass


def store_action_to_firebase(action_data: dict):
    """Stores the provided action data to Firebase Firestore."""

    # Reference to the Firestore collection where data will be stored
    admin_actions_ref = db.collection("admin_actions")

    try:
        # Check if an action with the same hash already exists
        matching_actions = admin_actions_ref.where(
            filter=FieldFilter("hash", "==", action_data["hash"])
        ).get(timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)

        # If no matching action was found, add the new action_data
        if not matching_actions:
            # Fetch only the most recent prior action for this user — Firestore sorts and
            # limits server-side, backed by the composite (user_id asc, date desc) index.
            previous_actions = (
                admin_actions_ref.where(
                    filter=FieldFilter("user_id", "==", action_data["user_id"])
                )
                .order_by("date", direction=Query.DESCENDING)
                .limit(1)
                .get(timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)
            )

            if previous_actions:
                latest_action = previous_actions[0].to_dict() or {}
                if action_data["action"] == "Joined":
                    action_data["total_joined"] = latest_action["total_joined"] + 1
                    action_data["total_left"] = latest_action["total_left"]
                elif action_data["action"] == "Left":
                    action_data["total_joined"] = latest_action["total_joined"]
                    action_data["total_left"] = latest_action["total_left"] + 1

            admin_actions_ref.add(action_data, timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)
            logger.info("Stored action data for user %s to Firestore", action_data["user_id"])

            message = "\n".join([f"{key}: {value}" for key, value in action_data.items()])
            send_message_to_channel(settings.BOT_API, settings.CHAT_ID, message)
        else:
            logger.debug(
                "Action data with hash %s already exists; skipping", action_data["hash"]
            )

    except Exception as e:
        logger.exception("Error storing data to Firestore: %s", e)
        capture_exception(e)


def send_missing_events_to_channel(last_known_hash):
    admin_actions_ref = db.collection("admin_actions")

    # Get the date of the last_known_hash
    hash_date_doc = admin_actions_ref.where(
        filter=FieldFilter("hash", "==", last_known_hash)
    ).get(timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)

    if not hash_date_doc:
        logger.warning("Hash %s not found", last_known_hash)
        return

    hash_date = (hash_date_doc[0].to_dict() or {}).get("date")

    # Get all actions after the date of the last_known_hash
    missing_actions = (
        admin_actions_ref.where(filter=FieldFilter("date", ">", hash_date))
        .order_by("date")
        .get(timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)
    )

    for action in missing_actions:
        action_data = action.to_dict() or {}
        message = "\n".join([f"{key}: {value}" for key, value in action_data.items()])
        send_message_to_channel(settings.BOT_API, settings.CHAT_ID, message)


def get_last_hash_from_firebase():
    admin_actions_ref = db.collection("admin_actions")

    # Order by date to get the latest action and retrieve only one record
    last_action = (
        admin_actions_ref.order_by("date", direction=Query.DESCENDING)
        .limit(1)
        .get(timeout=_FIRESTORE_TIMEOUT, retry=_FIRESTORE_RETRY)
    )

    if last_action:
        return (last_action[0].to_dict() or {}).get("hash")
    return None
