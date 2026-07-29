from django import forms
from .models import UserKYC, ID_TYPE_CHOICES


class KYCSubmitForm(forms.ModelForm):
    """Freelancer-facing identity submission: one government photo ID + a selfie."""

    class Meta:
        model = UserKYC
        fields = ["id_type", "id_number", "id_document", "selfie"]
        widgets = {
            "id_type": forms.Select(),
            "id_number": forms.TextInput(attrs={"placeholder": "Number on your ID"}),
            "id_document": forms.ClearableFileInput(attrs={"accept": "image/*,application/pdf"}),
            "selfie": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show a friendly placeholder instead of Django's default "---------".
        self.fields["id_type"].choices = [("", "Select ID type")] + list(ID_TYPE_CHOICES)
        self.fields["id_type"].required = True

    def clean(self):
        cleaned = super().clean()
        # On first submission both files are required; on resubmit keep existing if unchanged.
        if not (cleaned.get("id_document") or (self.instance and self.instance.id_document)):
            self.add_error("id_document", "Please upload a photo of your ID.")
        if not (cleaned.get("selfie") or (self.instance and self.instance.selfie)):
            self.add_error("selfie", "Please upload a selfie.")
        return cleaned
