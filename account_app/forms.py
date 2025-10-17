from django import forms
from .models import PaymentMethod

from django import forms

from django import forms
from .models import PaymentMethod


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = [
            'name', 'payment_type', 'is_default', 'is_active',
            'terminal_name', 'account_number', 'bank_name',
            'card_number', 'sheba_number', 'account_owner'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام روش پرداخت را وارد کنید'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'togglePaymentFields()'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'terminal_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام ترمینال کارتخوان'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره حساب'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام بانک'
            }),
            'card_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '6037XXXXXXXXXXXX'
            }),
            'sheba_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IRXXXXXXXXXXXXXXXXXXXXXXXX'
            }),
            'account_owner': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام صاحب حساب'
            }),
        }
        labels = {
            'name': 'نام روش پرداخت',
            'payment_type': 'نوع پرداخت',
            'is_default': 'پیش فرض',
            'is_active': 'فعال',
            'terminal_name': 'نام ترمینال',
            'account_number': 'شماره حساب',
            'bank_name': 'نام بانک',
            'card_number': 'شماره کارت',
            'sheba_number': 'شماره شبا',
            'account_owner': 'صاحب حساب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظیمات اضافی برای فیلدها
        self.fields['card_number'].required = False
        self.fields['sheba_number'].required = False
        self.fields['account_owner'].required = False
        self.fields['terminal_name'].required = False
        self.fields['bank_name'].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')

        # اعتبارسنجی شرطی بر اساس نوع پرداخت
        if payment_type == 'card':
            if not cleaned_data.get('terminal_name'):
                self.add_error('terminal_name', 'برای روش پرداخت کارتخوان، نام ترمینال الزامی است')
            if not cleaned_data.get('account_number'):
                self.add_error('account_number', 'برای روش پرداخت کارتخوان، شماره حساب الزامی است')

        elif payment_type == 'bank':
            if not cleaned_data.get('bank_name'):
                self.add_error('bank_name', 'برای روش پرداخت واریز به حساب، نام بانک الزامی است')
            if not cleaned_data.get('account_number'):
                self.add_error('account_number', 'برای روش پرداخت واریز به حساب، شماره حساب الزامی است')
            if not cleaned_data.get('sheba_number'):
                self.add_error('sheba_number', 'برای روش پرداخت واریز به حساب، شماره شبا الزامی است')
            if not cleaned_data.get('account_owner'):
                self.add_error('account_owner', 'برای روش پرداخت واریز به حساب، نام صاحب حساب الزامی است')

        return cleaned_data

# ----------------------ثبت هزینه ها----------------------------------------------------------------------------
from django import forms
from .models import Expense, ExpenseImage
from cantact_app.models import Branch


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ExpenseForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        label='عکس‌های فاکتور (اختیاری)'
    )

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'branch']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'شرح کامل هزینه را وارد کنید...'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'مبلغ به تومان'
            }),
            'branch': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'description': 'شرح هزینه *',
            'amount': 'مبلغ هزینه (تومان) *',
            'branch': 'شعبه *'
        }