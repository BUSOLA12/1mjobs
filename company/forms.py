from django import forms
from .models import Company


class CompanyResubmitForm(forms.ModelForm):
    """Employer-facing form used to correct and resubmit a company after an
    admin flagged one or more fields during verification."""

    class Meta:
        model = Company
        fields = [
            'company_name', 'brand_name', 'industry', 'description',
            'registration_number', 'tin', 'established_date', 'company_size',
            'headquarters_address', 'primary_phone', 'secondary_phone',
            'email', 'website', 'facebook', 'linkedin', 'company_country',
            'logo', 'documents',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'established_date': forms.DateInput(attrs={'type': 'date'}),
        }
