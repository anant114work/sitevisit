# crm_app/tasks.py
import time
import threading
from datetime import datetime, timedelta
from .models import SiteVisitRequest, UserProfile
from .whatsapp_service import send_location_update_reminder
import logging

logger = logging.getLogger(__name__)

def schedule_location_reminder(site_visit_request_id):
    """Schedule location update reminder after 60 minutes"""
    def send_reminder():
        # Wait 60 minutes (3600 seconds)
        time.sleep(3600)
        
        try:
            # Get the site visit request
            site_visit_request = SiteVisitRequest.objects.get(id=site_visit_request_id)
            requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
            
            # Only send if request is still pending
            if site_visit_request.status == 'pending' and requester_profile.contact_number:
                print(f"\n⏰ SENDING 60-MINUTE LOCATION REMINDER")
                print(f"Request ID: {site_visit_request_id}")
                print(f"Requester: {site_visit_request.team_member.get_full_name()}")
                
                result = send_location_update_reminder(
                    requester_profile.contact_number,
                    site_visit_request.team_member.get_full_name()
                )
                
                logger.info(f"Location reminder sent for request {site_visit_request_id}: {result}")
            else:
                print(f"⏭️ Skipping reminder - Request {site_visit_request_id} no longer pending or no contact")
                
        except SiteVisitRequest.DoesNotExist:
            logger.error(f"Site visit request {site_visit_request_id} not found for reminder")
        except Exception as e:
            logger.error(f"Error sending location reminder for request {site_visit_request_id}: {e}")
    
    # Start reminder thread
    reminder_thread = threading.Thread(target=send_reminder)
    reminder_thread.daemon = True
    reminder_thread.start()
    
    print(f"📅 Location reminder scheduled for request {site_visit_request_id} (60 minutes)")