from django import forms
from .models import Froshande

class FroshandeForm(forms.ModelForm):
    class Meta:
        model = Froshande
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
            'family': forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
            'mobile': forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
            'sheba_number': forms.TextInput(attrs={'class': 'validate', 'required': 'required'}),
        }
        labels = {
            'name': 'نام',
            'family': 'نام خانوادگی',
            'address': 'آدرس',
            'store_name': 'اسم فروشگاه',
            'card_number': 'شماره کارت',
            'sheba_number': 'شماره شبا',
            'phone': 'تلفن ثابت',
            'mobile': 'تلفن همراه',
        }
        error_messages = {
            'mobile': {
                'unique': "این شماره موبایل قبلا ثبت شده است"
            },
            'sheba_number': {
                'unique': "این شماره شبا قبلا ثبت شده است"
            }
        }


from django import forms
from .models import Invoice

class InvoiceEditForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['seller', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'seller': 'فروشنده',
            'date': 'تاریخ فاکتور',
        }



# --------------فروشنده----------------------------------

from django import forms
from .models import Froshande, ContactNumber, BankAccount
import re


class PersianTextValidator:
    def __call__(self, value):
        if not re.match(r'^[\u0600-\u06FF\s]+$', value):
            raise forms.ValidationError('لطفاً فقط از حروف فارسی استفاده کنید.')


class FroshandeForm(forms.ModelForm):
    name = forms.CharField(
        validators=[PersianTextValidator()],
        widget=forms.TextInput(attrs={'placeholder': 'نام'})
    )
    family = forms.CharField(
        validators=[PersianTextValidator()],
        widget=forms.TextInput(attrs={'placeholder': 'نام خانوادگی'})
    )
    store_name = forms.CharField(
        required=False,
        validators=[PersianTextValidator()],
        widget=forms.TextInput(attrs={'placeholder': 'اسم فروشگاه'})
    )

    class Meta:
        model = Froshande
        fields = ['name', 'family', 'store_name', 'address']


class ContactNumberForm(forms.ModelForm):
    class Meta:
        model = ContactNumber
        fields = ['contact_type', 'number', 'is_primary']


class BankAccountForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'bank_name', 'card_number', 'sheba_number', 'is_primary']