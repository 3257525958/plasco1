from django import forms
from account_app.models import Branch, PaymentMethod

class BranchSelectionForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        empty_label="شعبه را انتخاب کنید",
        label="شعبه"
    )

class PaymentMethodForm(forms.Form):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        empty_label="روش پرداخت را انتخاب کنید",
        label="روش پرداخت"
    )