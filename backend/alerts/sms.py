import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TO_PHONE_NUMBER = os.getenv("TO_PHONE_NUMBER")

def send_fire_sms(confidence, timestamp, location="Main Station"):
    """
    Sends an SMS alert via Twilio when fire/smoke is detected.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TO_PHONE_NUMBER]):
        print("⚠️ Twilio credentials missing. Skipping SMS alert.")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_body = (
            f"🚨 WILDFIRE ALERT 🚨\n"
            f"Fire detected at {location}\n"
            f"Confidence: {confidence:.2f}\n"
            f"Time: {timestamp}\n"
            f"Please take immediate action!"
        )

        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=TO_PHONE_NUMBER
        )
        print(f"✅ SMS Alert sent! SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
        return False
