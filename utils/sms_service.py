"""
SMS Notification Service for FoodBridge
Sends SMS notifications for various status updates in the food donation process.

This module provides a simple SMS sending functionality.
In production, replace with actual Twilio or other SMS API integration.
"""
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SMS configuration - set these environment variables for production
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# SMS Templates
SMS_TEMPLATES = {
    'request_sent': "FoodBridge: {donor_name} has requested food pickup from {ngo_name}. Track at: {tracking_link}",
    'ngo_accepted': "FoodBridge: Good news! {ngo_name} has accepted your donation request. A volunteer will collect soon. Track at: {tracking_link}",
    'volunteer_assigned': "FoodBridge: Volunteer {volunteer_name} has been assigned to collect food from {donor_name}. Track at: {tracking_link}",
    'food_collected': "FoodBridge: Food has been collected from {donor_name} and is on the way to {ngo_name}. Track at: {tracking_link}",
    'food_near_ngo': "FoodBridge: Food from {donor_name} is near {ngo_name}. Please be ready to receive. Track at: {tracking_link}",
    'donation_completed': "FoodBridge: Donation from {donor_name} has been successfully delivered to {ngo_name}. Thank you for your contribution!",
    'donor_welcome': "Welcome to FoodBridge, {donor_name}! You're now registered as a food donor. Start donating at: {app_link}",
    'ngo_welcome': "Welcome to FoodBridge, {ngo_name}! You're now registered as an NGO. View donation requests at: {app_link}",
}


def send_sms(phone_number, message):
    """
    Send an SMS to the specified phone number.
    
    In production, this would use Twilio or another SMS API.
    For now, it logs the message for testing purposes.
    
    Args:
        phone_number: The recipient's phone number (with country code)
        message: The SMS message content
        
    Returns:
        dict: Result of the SMS send operation
    """
    # Normalize phone number
    phone_number = str(phone_number).strip()
    if not phone_number.startswith('+'):
        # Assume Indian number if no country code
        phone_number = '+91' + phone_number.lstrip('0')
    
    # Log the SMS for debugging/testing
    logger.info(f"[SMS] To: {phone_number}")
    logger.info(f"[SMS] Message: {message}")
    
    # Check if Twilio credentials are configured
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            
            sms = client.messages.create(
                body=message,
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"[SMS] Sent successfully: SID={sms.sid}")
            return {
                'success': True,
                'sid': sms.sid,
                'status': sms.status
            }
        except Exception as e:
            logger.error(f"[SMS] Failed to send: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    else:
        # No Twilio configured - just log and return success for testing
        logger.info("[SMS] Twilio not configured - message logged only")
        return {
            'success': True,
            'status': 'logged',
            'message': 'SMS logged (Twilio not configured)'
        }


def send_notification(event_type, phone_number, **kwargs):
    """
    Send a templated notification SMS.
    
    Args:
        event_type: Type of notification (e.g., 'request_sent', 'ngo_accepted')
        phone_number: Recipient's phone number
        **kwargs: Variables to fill in the template
        
    Returns:
        dict: Result of the SMS send operation
    """
    template = SMS_TEMPLATES.get(event_type)
    if not template:
        logger.error(f"[SMS] Unknown event type: {event_type}")
        return {'success': False, 'error': f'Unknown event type: {event_type}'}
    
    # Add default tracking link if not provided
    if 'tracking_link' not in kwargs:
        kwargs['tracking_link'] = 'https://foodbridge.app/track'
    if 'app_link' not in kwargs:
        kwargs['app_link'] = 'https://foodbridge.app'
    
    try:
        message = template.format(**kwargs)
    except KeyError as e:
        logger.error(f"[SMS] Missing template variable: {e}")
        return {'success': False, 'error': f'Missing template variable: {e}'}
    
    return send_sms(phone_number, message)


def notify_request_sent(donor_phone, donor_name, ngo_name, tracking_link=None):
    """Notify donor that their request has been sent to NGO."""
    return send_notification(
        'request_sent',
        donor_phone,
        donor_name=donor_name,
        ngo_name=ngo_name,
        tracking_link=tracking_link
    )


def notify_ngo_accepted(donor_phone, ngo_name, tracking_link=None):
    """Notify donor that NGO has accepted their donation."""
    return send_notification(
        'ngo_accepted',
        donor_phone,
        ngo_name=ngo_name,
        tracking_link=tracking_link
    )


def notify_volunteer_assigned(donor_phone, ngo_phone, volunteer_name, donor_name, tracking_link=None):
    """Notify both donor and NGO that a volunteer has been assigned."""
    results = []
    
    if donor_phone:
        results.append(send_notification(
            'volunteer_assigned',
            donor_phone,
            volunteer_name=volunteer_name,
            donor_name=donor_name,
            tracking_link=tracking_link
        ))
    
    if ngo_phone:
        results.append(send_notification(
            'volunteer_assigned',
            ngo_phone,
            volunteer_name=volunteer_name,
            donor_name=donor_name,
            tracking_link=tracking_link
        ))
    
    return results


def notify_food_collected(donor_phone, ngo_phone, donor_name, ngo_name, tracking_link=None):
    """Notify that food has been collected by volunteer."""
    results = []
    
    if donor_phone:
        results.append(send_notification(
            'food_collected',
            donor_phone,
            donor_name=donor_name,
            ngo_name=ngo_name,
            tracking_link=tracking_link
        ))
    
    if ngo_phone:
        results.append(send_notification(
            'food_collected',
            ngo_phone,
            donor_name=donor_name,
            ngo_name=ngo_name,
            tracking_link=tracking_link
        ))
    
    return results


def notify_food_near_ngo(ngo_phone, donor_name, ngo_name, tracking_link=None):
    """Notify NGO that food is approaching."""
    return send_notification(
        'food_near_ngo',
        ngo_phone,
        donor_name=donor_name,
        ngo_name=ngo_name,
        tracking_link=tracking_link
    )


def notify_donation_completed(donor_phone, ngo_phone, donor_name, ngo_name):
    """Notify both parties that donation is complete."""
    results = []
    
    if donor_phone:
        results.append(send_notification(
            'donation_completed',
            donor_phone,
            donor_name=donor_name,
            ngo_name=ngo_name
        ))
    
    if ngo_phone:
        results.append(send_notification(
            'donation_completed',
            ngo_phone,
            donor_name=donor_name,
            ngo_name=ngo_name
        ))
    
    return results


def notify_donor_welcome(donor_phone, donor_name, app_link=None):
    """Send welcome SMS to newly registered donor."""
    return send_notification(
        'donor_welcome',
        donor_phone,
        donor_name=donor_name,
        app_link=app_link
    )


def notify_ngo_welcome(ngo_phone, ngo_name, app_link=None):
    """Send welcome SMS to newly registered NGO."""
    return send_notification(
        'ngo_welcome',
        ngo_phone,
        ngo_name=ngo_name,
        app_link=app_link
    )
