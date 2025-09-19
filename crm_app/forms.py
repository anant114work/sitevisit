from django import forms
from django.contrib.auth.models import User
from .models import SiteVisitRequest, ApprovalLog, UserProfile

class SiteVisitRequestForm(forms.ModelForm):
    class Meta:
        model = SiteVisitRequest
        fields = ['project_name', 'customer_broker_name', 'customer_broker_contact', 'visit_date', 'location_city', 'location_address', 'latitude', 'longitude']
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project name'}),
            'customer_broker_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter customer/broker name'}),
            'customer_broker_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact number'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location_city': forms.Select(attrs={'class': 'form-select'}),
            'location_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter detailed address'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

class ApprovalForm(forms.ModelForm):
    class Meta:
        model = ApprovalLog
        fields = ['action', 'comments']
        widgets = {
            'action': forms.Select(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'}),
        help_text='Upload Excel file with columns: Name, Email, Phone, Parent User, Role'
    )

class CreateUserForm(forms.Form):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    parent = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(), 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="No Parent"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = UserProfile.objects.exclude(role__in=['Sales Executive - T5', 'BROKER', 'Telecaller - T6'])