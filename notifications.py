import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms_notification(to_phone, message):
    """
    Send SMS notification using Twilio
    
    Args:
        to_phone (str): Recipient's phone number
        message (str): Message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logging.warning("Twilio credentials not configured. SMS not sent.")
        return False
        
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send message
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logging.info(f"SMS sent to {to_phone}: {message.sid}")
        return True
    except TwilioRestException as e:
        logging.error(f"Twilio error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Error sending SMS: {str(e)}")
        return False

def send_queue_confirmation(name, business_name, position, phone):
    """
    Send queue confirmation message
    
    Args:
        name (str): Customer name
        business_name (str): Business name
        position (int): Position in queue
        phone (str): Phone number
        
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"Hi {name}, you've been added to the queue at {business_name}. You are number {position} in line. We'll notify you as your turn approaches."
    return send_sms_notification(phone, message)

def send_queue_update(name, business_name, position, phone):
    """
    Send queue position update
    
    Args:
        name (str): Customer name
        business_name (str): Business name
        position (int): New position in queue
        phone (str): Phone number
        
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"Hi {name}, your position at {business_name} has been updated. You are now number {position} in line."
    return send_sms_notification(phone, message)

def send_turn_notification(name, business_name, phone):
    """
    Send notification when it's the customer's turn
    
    Args:
        name (str): Customer name
        business_name (str): Business name
        phone (str): Phone number
        
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"Hi {name}, it's your turn at {business_name}! Please proceed to the counter/desk."
    return send_sms_notification(phone, message)