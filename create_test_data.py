#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
django.setup()

from django.contrib.auth.models import User
from crm_app.models import SiteVisitRequest

# Create a test request from RM
rm_user = User.objects.get(username='rm')

SiteVisitRequest.objects.create(
    team_member=rm_user,
    customer_broker_name='Test Customer ABC',
    customer_broker_contact='9876543210',
    location_address='123 Test Street, Test City',
    latitude=12.9716,
    longitude=77.5946,
    status='pending'
)

SiteVisitRequest.objects.create(
    team_member=rm_user,
    customer_broker_name='Demo Client XYZ',
    customer_broker_contact='9876543211',
    location_address='456 Demo Avenue, Demo City',
    latitude=12.9800,
    longitude=77.6000,
    status='pending'
)

print("Test requests created successfully!")