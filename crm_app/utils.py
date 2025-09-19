import requests
import logging
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile, Notification

logger = logging.getLogger(__name__)

def send_whatsapp(phone_numbers, message, request_id=None):
    """Send site visit notification WhatsApp using AI Timey service"""
    print(f"\n📱 TRIGGERING WHATSAPP for: {phone_numbers}")
    from .whatsapp_service import send_whatsapp_message
    user_name = f"Request {request_id}" if request_id else "User"
    result = send_whatsapp_message(phone_numbers, user_name)
    print(f"WhatsApp result: {result}")
    return result.get('ok', False)

def get_next_approver(site_visit_request):
    """Get the next approver based on hierarchy"""
    requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
    
    # Get all approved users for this request
    approved_users = set(site_visit_request.approvals.filter(action='approved').values_list('approver_id', flat=True))
    
    # Start from requester and go up the hierarchy
    current_profile = requester_profile
    
    # Find the next person in hierarchy who hasn't approved yet
    while current_profile.parent:
        parent_user = current_profile.parent.user
        if parent_user.id not in approved_users:
            return parent_user
        current_profile = current_profile.parent
    
    # If we've gone through all parents, check if we need HR approval
    # HR approval comes after all hierarchy approvals
    hr_approved = site_visit_request.approvals.filter(
        approver__userprofile__role='Admin', 
        action='approved'
    ).exists()
    
    if not hr_approved:
        hr_user = User.objects.filter(userprofile__role='Admin').first()
        if hr_user and hr_user.id not in approved_users:
            return hr_user
    
    return None

def send_notification_to_approver(site_visit_request):
    """Send notifications to all approvers and direct manager"""
    requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
    
    # Get all required approvers (hierarchy + HR)
    required_approvers = []
    current = requester_profile
    while current.parent:
        current = current.parent
        required_approvers.append(current.user)
    
    # Add HR if not already in hierarchy
    from django.contrib.auth.models import User
    hr_user = User.objects.filter(userprofile__role='Admin').first()
    if hr_user and hr_user not in required_approvers:
        required_approvers.append(hr_user)
    
    # Also add HR user with contact 8882443789
    hr_contact_user = User.objects.filter(userprofile__contact_number='8882443789').first()
    if hr_contact_user and hr_contact_user not in required_approvers:
        required_approvers.append(hr_contact_user)
    
    # Add direct manager (immediate parent) for WhatsApp notification
    direct_manager = None
    if requester_profile.parent:
        direct_manager = requester_profile.parent.user
        if direct_manager not in required_approvers:
            required_approvers.append(direct_manager)
    
    # Send notifications to all approvers and hierarchy
    all_notified = set()  # Track who we've notified to avoid duplicates
    
    for approver in required_approvers:
        if approver.id in all_notified:
            continue
            
        # Create in-app notification
        from .models import Notification
        Notification.objects.create(
            user=approver,
            message=f"New site visit request from {site_visit_request.team_member.get_full_name()} requires your approval.",
            site_visit_request=site_visit_request
        )
        
        # Send WhatsApp
        approver_profile = UserProfile.objects.get(user=approver)
        if approver_profile.contact_number:
            print(f"\n📱 SENDING WHATSAPP to {approver.get_full_name()} ({approver_profile.get_role_display()})")
            print(f"Contact: {approver_profile.contact_number}")
            
            from .whatsapp_service import send_whatsapp_message
            requester_name = site_visit_request.team_member.get_full_name() or "User"
            customer_name = getattr(site_visit_request, 'customer_broker_name', 'Customer')
            visit_date = getattr(site_visit_request, 'visit_date', 'Today')
            if hasattr(visit_date, 'strftime'):
                visit_date = visit_date.strftime('%d-%m-%Y')
            
            result = send_whatsapp_message([approver_profile.contact_number], requester_name, customer_name, str(visit_date))
            print(f"WhatsApp result: {result}")
            logger.info(f"WhatsApp sent to {approver_profile.contact_number}: {result}")
        else:
            print(f"\n⚠️ NO CONTACT NUMBER for {approver.get_full_name()}")
            
        all_notified.add(approver.id)
        
        # Send Email
        email_address = approver_profile.email or approver.email
        if email_address:
            print(f"\n📧 TRIGGERING EMAIL for approver: {approver.get_full_name()}")
            print(f"Email address: {email_address}")
            from .email_service import send_email
            subject = "New Site Visit Request - Approval Required"
            message = f"New site visit request from {site_visit_request.team_member.get_full_name()} requires your approval."
            result = send_email([email_address], subject, message, site_visit_request.id)
            print(f"Email result: {result}")
            logger.info(f"Email sent to {email_address}: {result}")
        else:
            print(f"\n⚠️ NO EMAIL ADDRESS for approver: {approver.get_full_name()}")

def can_user_view_request(user, site_visit_request):
    """Check if user can view a specific site visit request"""
    user_profile = UserProfile.objects.get(user=user)
    
    # Admin and Sales Director can view all requests
    if user_profile.role in ['Admin', 'Sales Director - T1']:
        return True
    
    # Own request
    if site_visit_request.team_member == user:
        return True
    
    # Check if user is in the hierarchy chain above the requester
    requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
    current = requester_profile
    while current.parent:
        current = current.parent
        if current.user == user:
            return True
    
    return False

def get_subordinate_requests(user_profile):
    """Get all requests from subordinates"""
    subordinate_profiles = []
    
    def collect_subordinates(profile):
        for subordinate in profile.subordinates.all():
            subordinate_profiles.append(subordinate)
            collect_subordinates(subordinate)
    
    collect_subordinates(user_profile)
    subordinate_users = [p.user for p in subordinate_profiles]
    
    from .models import SiteVisitRequest
    return SiteVisitRequest.objects.filter(team_member__in=subordinate_users)