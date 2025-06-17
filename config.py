import os
from dotenv import load_dotenv
load_dotenv()

MPESA_CREDENTIALS = {
    "key": os.getenv("MPESA_CONSUMER_KEY"),
    "secret": os.getenv("MPESA_CONSUMER_SECRET"),
    "shortcode": os.getenv("MPESA_SHORTCODE"),
    "passkey": os.getenv("MPESA_PASSKEY"),
    "callback_url": os.getenv("MPESA_CALLBACK_URL"),
}
