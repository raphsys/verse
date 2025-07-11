# app/utils/sms_sender.py

from twilio.rest import Client

def send_sms(to_number: str, body: str):
    ACCOUNT_SID = "TON_ACCOUNT_SID"
    AUTH_TOKEN = "TON_AUTH_TOKEN"
    FROM_NUMBER = "+123456789"  # Ton numéro Twilio

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    message = client.messages.create(
        body=body,
        from_=FROM_NUMBER,
        to=to_number
    )

