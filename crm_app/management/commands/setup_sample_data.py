from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from crm_app.models import UserProfile

class Command(BaseCommand):
    help = 'Create sample users with different roles'

    def handle(self, *args, **options):
        # Create CGO
        cgo_user, created = User.objects.get_or_create(
            username='cgo',
            defaults={
                'first_name': 'Chief',
                'last_name': 'Growth Officer',
                'email': 'cgo@company.com',
                'is_staff': True
            }
        )
        if created:
            cgo_user.set_password('cgo123')
            cgo_user.save()
        
        cgo_profile, _ = UserProfile.objects.get_or_create(
            user=cgo_user,
            defaults={
                'role': 'Sales Director - T1',
                'contact_number': '+919876543210'
            }
        )

        # Create HR
        hr_user, created = User.objects.get_or_create(
            username='hr',
            defaults={
                'first_name': 'HR',
                'last_name': 'Manager',
                'email': 'hr@company.com'
            }
        )
        if created:
            hr_user.set_password('hr123')
            hr_user.save()
        
        hr_profile, _ = UserProfile.objects.get_or_create(
            user=hr_user,
            defaults={
                'role': 'Admin',
                'contact_number': '+919876543211'
            }
        )

        # Create Business Head
        bh_user, created = User.objects.get_or_create(
            username='businesshead',
            defaults={
                'first_name': 'Business',
                'last_name': 'Head',
                'email': 'bh@company.com'
            }
        )
        if created:
            bh_user.set_password('bh123')
            bh_user.save()
        
        bh_profile, _ = UserProfile.objects.get_or_create(
            user=bh_user,
            defaults={
                'role': 'Sales Manager - T4',
                'contact_number': '+919876543212'
            }
        )

        # Create Team Head
        th_user, created = User.objects.get_or_create(
            username='teamhead',
            defaults={
                'first_name': 'Team',
                'last_name': 'Head',
                'email': 'th@company.com'
            }
        )
        if created:
            th_user.set_password('th123')
            th_user.save()
        
        th_profile, _ = UserProfile.objects.get_or_create(
            user=th_user,
            defaults={
                'role': 'TEAM Head - T2',
                'contact_number': '+919876543213',
                'parent': bh_profile
            }
        )

        # Create Team Leader
        tl_user, created = User.objects.get_or_create(
            username='teamleader',
            defaults={
                'first_name': 'Team',
                'last_name': 'Leader',
                'email': 'tl@company.com'
            }
        )
        if created:
            tl_user.set_password('tl123')
            tl_user.save()
        
        tl_profile, _ = UserProfile.objects.get_or_create(
            user=tl_user,
            defaults={
                'role': 'Team leader - t3',
                'contact_number': '+919876543214',
                'parent': th_profile
            }
        )

        # Create RM
        rm_user, created = User.objects.get_or_create(
            username='rm',
            defaults={
                'first_name': 'Relationship',
                'last_name': 'Manager',
                'email': 'rm@company.com'
            }
        )
        if created:
            rm_user.set_password('rm123')
            rm_user.save()
        
        rm_profile, _ = UserProfile.objects.get_or_create(
            user=rm_user,
            defaults={
                'role': 'Sales Executive - T5',
                'contact_number': '+919876543215',
                'parent': tl_profile
            }
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Sample users created successfully!\n'
                'Sales Director: cgo/cgo123\n'
                'Admin: hr/hr123\n'
                'Sales Manager: businesshead/bh123\n'
                'Team Head: teamhead/th123\n'
                'Team Leader: teamleader/tl123\n'
                'Sales Executive: rm/rm123'
            )
        )