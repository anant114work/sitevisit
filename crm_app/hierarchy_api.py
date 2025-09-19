# crm_app/hierarchy_api.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from .models import UserProfile

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def update_hierarchy(request):
    """API endpoint to update user hierarchy via drag and drop"""
    try:
        # Check permissions
        user_profile = UserProfile.objects.get(user=request.user)
        if user_profile.role not in ['Admin', 'Sales Director - T1']:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_parent_id = data.get('new_parent_id')
        
        if not user_id:
            return JsonResponse({'error': 'User ID required'}, status=400)
        
        # Get the user profile to update
        profile = UserProfile.objects.get(user_id=user_id)
        
        # Set new parent
        if new_parent_id:
            new_parent = UserProfile.objects.get(user_id=new_parent_id)
            profile.parent = new_parent
        else:
            profile.parent = None
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Updated hierarchy for {profile.user.get_full_name()}'
        })
        
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)