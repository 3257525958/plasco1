from django import forms
from .models import Branch, BranchAdmin


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'address', 'sellers']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شعبه'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'آدرس شعبه'}),
            'sellers': forms.SelectMultiple(attrs={'class': 'form-control d-none', 'id': 'selected-sellers'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sellers'].required = False

    def clean_sellers(self):
        # اطمینان از اینکه sellers همیشه یک لیست است
        sellers = self.cleaned_data.get('sellers')
        if isinstance(sellers, str):
            # اگر sellers یک رشته است، آن را به لیست تبدیل کنید
            try:
                sellers = [int(seller_id) for seller_id in sellers.split(',') if seller_id.strip()]
            except ValueError:
                raise forms.ValidationError('فرمت داده فروشندگان نامعتبر است.')
        return sellers


class BranchAdminForm(forms.ModelForm):
    class Meta:
        model = BranchAdmin
        fields = ['branch', 'admin_user']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'admin_user': forms.Select(attrs={'class': 'form-control'}),
        }