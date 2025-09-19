from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, SiteVisitRequest, ApprovalLog, Notification

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'contact_number', 'parent']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'parent' in form.base_fields:
            if obj and obj.role:
                role_hierarchy = {
                    'rm': 'team_leader',
                    'team_leader': 'team_head', 
                    'team_head': 'business_head',
                    'business_head': 'cgo'
                }
                parent_role = role_hierarchy.get(obj.role)
                if parent_role:
                    form.base_fields['parent'].queryset = UserProfile.objects.filter(role=parent_role)
        return form

@admin.register(SiteVisitRequest)
class SiteVisitRequestAdmin(admin.ModelAdmin):
    list_display = ['team_member', 'customer_broker_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_broker_name', 'team_member__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['site_visit_request', 'approver', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']