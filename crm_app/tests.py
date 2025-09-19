from django.test import TestCase
from django.contrib.auth.models import User
from .models import UserProfile, SiteVisitRequest
from .utils import can_user_view_request, get_next_approver

class CRMTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.team_member_user = User.objects.create_user('team1', 'team1@test.com', 'pass')
        self.bh_user = User.objects.create_user('bh1', 'bh1@test.com', 'pass')
        self.hr_user = User.objects.create_user('hr1', 'hr1@test.com', 'pass')
        self.cgo_user = User.objects.create_user('cgo1', 'cgo1@test.com', 'pass')
        
        # Create profiles
        self.team_profile = UserProfile.objects.create(
            user=self.team_member_user, role='team_member', contact_number='1234567890'
        )
        self.bh_profile = UserProfile.objects.create(
            user=self.bh_user, role='business_head', contact_number='1234567891'
        )
        self.hr_profile = UserProfile.objects.create(
            user=self.hr_user, role='hr', contact_number='1234567892'
        )
        self.cgo_profile = UserProfile.objects.create(
            user=self.cgo_user, role='cgo', contact_number='1234567893'
        )
        
        # Set hierarchy
        self.team_profile.business_head = self.bh_profile
        self.team_profile.save()
        
        # Create test request
        self.request = SiteVisitRequest.objects.create(
            team_member=self.team_member_user,
            customer_broker_name='Test Customer',
            customer_broker_contact='9876543210',
            location_address='Test Address',
            latitude=12.9716,
            longitude=77.5946
        )
    
    def test_permission_system(self):
        # Team member can view own request
        self.assertTrue(can_user_view_request(self.team_member_user, self.request))
        
        # Business head can view team member's request
        self.assertTrue(can_user_view_request(self.bh_user, self.request))
        
        # HR can view all requests
        self.assertTrue(can_user_view_request(self.hr_user, self.request))
        
        # CGO can view all requests
        self.assertTrue(can_user_view_request(self.cgo_user, self.request))
    
    def test_approval_workflow(self):
        # First approver should be business head
        next_approver = get_next_approver(self.request)
        self.assertEqual(next_approver, self.bh_user)