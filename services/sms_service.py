"""
SMS Notification Service for FoodBridge
Sends notifications via SMS to food donors, NGOs, and volunteers during status updates.
Uses a dummy implementation that logs SMS (can be replaced with Twilio or other SMS gateway).
"""

import logging
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flag to enable/disable actual SMS sending (set to False for dummy mode)
SMS_ENABLED = False

# Twilio configuration (optional - uncomment and configure if using Twilio)
# TWILIO_ACCOUNT_SID = 'your_account_sid'
# TWILIO_AUTH_TOKEN = 'your_auth_token'
# TWILIO_PHONE_NUMBER = '+1234567890'


class SMSNotificationService:
    """
    SMS notification service that can send messages to users.
    Currently uses a dummy implementation that logs messages.
    Can be extended to use Twilio or other SMS gateways.
    """
    
    def __init__(self):
        self.sms_log = []
        
    def send_sms(self, phone_number: str, message: str) -> dict:
        """
        Send an SMS message to the specified phone number.
        
        Args:
            phone_number: The recipient's phone number
            message: The message to send
            
        Returns:
            dict with success status and details
        """
        if not phone_number:
            return {'success': False, 'error': 'No phone number provided'}
        
        # Format phone number
        formatted_phone = self._format_phone(phone_number)
        
        # Log the SMS (dummy mode)
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'phone': formatted_phone,
            'message': message,
            'status': 'sent (dummy)'
        }
        self.sms_log.append(log_entry)
        
        logger.info(f"[SMS] To: {formatted_phone} | Message: {message}")
        
        if SMS_ENABLED:
            # If SMS is enabled, attempt to send via Twilio
            try:
                return self._send_via_twilio(formatted_phone, message)
            except Exception as e:
                logger.error(f"[SMS ERROR] Failed to send via Twilio: {e}")
                return {'success': False, 'error': str(e)}
        
        return {'success': True, 'message': 'SMS logged (dummy mode)', 'log': log_entry}
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number for SMS sending."""
        # Remove any non-digit characters except +
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Add country code if not present (default to India +91)
        if not phone.startswith('+'):
            if len(phone) == 10:
                phone = '+91' + phone
            elif len(phone) == 11 and phone.startswith('0'):
                phone = '+91' + phone[1:]
        
        return phone
    
    def _send_via_twilio(self, phone_number: str, message: str) -> dict:
        """
        Send SMS via Twilio (requires twilio package and configuration).
        Uncomment and configure for production use.
        """
        # Dummy implementation - replace with actual Twilio code
        # from twilio.rest import Client
        # client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=message,
        #     from_=TWILIO_PHONE_NUMBER,
        #     to=phone_number
        # )
        # return {'success': True, 'sid': message.sid}
        
        return {'success': True, 'message': 'Twilio SMS sent (placeholder)'}
    
    def get_log(self) -> list:
        """Get the SMS log for debugging."""
        return self.sms_log
    
    # Notification templates for different events
    
    def notify_food_request_sent(self, donor_phone: str, donor_name: str, ngo_name: str) -> dict:
        """Notify food donor that their request has been sent to an NGO."""
        message = f"Hi {donor_name}! Your food donation request has been sent to {ngo_name}. You'll be notified when they accept. - FoodBridge"
        return self.send_sms(donor_phone, message)
    
    def notify_ngo_new_request(self, ngo_phone: str, ngo_name: str, donor_name: str, food_type: str) -> dict:
        """Notify NGO about a new donation request."""
        message = f"Hi {ngo_name}! New donation request from {donor_name} ({food_type}). Login to FoodBridge to accept. - FoodBridge"
        return self.send_sms(ngo_phone, message)
    
    def notify_ngo_accepted(self, donor_phone: str, donor_name: str, ngo_name: str) -> dict:
        """Notify food donor that NGO has accepted their request."""
        message = f"Good news {donor_name}! {ngo_name} has accepted your donation. Please pack the food and mark it ready. - FoodBridge"
        return self.send_sms(donor_phone, message)
    
    def notify_volunteer_assigned(self, donor_phone: str, ngo_phone: str, volunteer_name: str) -> dict:
        """Notify both parties about volunteer assignment."""
        message = f"Volunteer {volunteer_name} has been assigned for pickup. They'll collect the food shortly. - FoodBridge"
        result1 = self.send_sms(donor_phone, message)
        result2 = self.send_sms(ngo_phone, message)
        return {'donor_sms': result1, 'ngo_sms': result2}
    
    def notify_food_collected(self, donor_phone: str, ngo_phone: str, volunteer_name: str) -> dict:
        """Notify both parties when food is collected by volunteer."""
        donor_message = f"Your food donation has been collected by {volunteer_name}. It's on its way to the NGO. - FoodBridge"
        ngo_message = f"Food is on its way! {volunteer_name} has collected the donation and will deliver soon. - FoodBridge"
        result1 = self.send_sms(donor_phone, donor_message)
        result2 = self.send_sms(ngo_phone, ngo_message)
        return {'donor_sms': result1, 'ngo_sms': result2}
    
    def notify_reached_ngo(self, donor_phone: str, ngo_phone: str, ngo_name: str) -> dict:
        """Notify when food has reached the NGO."""
        donor_message = f"Great news! Your food donation has reached {ngo_name}. Thank you for your contribution! - FoodBridge"
        ngo_message = f"Food delivery has arrived! Please receive and mark as done when complete. - FoodBridge"
        result1 = self.send_sms(donor_phone, donor_message)
        result2 = self.send_sms(ngo_phone, ngo_message)
        return {'donor_sms': result1, 'ngo_sms': result2}
    
    def notify_donation_complete(self, donor_phone: str, donor_name: str, ngo_name: str) -> dict:
        """Notify food donor when donation is marked as complete by NGO."""
        message = f"Thank you {donor_name}! Your donation to {ngo_name} has been completed. Your generosity helps feed those in need! - FoodBridge"
        return self.send_sms(donor_phone, message)


# Singleton instance
sms_service = SMSNotificationService()


def get_sms_service() -> SMSNotificationService:
    """Get the SMS service singleton instance."""
    return sms_service
