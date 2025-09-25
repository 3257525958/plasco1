
from django import forms
from account_app.models import Branch
from .models import POSDevice, CheckPayment, CreditPayment

class BranchSelectionForm(forms.Form):
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        empty_label="شعبه را انتخاب کنید",
        label="شعبه",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class POSDeviceForm(forms.ModelForm):
    class Meta:
        model = POSDevice
        fields = ['name', 'account_holder', 'card_number', 'account_number', 'bank_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام دستگاه'}),
            'account_holder': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام صاحب حساب'}),
            'card_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره کارت (16 رقم)'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره حساب'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام بانک'}),
        }

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        if card_number and (len(card_number) != 16 or not card_number.isdigit()):
            raise forms.ValidationError('شماره کارت باید 16 رقم باشد')
        return card_number

class CheckPaymentForm(forms.ModelForm):
    class Meta:
        model = CheckPayment
        fields = ['owner_name', 'owner_family', 'national_id', 'address', 'phone', 'check_number', 'amount', 'check_date']
        widgets = {
            'check_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'owner_family': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن'}),
            'check_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره چک'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس'}),
        }

class CreditPaymentForm(forms.ModelForm):
    class Meta:
        model = CreditPayment
        fields = ['customer_name', 'customer_family', 'phone', 'address', 'national_id', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'customer_family': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس'}),
        }

class DiscountForm(forms.Form):
    discount = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مبلغ تخفیف'})
    )

