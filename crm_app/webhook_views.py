# crm_app/webhook_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .models import LocationResponse, SiteVisitRequest, UserProfile, User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """Handle WhatsApp webhook responses for location tracking"""
    try:
        print(f"\n📱 WHATSAPP WEBHOOK RECEIVED")
        data = json.loads(request.body)
        print(f"Webhook data: {data}")
        
        # Extract phone number and message details
        phone_number = data.get('from', '').replace('+', '')
        message_type = data.get('type', '')
        
        print(f"Phone: {phone_number}, Type: {message_type}")
        
        # Find user by phone number
        try:
            user_profile = UserProfile.objects.get(contact_number__endswith=phone_number[-10:])
            user = user_profile.user
            print(f"Found user: {user.get_full_name()}")
        except UserProfile.DoesNotExist:
            print(f"User not found for phone: {phone_number}")
            return JsonResponse({'status': 'user_not_found'})
        
        # Find the most recent pending site visit request for this user
        site_visit_request = SiteVisitRequest.objects.filter(
            team_member=user,
            status='pending'
        ).order_by('-created_at').first()
        
        if not site_visit_request:
            print(f"No pending site visit request found for user: {user.get_full_name()}")
            return JsonResponse({'status': 'no_pending_request'})
        
        print(f"Found site visit request: {site_visit_request.id}")
        
        # Process different message types
        location_response = LocationResponse(
            site_visit_request=site_visit_request,
            user=user,
            phone_number=phone_number
        )
        
        if message_type == 'location':
            # Handle location message
            location_data = data.get('location', {})
            location_response.response_type = 'location'
            location_response.latitude = location_data.get('latitude')
            location_response.longitude = location_data.get('longitude')
            location_response.address = location_data.get('address', '')
            print(f"Location received: {location_response.latitude}, {location_response.longitude}")
            
        elif message_type == 'text':
            # Handle text message
            text_data = data.get('text', {})
            location_response.response_type = 'text'
            location_response.message_content = text_data.get('body', '')
            print(f"Text received: {location_response.message_content}")
            
        else:
            print(f"Unsupported message type: {message_type}")
            return JsonResponse({'status': 'unsupported_type'})
        
        location_response.save()
        print(f"✅ Location response saved: {location_response.id}")
        
        return JsonResponse({
            'status': 'success',
            'response_id': location_response.id,
            'user': user.get_full_name(),
            'request_id': site_visit_request.id
        })
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in webhook")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        logger.error(f"WhatsApp webhook error: {e}")
        return JsonResponse({'error': str(e)}, status=500)