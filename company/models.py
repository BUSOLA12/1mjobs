from django.db import models
from django.conf import settings

# Create your models here.


COMPANY_INDUSTRIES = [
    ('accounting_and_finance', 'Accounting and Finance'),
    ('clerical_and_data_entry', 'Clerical and Data Entry'),
    ('customer_service', 'Customer Service'),
    ('engineering_and_technical', 'Engineering and Technical'),
    ('healthcare', 'Healthcare'),
    ('hospitality_and_tourism', 'Hospitality and Tourism'),
    ('information_technology', 'Information Technology'),
    ('legal', 'Legal'),
    ('marketing_and_advertising', 'Marketing and Advertising'),
    ('sales_and_business_development', 'Sales and Business Development'),
    ('skilled_trades_and_services', 'Skilled Trades and Services'),
    ('education_and_training', 'Education and Training'),
    ('creative_and_design', 'Creative and Design'),
    ('real_estate_and_property_management', 'Real Estate and Property Management'),
    ('transportation_and_logistics', 'Transportation and Logistics'),
    ('construction_and_maintenance', 'Construction and Maintenance'),
    ('research_and_development', 'Research and Development'),
    ('non_profit_and_volunteering', 'Non-Profit and Volunteering'),
    ('government_and_public_service', 'Government and Public Service'),
    ('media_and_entertainment', 'Media and Entertainment'),
    ('telecommunications', 'Telecommunications'),
    ('energy_and_utilities', 'Energy and Utilities'),
    ('agriculture_and_environment', 'Agriculture and Environment'),
    ('science_and_technology', 'Science and Technology'),
]

VERIFICATION_STATUS = [
    ('pending', 'Pending Review'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]

# The set of fields an admin verifies one by one. (name, label)
VERIFIABLE_FIELDS = [
    ('company_name', 'Company Name'),
    ('brand_name', 'Brand / Trading Name'),
    ('industry', 'Industry'),
    ('description', 'Description'),
    ('registration_number', 'Registration / RC Number'),
    ('tin', 'Tax ID (TIN)'),
    ('established_date', 'Date Established'),
    ('company_size', 'Company Size'),
    ('headquarters_address', 'Headquarters Address'),
    ('primary_phone', 'Primary Phone'),
    ('secondary_phone', 'Secondary Phone'),
    ('email', 'Official Email'),
    ('website', 'Website'),
    ('facebook', 'Facebook'),
    ('linkedin', 'LinkedIn'),
    ('company_country', 'Company Country'),
    ('logo', 'Logo'),
    ('documents', 'Documents'),
]

class Company(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='creator',
        null=True, blank=True
    )    
    company_name = models.CharField(max_length=250)
    brand_name = models.CharField(max_length=250, null=True, blank=True)
    industry = models.CharField(max_length=250, choices=COMPANY_INDUSTRIES)
    description = models.TextField()
    registration_number = models.CharField(max_length=250, null=True, blank=True)
    tin = models.CharField(max_length=250, null=True, blank=True)
    established_date = models.DateTimeField(blank=True, null=True)
    company_size = models.CharField(max_length=250, null=True, blank=True)
    headquarters_address = models.CharField(max_length=250, blank=True, null=True)
    primary_phone = models.CharField(max_length=50, blank=True)
    secondary_phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=250, blank=True, null=True, unique=True)
    website = models.CharField(max_length=250, blank=True, null=True, unique=True)
    facebook = models.CharField(max_length=250, blank=True, null=True, unique=True)
    linkedin = models.CharField(max_length=250, blank=True, null=True, unique=True)
    logo = models.ImageField(upload_to='company_logo/', blank=True, null=True)
    documents = models.FileField(upload_to='company_documents/', blank=True, null=True)
    company_country = models.CharField(max_length=150, blank=True, null=True)
    members = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='members', blank=True, null=True)
    verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    # {"registration_number": {"status": "rejected", "note": "doesn't match CAC"}, ...}
    field_reviews = models.JSONField(default=dict, blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_companies'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    def get_field_status(self, name):
        return (self.field_reviews or {}).get(name, {}).get('status', 'pending')

    def get_field_note(self, name):
        return (self.field_reviews or {}).get(name, {}).get('note', '')

    def recompute_verification(self):
        statuses = [self.get_field_status(f) for f, _ in VERIFIABLE_FIELDS]
        if any(s == 'rejected' for s in statuses):
            self.verification_status = 'rejected'
            self.verified = False
        elif statuses and all(s == 'approved' for s in statuses):
            self.verification_status = 'approved'
            self.verified = True
        else:
            self.verification_status = 'pending'
            self.verified = False


