# crm_app/location_service.py
import requests
import logging

logger = logging.getLogger(__name__)

# MapMyIndia API Credentials
CLIENT_ID = '96dHZVzsAuvRIR9MoMTPmwzh9VlDMzB0fhcMlrHqtkIX9lbrGGQarp5t5nRPsvK-fAudtWWw81iUNa2Y4hhwt-1F6FNEdRUP'
CLIENT_SECRET = 'lrFxI-iSEg9KOqzlrDTGqtTNdjtHgZ1aCmQ2KyZZhRFdhMNPlSLvv49YpjYAYXqxI6palJrRF0PPTuv89PPp4Oir4DYADtlu21OWYMF2y8s='
AUTH_URL = 'https://outpost.mapmyindia.com/api/security/oauth/token'

def get_access_token():
    """Get MapMyIndia access token"""
    try:
        print(f"\n🔑 REQUESTING MapMyIndia access token...")
        response = requests.post(
            AUTH_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            },
            timeout=10
        )
        print(f"Auth response status: {response.status_code}")
        print(f"Auth response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            token = response_data['access_token']
            print(f"✅ Got access token: {token[:20]}...")
            return token
        else:
            print(f"❌ Auth failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ MapMyIndia auth error: {e}")
        return None

def get_address_from_coordinates(lat, lng):
    """Get precise address from GPS coordinates using MapMyIndia"""
    try:
        print(f"\n🗺️ GETTING ADDRESS for coordinates: {lat}, {lng}")
        
        access_token = get_access_token()
        if not access_token:
            print("❌ No access token available")
            return {'success': False, 'error': 'Authentication failed'}
            
        url = f'https://atlas.mapmyindia.com/api/advancedmaps/v1/{access_token}/rev_geocode?lat={lat}&lng={lng}'
        print(f"Geocoding URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Geocoding response status: {response.status_code}")
        print(f"MapmyIndia API Response: {response.text}")
        
        if response.status_code == 200:
            res_data = response.json()
            
            if 'results' in res_data and len(res_data['results']) > 0:
                address = res_data['results'][0]['formatted_address']
                print(f"✅ Got address: {address}")
                
                return {
                    'formatted_address': address,
                    'success': True
                }
            else:
                print("❌ No results in geocoding response")
                return {'success': False, 'error': 'Address not found'}
        else:
            print(f"❌ Geocoding API error: {response.status_code} - {response.text}")
            return {'success': False, 'error': f'API error: {response.status_code}'}
        
    except Exception as e:
        print(f"❌ MapMyIndia geocoding error: {e}")
        return {'success': False, 'error': str(e)}