#!/usr/bin/env python
"""
Quick setup script for the CRM application
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
    django.setup()
    
    print("Setting up CRM Application...")
    
    # Run migrations
    print("1. Creating database tables...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create sample data
    print("2. Creating sample users...")
    execute_from_command_line(['manage.py', 'setup_sample_data'])
    
    print("\nSetup completed successfully!")
    print("\nYou can now:")
    print("1. Run: python manage.py runserver")
    print("2. Access: http://localhost:8000/")
    print("3. Login with sample users:")
    print("   - CGO: cgo/cgo123")
    print("   - HR: hr/hr123") 
    print("   - Business Head: businesshead/bh123")
    print("   - Team Head: teamhead/th123")
    print("   - Team Leader: teamleader/tl123")
    print("   - RM: rm/rm123")
    print("4. Admin panel: http://localhost:8000/admin/")