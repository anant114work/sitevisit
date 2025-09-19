# crm_app/api_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .location_service import get_address_from_coordinates

@csrf_exempt
@require_http_methods(["POST"])
def get_address_from_location(request):
    """API endpoint to get address from GPS coordinates"""
    try:
        print(f"\n🔍 API ENDPOINT CALLED: {request.method} {request.path}")
        print(f"Request body: {request.body}")
        
        data = json.loads(request.body)
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        print(f"Extracted coordinates: lat={lat}, lng={lng}")
        
        if not lat or not lng:
            print("❌ Missing coordinates")
            return JsonResponse({'error': 'Latitude and longitude required'}, status=400)
        
        # Get address from MapMyIndia
        print("Calling MapMyIndia service...")
        address_data = get_address_from_coordinates(lat, lng)
        
        print(f"MapMyIndia response: {address_data}")
        
        if address_data and address_data.get('success'):
            print("✅ Returning successful response")
            # Match Flask response format
            return JsonResponse({
                'address': address_data['formatted_address'],
                'success': True
            })
        else:
            # Fallback: Return coordinates as address if MapMyIndia fails
            fallback_address = f"Location: {lat:.6f}, {lng:.6f}"
            print(f"⚠️ Using fallback address: {fallback_address}")
            return JsonResponse({
                'address': fallback_address,
                'success': True,
                'note': 'MapMyIndia lookup failed, showing coordinates'
            })
            
    except Exception as e:
        print(f"❌ API Exception: {e}")
        return JsonResponse({'error': str(e), 'success': False}, status=500)