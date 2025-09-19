# crm_app/sms_service.py
import requests
import random
import logging
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# Edumarc SMS API Configuration
SMS_API_URL = 'https://smsapi.edumarcsms.com/api/v1/sendsms'
OTP_API_KEY = 'cliyfm0jy0002xnqx4w60excg'
SENDER_ID = 'REABOP'
OTP_TEMPLATE_ID = '1607100000000223009'

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_sms(phone_number, otp_code, purpose="verification"):
    """Send OTP SMS using Edumarc API"""
    try:
        # Format phone number
        if not phone_number.startswith('91'):
            phone_number = '91' + phone_number.lstrip('0')
        
        # Prepare message using template: "Your verification code is : {#var#} Regards BOP REALTY"
        message = f"Your verification code is : {otp_code} Regards BOP REALTY"
        
        payload = {
            "number": [phone_number],
            "message": message,
            "senderId": SENDER_ID,
            "templateId": OTP_TEMPLATE_ID
        }
        
        headers = {
            'Content-Type': 'application/json',
            'apikey': OTP_API_KEY
        }
        
        print(f"\n📱 SENDING OTP SMS to {phone_number}")
        print(f"OTP Code: {otp_code}")
        print(f"Message: {message}")
        
        response = requests.post(SMS_API_URL, json=payload, headers=headers, timeout=10)
        
        print(f"SMS API Response: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            logger.info(f"OTP SMS sent successfully to {phone_number}")
            return {'success': True, 'message': 'OTP sent successfully'}
        else:
            logger.error(f"SMS API error: {response.status_code} - {response.text}")
            return {'success': False, 'error': f'SMS API error: {response.status_code}'}
            
    except Exception as e:
        logger.error(f"Error sending OTP SMS: {e}")
        print(f"❌ SMS Error: {e}")
        return {'success': False, 'error': str(e)}

def verify_otp(user_profile, entered_otp):
    """Verify OTP code and check expiry"""
    if not user_profile.otp_code:
        return {'success': False, 'error': 'No OTP found'}
    
    # Check if OTP is expired (5 minutes)
    if user_profile.otp_created_at:
        expiry_time = user_profile.otp_created_at + timedelta(minutes=5)
        if timezone.now() > expiry_time:
            return {'success': False, 'error': 'OTP expired'}
    
    # Verify OTP
    if user_profile.otp_code == entered_otp:
        # Clear OTP after successful verification
        user_profile.otp_code = None
        user_profile.otp_created_at = None
        user_profile.save()
        return {'success': True, 'message': 'OTP verified successfully'}
    else:
        return {'success': False, 'error': 'Invalid OTP'}