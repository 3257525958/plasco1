# ----------------------------ادمین-----------------------------
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'is_default', 'is_active', 'created_at']
    list_filter = ['payment_type', 'is_default', 'is_active']
    search_fields = ['name', 'terminal_name', 'bank_name', 'account_owner']
    list_editable = ['is_default', 'is_active']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'payment_type', 'is_default', 'is_active')
        }),
        ('اطلاعات کارتخوان', {
            'fields': ('terminal_name', 'account_number'),
            'classes': ('collapse',),
            'description': 'این اطلاعات فقط برای روش پرداخت کارتخوان استفاده می‌شود'
        }),
        ('اطلاعات واریز به حساب', {
            'fields': ('bank_name', 'card_number', 'sheba_number', 'account_owner'),
            'classes': ('collapse',),
            'description': 'این اطلاعات فقط برای روش پرداخت واریز به حساب استفاده می‌شود'
        }),
    )

    def get_fieldsets(self, request, obj=None):
        """
        نمایش فیلدهای مربوطه بر اساس نوع پرداخت انتخاب شده
        """
        fieldsets = super().get_fieldsets(request, obj)

        if obj:
            # اگر نوع پرداخت کارتخوان است، فقط اطلاعات کارتخوان را نشان بده
            if obj.payment_type == 'card':
                return (
                    fieldsets[0],  # اطلاعات اصلی
                    fieldsets[1],  # اطلاعات کارتخوان
                )
            # اگر نوع پرداخت واریز به حساب است، فقط اطلاعات بانکی را نشان بده
            elif obj.payment_type == 'bank':
                return (
                    fieldsets[0],  # اطلاعات اصلی
                    fieldsets[2],  # اطلاعات واریز به حساب
                )
            # برای نقدی و چک فقط اطلاعات اصلی را نشان بده
            else:
                return (fieldsets[0],)

        return fieldsets

    def save_model(self, request, obj, form, change):
        """
        اعتبارسنجی و ذخیره مدل
        """
        # تمیز کردن و اعتبارسنجی مدل
        obj.clean()
        super().save_model(request, obj, form, change)

# -----------------------------فرم---------


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
                'placeholder': 'نام ترمینال کارتخوان (اختیاری)'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره حساب (اختیاری)'
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
            'terminal_name': 'نام ترمینال (اختیاری)',
            'account_number': 'شماره حساب (اختیاری)',
            'bank_name': 'نام بانک',
            'card_number': 'شماره کارت',
            'sheba_number': 'شماره شبا',
            'account_owner': 'صاحب حساب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # همه فیلدها را اختیاری می‌کنیم
        for field_name in self.fields:
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')

        # فقط برای واریز به حساب اعتبارسنجی انجام بده
        if payment_type == 'bank':
            if not cleaned_data.get('bank_name'):
                self.add_error('bank_name', 'برای روش پرداخت واریز به حساب، نام بانک الزامی است')
            if not cleaned_data.get('account_number'):
                self.add_error('account_number', 'برای روش پرداخت واریز به حساب، شماره حساب الزامی است')
            if not cleaned_data.get('sheba_number'):
                self.add_error('sheba_number', 'برای روش پرداخت واریز به حساب، شماره شبا الزامی است')
            if not cleaned_data.get('account_owner'):
                self.add_error('account_owner', 'برای روش پرداخت واریز به حساب، نام صاحب حساب الزامی است')

        return cleaned_data







# -------------------view----------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.core.exceptions import ValidationError
import json

from .models import PaymentMethod
from .forms import PaymentMethodForm


def payment_method_list(request):
    payment_methods = PaymentMethod.objects.all()
    return render(request, 'payment_method_list.html', {
        'payment_methods': payment_methods
    })


def payment_method_create(request):
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save()
            messages.success(request, f'روش پرداخت "{payment_method.name}" با موفقیت ایجاد شد')
            return redirect('account_app:payment_method_list')
    else:
        form = PaymentMethodForm()

    return render(request, 'payment_method_form.html', {
        'form': form,
        'title': 'ایجاد روش پرداخت جدید'
    })


def payment_method_update(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=payment_method)
        if form.is_valid():
            payment_method = form.save()
            messages.success(request, f'روش پرداخت "{payment_method.name}" با موفقیت بروزرسانی شد')
            return redirect('account_app:payment_method_list')
    else:
        form = PaymentMethodForm(instance=payment_method)

    return render(request, 'payment_method_form.html', {
        'form': form,
        'title': 'ویرایش روش پرداخت',
        'payment_method': payment_method
    })


def payment_method_delete(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)

    if request.method == 'POST':
        method_name = payment_method.name
        payment_method.delete()
        messages.success(request, f'روش پرداخت "{method_name}" با موفقیت حذف شد')
        return redirect('account_app:payment_method_list')

    return render(request, 'payment_method_confirm_delete.html', {
        'payment_method': payment_method
    })


def payment_method_toggle_active(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    payment_method.is_active = not payment_method.is_active
    payment_method.save()

    action = "فعال" if payment_method.is_active else "غیرفعال"
    messages.success(request, f'روش پرداخت "{payment_method.name}" {action} شد')

    return redirect('account_app:payment_method_list')


def set_default_payment_method(request, pk):
    payment_method = get_object_or_404(PaymentMethod, pk=pk)

    # تمام روش‌ها را از حالت پیش فرض خارج کن
    PaymentMethod.objects.filter(is_default=True).update(is_default=False)

    # این روش را به پیش فرض تبدیل کن
    payment_method.is_default = True
    payment_method.save()

    messages.success(request, f'روش پرداخت "{payment_method.name}" به عنوان پیش فرض تنظیم شد')

    return redirect('account_app:payment_method_list')


def check_auth_status(request):
    return JsonResponse({
        'is_authenticated': False,  # همیشه false چون احراز هویت غیرفعال است
        'username': None,
        'session_key': request.session.session_key,
    })


def session_test(request):
    request.session['test_key'] = 'test_value'
    test_value = request.session.get('test_key', 'not_set')
    return HttpResponse(f"Session test: {test_value}")


