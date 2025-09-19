import csv
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.contrib.auth.models import User
from .models import SiteVisitRequest, UserProfile, ApprovalLog, Notification
from .forms import SiteVisitRequestForm, ApprovalForm, ExcelUploadForm, CreateUserForm
from .utils import send_notification_to_approver, can_user_view_request, get_next_approver, get_subordinate_requests, send_whatsapp

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            user_profile = UserProfile.objects.get(user=user)
            
            # Check if first-time login
            if user_profile.first_login:
                # Store user ID in session for OTP verification
                request.session['first_login_user_id'] = user.id
                return redirect('setup_credentials')
            
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def otp_login_view(request):
    step = request.GET.get('step', 'phone')
    
    if request.method == 'POST':
        if 'phone_number' in request.POST and 'otp_code' not in request.POST:
            # Step 1: Send OTP
            phone_number = request.POST.get('phone_number')
            
            try:
                # Try exact match first, then with country code
                user_profile = None
                try:
                    user_profile = UserProfile.objects.get(contact_number=phone_number)
                except UserProfile.DoesNotExist:
                    try:
                        user_profile = UserProfile.objects.get(contact_number=f'91{phone_number}')
                    except UserProfile.DoesNotExist:
                        try:
                            user_profile = UserProfile.objects.get(contact_number__endswith=phone_number)
                        except UserProfile.MultipleObjectsReturned:
                            user_profile = UserProfile.objects.filter(
                                contact_number__endswith=phone_number,
                                first_login=True
                            ).first()
                
                if not user_profile:
                    raise UserProfile.DoesNotExist()
                
                if not user_profile.first_login:
                    messages.error(request, 'This account has already been activated. Use regular login.')
                    return redirect('login')
                
                # Generate and send OTP
                from .sms_service import generate_otp, send_otp_sms
                from django.utils import timezone
                
                otp_code = generate_otp()
                user_profile.otp_code = otp_code
                user_profile.otp_created_at = timezone.now()
                user_profile.save()
                
                result = send_otp_sms(phone_number, otp_code)
                
                if result['success']:
                    request.session['otp_phone'] = phone_number
                    masked_phone = phone_number[:2] + '*' * 6 + phone_number[-2:]
                    return render(request, 'registration/otp_login.html', {
                        'step': 'otp',
                        'phone_number': phone_number,
                        'masked_phone': masked_phone
                    })
                else:
                    messages.error(request, f'Failed to send OTP: {result["error"]}')
                    
            except UserProfile.DoesNotExist:
                messages.error(request, 'Phone number not found in our records.')
        
        elif 'otp_code' in request.POST:
            # Step 2: Verify OTP
            phone_number = request.POST.get('phone_number')
            otp_code = request.POST.get('otp_code')
            
            try:
                # Try exact match first, then with country code
                user_profile = None
                try:
                    user_profile = UserProfile.objects.get(contact_number=phone_number)
                except UserProfile.DoesNotExist:
                    try:
                        user_profile = UserProfile.objects.get(contact_number=f'91{phone_number}')
                    except UserProfile.DoesNotExist:
                        try:
                            user_profile = UserProfile.objects.get(contact_number__endswith=phone_number)
                        except UserProfile.MultipleObjectsReturned:
                            user_profile = UserProfile.objects.filter(
                                contact_number__endswith=phone_number,
                                first_login=True
                            ).first()
                
                if not user_profile:
                    raise UserProfile.DoesNotExist()
                
                from .sms_service import verify_otp
                result = verify_otp(user_profile, otp_code)
                
                if result['success']:
                    request.session['verified_user_id'] = user_profile.user.id
                    return redirect('setup_credentials')
                else:
                    messages.error(request, result['error'])
                    masked_phone = phone_number[:2] + '*' * 6 + phone_number[-2:]
                    return render(request, 'registration/otp_login.html', {
                        'step': 'otp',
                        'phone_number': phone_number,
                        'masked_phone': masked_phone
                    })
                    
            except UserProfile.DoesNotExist:
                messages.error(request, 'Invalid session. Please try again.')
                return redirect('otp_login')
    
    return render(request, 'registration/otp_login.html', {'step': step})

def setup_credentials_view(request):
    user_id = request.session.get('verified_user_id') or request.session.get('first_login_user_id')
    
    if not user_id:
        messages.error(request, 'Invalid session. Please start over.')
        return redirect('otp_login')
    
    try:
        user = User.objects.get(id=user_id)
        user_profile = UserProfile.objects.get(user=user)
        
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'registration/setup_credentials.html', {'user': user})
            
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, 'Username already taken.')
                return render(request, 'registration/setup_credentials.html', {'user': user})
            
            # Update user credentials
            user.username = username
            user.set_password(password)
            user.save()
            
            # Mark as no longer first login
            user_profile.first_login = False
            user_profile.save()
            
            # Clear session
            request.session.pop('verified_user_id', None)
            request.session.pop('first_login_user_id', None)
            
            # Login user
            login(request, user)
            messages.success(request, 'Account setup completed successfully!')
            return redirect('dashboard')
        
        return render(request, 'registration/setup_credentials.html', {'user': user})
        
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, 'Invalid user session.')
        return redirect('otp_login')

@csrf_exempt
def resend_otp_view(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        
        try:
            # Try exact match first, then with country code
            user_profile = None
            try:
                user_profile = UserProfile.objects.get(contact_number=phone_number)
            except UserProfile.DoesNotExist:
                try:
                    user_profile = UserProfile.objects.get(contact_number=f'91{phone_number}')
                except UserProfile.DoesNotExist:
                    try:
                        user_profile = UserProfile.objects.get(contact_number__endswith=phone_number)
                    except UserProfile.MultipleObjectsReturned:
                        user_profile = UserProfile.objects.filter(
                            contact_number__endswith=phone_number,
                            first_login=True
                        ).first()
            
            if not user_profile:
                raise UserProfile.DoesNotExist()
            
            from .sms_service import generate_otp, send_otp_sms
            from django.utils import timezone
            
            otp_code = generate_otp()
            user_profile.otp_code = otp_code
            user_profile.otp_created_at = timezone.now()
            user_profile.save()
            
            result = send_otp_sms(phone_number, otp_code)
            return JsonResponse(result)
            
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    context = {
        'user_profile': user_profile,
        'notifications': notifications,
    }
    
    # All users can see their own requests
    context['my_requests'] = SiteVisitRequest.objects.filter(team_member=request.user)[:5]
    
    if user_profile.role in ['Admin', 'Sales Director - T1']:
        # Admin/Director sees all requests in the system
        context['pending_requests'] = SiteVisitRequest.objects.filter(status='pending')[:5]
        context['total_requests'] = SiteVisitRequest.objects.count()
        context['all_requests'] = SiteVisitRequest.objects.all()[:10]
    else:
        # Other roles see requests from their subordinates
        subordinate_requests = get_subordinate_requests(user_profile)
        context['pending_requests'] = subordinate_requests.filter(status='pending')[:5]
    
    return render(request, 'dashboard.html', context)

@login_required
def create_site_visit_request(request):
    user_profile = UserProfile.objects.get(user=request.user)
    # All users can create site visit requests
    
    if request.method == 'POST':
        form = SiteVisitRequestForm(request.POST)
        if form.is_valid():
            site_visit = form.save(commit=False)
            site_visit.team_member = request.user
            site_visit.save()
            
            # Send notification to next approver
            send_notification_to_approver(site_visit)
            
            # Schedule location update reminder after 60 minutes
            from .tasks import schedule_location_reminder
            schedule_location_reminder(site_visit.id)
            
            # Debug: Test immediate reminder
            print(f"\n🔍 DEBUG: Testing immediate location reminder for request {site_visit.id}")
            try:
                from .whatsapp_service import send_location_update_reminder
                user_profile = UserProfile.objects.get(user=request.user)
                if user_profile.contact_number:
                    result = send_location_update_reminder(
                        user_profile.contact_number,
                        request.user.get_full_name()
                    )
                    print(f"Debug reminder result: {result}")
                else:
                    print("No contact number found for user")
            except Exception as e:
                print(f"Debug reminder error: {e}")
            
            messages.success(request, 'Site visit request created and sent for approval!')
            return redirect('my_requests')
    else:
        form = SiteVisitRequestForm()
    
    return render(request, 'create_request.html', {'form': form, 'user_profile': user_profile})

@login_required
def my_requests(request):
    user_profile = UserProfile.objects.get(user=request.user)
    # All users can view their own requests
    
    requests = SiteVisitRequest.objects.filter(team_member=request.user).order_by('-created_at')
    return render(request, 'my_requests.html', {'requests': requests})

@login_required
def view_requests(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # All users can access view requests page
    
    if user_profile.role in ['Admin', 'Sales Director - T1']:
        requests = SiteVisitRequest.objects.all().order_by('-created_at')
    else:
        requests = get_subordinate_requests(user_profile).order_by('-created_at')
    
    return render(request, 'view_requests.html', {'requests': requests, 'user_profile': user_profile})

@login_required
def request_detail(request, request_id):
    site_visit_request = get_object_or_404(SiteVisitRequest, id=request_id)
    
    if not can_user_view_request(request.user, site_visit_request):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('dashboard')
    
    user_profile = UserProfile.objects.get(user=request.user)
    can_approve = False
    
    # Check if user can approve this request
    if site_visit_request.status == 'pending':
        # Check if user hasn't already approved
        already_approved = site_visit_request.approvals.filter(
            approver=request.user, 
            action='approved'
        ).exists()
        
        # Allow specific roles to approve
        can_approve_role = user_profile.role in [
            'Admin', 
            'Sales Director - T1', 
            'Sales Manager - T4', 
            'TEAM Head - T2', 
            'Team leader - t3'
        ]
        
        can_approve = can_approve_role and not already_approved
    
    if request.method == 'POST' and can_approve:
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.site_visit_request = site_visit_request
            approval.approver = request.user
            approval.save()
            
            if approval.action == 'rejected':
                site_visit_request.status = 'rejected'
                site_visit_request.save()
                messages.success(request, 'Request rejected successfully.')
            else:
                # Check if all required approvals are complete
                requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
                
                # Get all required approvers (hierarchy + Admin + Sales Director)
                required_approvers = []
                current = requester_profile
                while current.parent:
                    current = current.parent
                    required_approvers.append(current.user)
                
                # Add Admin and Sales Director
                admin_user = User.objects.filter(userprofile__role='Admin').first()
                if admin_user and admin_user not in required_approvers:
                    required_approvers.append(admin_user)
                    
                director_user = User.objects.filter(userprofile__role='Sales Director - T1').first()
                if director_user and director_user not in required_approvers:
                    required_approvers.append(director_user)
                
                # Check how many have approved
                approved_count = site_visit_request.approvals.filter(
                    approver__in=required_approvers,
                    action='approved'
                ).count()
                
                if approved_count >= len(required_approvers):
                    # All required approvals complete
                    site_visit_request.status = 'approved'
                    site_visit_request.save()
                    # Notify requester of final approval
                    Notification.objects.create(
                        user=site_visit_request.team_member,
                        message=f'Your site visit request for {site_visit_request.customer_broker_name} has been approved!',
                        site_visit_request=site_visit_request
                    )
                    requester_profile = UserProfile.objects.get(user=site_visit_request.team_member)
                    if requester_profile.contact_number:
                        from .utils import send_whatsapp
                        send_whatsapp([requester_profile.contact_number], 'Your site visit request has been approved!')
                    
                    # Send approval email
                    email_address = requester_profile.email or site_visit_request.team_member.email
                    if email_address:
                        from .email_service import send_email
                        subject = "Site Visit Request Approved"
                        message = f"Your site visit request for {site_visit_request.customer_broker_name} has been approved!"
                        send_email([email_address], subject, message, site_visit_request.id)
                    messages.success(request, 'Request approved successfully!')
                else:
                    messages.success(request, f'Your approval recorded. {len(required_approvers) - approved_count} more approvals needed.')
            
            return redirect('request_detail', request_id=request_id)
    else:
        form = ApprovalForm()
    
    approvals = site_visit_request.approvals.all().order_by('timestamp')
    
    context = {
        'site_visit_request': site_visit_request,
        'approvals': approvals,
        'can_approve': can_approve,
        'form': form,
        'user_profile': user_profile,
    }
    
    return render(request, 'request_detail.html', context)

@login_required
def export_requests_csv(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Only Admin/Director can export data.')
        return redirect('dashboard')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="site_visit_requests.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Team Member', 'Customer/Broker Name', 'Contact Number', 
        'Location Address', 'Latitude', 'Longitude', 'Status', 
        'Created At', 'Updated At'
    ])
    
    for request_obj in SiteVisitRequest.objects.all():
        writer.writerow([
            request_obj.team_member.get_full_name(),
            request_obj.customer_broker_name,
            request_obj.customer_broker_contact,
            request_obj.location_address,
            request_obj.latitude,
            request_obj.longitude,
            request_obj.get_status_display(),
            request_obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            request_obj.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def upload_users_excel(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Only Admin/Director can upload users.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                df = pd.read_excel(excel_file)
                created_count = 0
                error_count = 0
                
                for index, row in df.iterrows():
                    try:
                        name_parts = str(row['Name']).split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ''
                        
                        username = str(row['Email']).split('@')[0].lower().replace('.', '')
                        
                        # Create user
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': str(row['Email']),
                            }
                        )
                        
                        if created:
                            user.set_password('password123')
                            user.save()
                        
                        # Find parent user
                        parent_profile = None
                        if pd.notna(row['Parent User']) and str(row['Parent User']).strip():
                            parent_name = str(row['Parent User']).strip()
                            parent_users = User.objects.filter(
                                Q(first_name__icontains=parent_name.split()[0]) |
                                Q(username__icontains=parent_name.lower().replace(' ', ''))
                            )
                            if parent_users.exists():
                                parent_profile = UserProfile.objects.filter(user=parent_users.first()).first()
                        
                        # Create/update profile
                        profile, profile_created = UserProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                'role': str(row['Role']),
                                'contact_number': str(row['Phone']),
                                'parent': parent_profile
                            }
                        )
                        
                        if not profile_created:
                            profile.role = str(row['Role'])
                            profile.contact_number = str(row['Phone'])
                            profile.parent = parent_profile
                            profile.save()
                        
                        created_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        print(f"Error processing row {index}: {e}")
                
                messages.success(request, f'Successfully processed {created_count} users. {error_count} errors.')
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = ExcelUploadForm()
    
    return render(request, 'upload_users.html', {'form': form})

@login_required
def create_user(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Only Admin/Director can create users.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            try:
                base_username = form.cleaned_data['email'].split('@')[0].lower().replace('.', '')
                username = base_username
                counter = 1
                
                # Handle duplicate usernames
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': form.cleaned_data['email'],
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                    }
                )
                
                if created:
                    user.set_password('password123')
                    user.save()
                
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': form.cleaned_data['role'],
                        'contact_number': form.cleaned_data['phone'],
                        'parent': form.cleaned_data['parent']
                    }
                )
                
                if not profile_created:
                    profile.role = form.cleaned_data['role']
                    profile.contact_number = form.cleaned_data['phone']
                    profile.parent = form.cleaned_data['parent']
                    profile.save()
                
                messages.success(request, f'User {user.get_full_name()} created successfully! Username: {username}, Password: password123')
                return redirect('create_user')
                
            except Exception as e:
                messages.error(request, f'Error creating user: {str(e)}')
    else:
        form = CreateUserForm()
    
    return render(request, 'create_user.html', {'form': form})

@login_required
def edit_profile(request, user_id=None):
    current_user_profile = UserProfile.objects.get(user=request.user)
    
    # Allow CGO/Admin to edit any profile, others can only edit their own
    if user_id and current_user_profile.role in ['Admin', 'Sales Director - T1']:
        target_user = get_object_or_404(User, id=user_id)
        user_profile = UserProfile.objects.get(user=target_user)
    else:
        user_profile = current_user_profile
    
    if request.method == 'POST':
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        user_profile.contact_number = contact_number
        if email:
            user_profile.email = email
        
        # Only CGO/Admin can change roles
        if role and current_user_profile.role in ['Admin', 'Sales Director - T1']:
            user_profile.role = role
        
        user_profile.save()
        messages.success(request, f'Profile updated successfully for {user_profile.user.get_full_name()}!')
        
        if user_id:
            return redirect('manage_users')
        else:
            return redirect('dashboard')
    
    return render(request, 'edit_profile.html', {
        'user_profile': user_profile, 
        'can_edit_role': current_user_profile.role in ['Admin', 'Sales Director - T1'],
        'is_editing_other': user_id is not None
    })

@login_required
def manage_users(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        contact_number = request.POST.get('contact_number')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        profile = UserProfile.objects.get(user_id=user_id)
        profile.contact_number = contact_number
        if email:
            profile.email = email
        if role:
            profile.role = role
        profile.save()
        
        messages.success(request, f'Updated profile for {profile.user.get_full_name()}')
    
    users = UserProfile.objects.all().order_by('role', 'user__first_name')
    return render(request, 'manage_users.html', {'users': users})

@login_required
def location_responses(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    from .models import LocationResponse
    location_responses = LocationResponse.objects.all().order_by('-received_at')
    
    return render(request, 'location_responses.html', {
        'location_responses': location_responses
    })

@login_required
def hierarchy_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile.role not in ['Admin', 'Sales Director - T1']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        parent_id = request.POST.get('parent_id')
        
        try:
            target_profile = UserProfile.objects.get(user_id=user_id)
            
            if action == 'assign' and parent_id:
                parent_profile = UserProfile.objects.get(user_id=parent_id)
                target_profile.parent = parent_profile
                target_profile.save()
                messages.success(request, f'{target_profile.user.get_full_name()} assigned under {parent_profile.user.get_full_name()}')
                
            elif action == 'unassign':
                target_profile.parent = None
                target_profile.save()
                messages.success(request, f'{target_profile.user.get_full_name()} removed from hierarchy')
                
        except UserProfile.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
        return redirect('hierarchy_view')
    
    # Get root profiles (top-level managers)
    root_profiles = UserProfile.objects.filter(
        parent=None,
        role__in=['Admin', 'Sales Director - T1']
    ).order_by('role')
    
    # Get unassigned profiles
    unassigned_profiles = UserProfile.objects.filter(
        parent=None
    ).exclude(
        role__in=['Admin', 'Sales Director - T1']
    ).order_by('role')
    
    return render(request, 'hierarchy_view.html', {
        'root_profiles': root_profiles,
        'unassigned_profiles': unassigned_profiles
    })