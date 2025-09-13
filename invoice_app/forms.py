from django import forms
from account_app.models import Branch

class BranchSelectionForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        empty_label="شعبه را انتخاب کنید",
        label="شعبه",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
class ProductSearchForm(forms.Form):
    product_query = forms.CharField(
        max_length=100,
        label="جستجوی کالا (نام یا بارکد)"
    )

from django import forms
from account_app.models import Branch, PaymentMethod

class BranchSelectionForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        empty_label="شعبه را انتخاب کنید",
        label="شعبه",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class PaymentMethodForm(forms.Form):
    payment_method = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.filter(is_active=True),
        empty_label=None,
        label="روش پرداخت",
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        initial=PaymentMethod.objects.filter(is_default=True, is_active=True).first
    )