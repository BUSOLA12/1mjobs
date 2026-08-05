from django import forms
from pricing.models import Plan

class AdminPlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            "name",
            "user_type",
            "description",
            "monthly_price",
            "yearly_price",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "user_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "monthly_price": forms.NumberInput(attrs={"class": "form-control"}),
            "yearly_price": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        monthly = cleaned_data.get("monthly_price")
        yearly = cleaned_data.get("yearly_price")

        if yearly and monthly and yearly < monthly:
            self.add_error(
                "yearly_price",
                "Yearly price should not be less than monthly price."
            )

        return cleaned_data

# admin_panel/forms.py
from django import forms
from pricing.models import PlanFeature
from pricing.features import FEATURE_CHOICES

class AdminPlanFeatureForm(forms.ModelForm):
    # The feature name must be one of the keys the code actually checks, so it's
    # a dropdown rather than free text (a typo would silently gate nothing).
    feature_name = forms.ChoiceField(
        choices=FEATURE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = PlanFeature
        fields = ["feature_name", "is_boolean", "limit"]

        widgets = {
            "is_boolean": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "limit": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_boolean = cleaned_data.get("is_boolean")
        limit = cleaned_data.get("limit")

        if is_boolean and limit:
            self.add_error("limit", "Boolean features should not have a limit.")

        if not is_boolean and limit is None:
            self.add_error("limit", "Non-boolean features must have a limit or be unlimited.")

        return cleaned_data


# admin_panel/forms.py
from company.models import Company


class AdminCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "created_by",
            "members",
            "company_name",
            "brand_name",
            "industry",
            "description",
            "registration_number",
            "tin",
            "established_date",
            "company_size",
            "headquarters_address",
            "primary_phone",
            "secondary_phone",
            "email",
            "website",
            "facebook",
            "linkedin",
            "company_country",
            "logo",
            "documents",
        ]

        widgets = {
            "created_by": forms.Select(attrs={"class": "form-select"}),
            "members": forms.Select(attrs={"class": "form-select"}),
            "company_name": forms.TextInput(attrs={"class": "form-control"}),
            "brand_name": forms.TextInput(attrs={"class": "form-control"}),
            "industry": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "registration_number": forms.TextInput(attrs={"class": "form-control"}),
            "tin": forms.TextInput(attrs={"class": "form-control"}),
            "established_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "company_size": forms.TextInput(attrs={"class": "form-control"}),
            "headquarters_address": forms.TextInput(attrs={"class": "form-control"}),
            "primary_phone": forms.TextInput(attrs={"class": "form-control"}),
            "secondary_phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.TextInput(attrs={"class": "form-control"}),
            "facebook": forms.TextInput(attrs={"class": "form-control"}),
            "linkedin": forms.TextInput(attrs={"class": "form-control"}),
            "company_country": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "documents": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # created_by / members are optional links to user accounts.
        self.fields["created_by"].required = False
        self.fields["created_by"].label = "Owner account (created by)"
        self.fields["created_by"].empty_label = "— none —"
        self.fields["members"].required = False
        self.fields["members"].label = "Member account"
        self.fields["members"].empty_label = "— none —"

    def _blank_to_none(self, field_name):
        """email/website/facebook/linkedin are unique; store blanks as NULL so
        multiple companies without them don't collide on the unique constraint."""
        value = self.cleaned_data.get(field_name)
        if value in ("", None):
            return None
        return value

    def clean_email(self):
        return self._blank_to_none("email")

    def clean_website(self):
        return self._blank_to_none("website")

    def clean_facebook(self):
        return self._blank_to_none("facebook")

    def clean_linkedin(self):
        return self._blank_to_none("linkedin")


# admin_panel/forms.py
from admins.models import AdminProfile


class AdminContactForm(forms.ModelForm):
    """Site-wide contact / social details shown on the public contact page."""

    class Meta:
        model = AdminProfile
        fields = [
            "name",
            "gmail",
            "phone",
            "address",
            "facebook",
            "linkedin",
            "x",
            "github",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "gmail": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "facebook": forms.URLInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "x": forms.URLInput(attrs={"class": "form-control"}),
            "github": forms.URLInput(attrs={"class": "form-control"}),
        }

        labels = {
            "gmail": "Contact email",
            "x": "X (Twitter)",
        }
