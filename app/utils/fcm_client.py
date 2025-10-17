import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK once
try:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase Admin SDK initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")


def send_push_notification(device_token: str, title: str, body: str, data: dict = None):
    """Sends a push notification to a single device token."""
    if not firebase_admin._apps:
        logger.error("Firebase Admin SDK is not initialized.")
        return None

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},  # Custom data payload for handling in the client app
        token=device_token,
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending message to token {device_token}: {e}")
        return None


def send_multicast_notification(device_tokens: list, title: str, body: str, data: dict = None):
    """Sends a push notification to multiple device tokens."""
    if not firebase_admin._apps:
        logger.error("Firebase Admin SDK is not initialized.")
        return None

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=device_tokens,
    )

    try:
        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent multicast message. Success: {response.success_count}, Failure: {response.failure_count}")
        return response
    except Exception as e:
        logger.error(f"Error sending multicast message: {e}")
        return None