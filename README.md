# CRM Site Visit Management System

A Django-based CRM application for managing site visit requests with hierarchical approval workflow.

## Features

- **User Hierarchy**: RM → Team Leader → Team Head → Business Head → CGO
- **Site Visit Requests**: Create, track, and approve site visit requests
- **Live Location Capture**: HTML5 Geolocation API integration
- **SMS Notifications**: Edumarc SMS API integration
- **Role-based Access Control**: Strict permission enforcement
- **Google Maps Integration**: View request locations on maps
- **CSV Export**: Export data for analysis (CGO only)

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

5. **Access Admin Panel**
   - Go to `http://localhost:8000/admin/`
   - Create users and assign roles via UserProfile

## User Management

1. Create users in Django Admin
2. Assign roles via UserProfile:
   - `rm`: Can create and view own requests
   - `team_leader`: Can approve RM requests
   - `team_head`: Can approve team leader requests
   - `business_head`: Can approve team head requests
   - `cgo`: Final approval authority, can export data

3. Set parent relationships in hierarchy

## API Configuration

Update `settings.py` with your SMS API credentials:
- `SMS_API_KEY`: Your Edumarc API key
- `SMS_API_URL`: SMS API endpoint
- `SMS_SENDER_ID`: Sender ID for SMS
- `SMS_TEMPLATE_ID`: DLT approved template ID

## Workflow

1. RM creates site visit request with location
2. Team Leader receives notification and approves/rejects
3. If approved, Team Head receives notification for approval
4. If approved, Business Head receives notification for approval
5. If approved, CGO receives notification for final approval
6. SMS notifications sent at each stage
7. Request status updated based on approvals/rejections

## Security Features

- Role-based access control
- Users can only see permitted data
- Sequential approval workflow
- Audit trail for all approvals
- Location verification via coordinates