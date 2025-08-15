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