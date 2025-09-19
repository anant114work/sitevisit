# crm_app/whatsapp_service.py
import logging
import requests

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://backend.api-wa.co/campaign/combirds/api/v2"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY4YTA3MzE5YjRjNTczMGMyZmVjMmQwZSIsIm5hbWUiOiJib3AiLCJhcHBOYW1lIjoiQWlTZW5zeSIsImNsaWVudElkIjoiNjhhMDczMTliNGM1NzMwYzJmZWMyZDAyIiwiYWN0aXZlUGxhbiI6IkJBU0lDX1RSSUFMIiwiaWF0IjoxNzU2Mzc1ODM1fQ.ui6ifFpMyiLl80BQamwC4gGUrTAyPX-2qWqKh-dpVMU"

def normalize_number(num: str, default_cc="91"):
    n = ''.join(ch for ch in str(num) if ch.isdigit())
    if len(n) == 10:
        return default_cc + n
    if n.startswith("0") and len(n) > 10:
        n = n.lstrip("0")
        if len(n) == 10:
            return default_cc + n
    return n

def send_whatsapp_message(mobile_numbers, requester_name="User", customer_name="Customer", visit_date="Today"):
    """Send WhatsApp message using site visit campaign with template parameters"""
    numbers = mobile_numbers if isinstance(mobile_numbers, (list, tuple)) else [mobile_numbers]
    
    results = []
    for number in numbers:
        formatted_number = normalize_number(number)
        
        payload = {
            "apiKey": API_KEY,
            "campaignName": "site1",
            "destination": formatted_number,
            "userName": requester_name,
            "templateParams": [requester_name, customer_name, visit_date],
            "source": "site-visit-system",
            "media": {},
            "buttons": [],
            "carouselCards": [],
            "location": {},
            "attributes": {},
            "paramsFallbackValue": {
                "FirstName": requester_name
            }
        }
        
        try:
            logger.info("Sending WhatsApp message to %s", formatted_number)
            r = requests.post(WHATSAPP_API_URL, json=payload, timeout=15)
            
            if r.status_code == 200:
                results.append({"ok": True, "number": formatted_number})
            else:
                results.append({"ok": False, "number": formatted_number, "error": r.text})
                
        except requests.RequestException as e:
            logger.exception("WhatsApp request exception for %s", formatted_number)
            results.append({"ok": False, "number": formatted_number, "error": str(e)})
    
    return {"ok": all(r["ok"] for r in results), "results": results}

def send_location_update_reminder(mobile_number, user_name="User"):
    """Send location update reminder using locationupdate campaign"""
    formatted_number = normalize_number(mobile_number)
    
    payload = {
        "apiKey": API_KEY,
        "campaignName": "locationupdate",
        "destination": formatted_number,
        "userName": user_name,
        "templateParams": [],
        "source": "location-reminder-system",
        "media": {},
        "buttons": [],
        "carouselCards": [],
        "location": {},
        "attributes": {},
        "paramsFallbackValue": {}
    }
    
    try:
        print(f"\n📱 SENDING LOCATION REMINDER to {user_name} ({formatted_number})")
        logger.info("Sending location update reminder to %s", formatted_number)
        r = requests.post(WHATSAPP_API_URL, json=payload, timeout=15)
        
        if r.status_code == 200:
            print(f"✅ Location reminder sent successfully")
            return {"ok": True, "number": formatted_number}
        else:
            print(f"❌ Location reminder failed: {r.text}")
            return {"ok": False, "number": formatted_number, "error": r.text}
            
    except requests.RequestException as e:
        print(f"❌ Location reminder exception: {e}")
        logger.exception("Location reminder exception for %s", formatted_number)
        return {"ok": False, "number": formatted_number, "error": str(e)}

# Backward compatibility
def send_sms_using_template(mobile_numbers, template_key, var_value=None, max_retries=2, timeout=15):
    """Backward compatibility wrapper for WhatsApp messages"""
    user_name = f"User {var_value}" if var_value else "User"
    return send_whatsapp_message(mobile_numbers, user_name)