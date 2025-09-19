from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Sales Executive - T5', 'Sales Executive - T5'),
        ('Team leader - t3', 'Team Leader - T3'),
        ('TEAM Head - T2', 'Team Head - T2'),
        ('Sales Manager - T4', 'Sales Manager - T4'),
        ('Sales Director - T1', 'Sales Director - T1'),
        ('Admin', 'Admin'),
        ('BROKER', 'Broker'),
        ('Telecaller - T6', 'Telecaller - T6'),
        ('Commercial', 'Commercial'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    first_login = models.BooleanField(default=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

class SiteVisitRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    LOCATION_CHOICES = [
        ('noida', 'Noida'),
        ('gurgaon', 'Gurgaon'),
        ('delhi', 'Delhi'),
        ('faridabad', 'Faridabad'),
        ('ghaziabad', 'Ghaziabad'),
        ('other', 'Other'),
    ]
    
    team_member = models.ForeignKey(User, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=200)
    customer_broker_name = models.CharField(max_length=200)
    customer_broker_contact = models.CharField(max_length=15)
    visit_date = models.DateField(default=timezone.now)
    location_city = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='noida')
    location_address = models.TextField()
    latitude = models.DecimalField(max_digits=12, decimal_places=10, null=True, blank=True)
    longitude = models.DecimalField(max_digits=13, decimal_places=10, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Site Visit - {self.customer_broker_name} by {self.team_member.get_full_name()}"

class ApprovalLog(models.Model):
    site_visit_request = models.ForeignKey(SiteVisitRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=[('approved', 'Approved'), ('rejected', 'Rejected')])
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.action.title()} by {self.approver.get_full_name()}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    site_visit_request = models.ForeignKey(SiteVisitRequest, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class LocationResponse(models.Model):
    site_visit_request = models.ForeignKey(SiteVisitRequest, on_delete=models.CASCADE, related_name='location_responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    latitude = models.DecimalField(max_digits=12, decimal_places=10, null=True, blank=True)
    longitude = models.DecimalField(max_digits=13, decimal_places=10, null=True, blank=True)
    address = models.TextField(blank=True)
    response_type = models.CharField(max_length=20, choices=[('location', 'Location'), ('text', 'Text')], default='location')
    message_content = models.TextField(blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-received_at']
    
    def __str__(self):
        return f"Location Response from {self.user.get_full_name()} - {self.received_at}"