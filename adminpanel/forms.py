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

class AdminPlanFeatureForm(forms.ModelForm):
    class Meta:
        model = PlanFeature
        fields = ["feature_name", "is_boolean", "limit"]

        widgets = {
            "feature_name": forms.TextInput(attrs={"class": "form-control"}),
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
