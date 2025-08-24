from django import forms
from cantact_app.models import accuntmodel

# class accuntform(forms.ModelForm):
#     class Meta:
#         model = accuntmodel
#         exclude = ('firstname','lastname','melicode','phonnumber','berthday'),
        # labels = {
        #     "imageuser" : ('عکسی برای پروفایل خودتان انتخاب کنید'),
        # }
        # widgets = {
        #     "imageuser" : forms.Textarea(attrs = { "class":"box",}),
        # }
class accuntform(forms.ModelForm):
    class Meta:
        model = accuntmodel
        fields = '__all__'  # یا فیلدهای مورد نیاز را مشخص کنید
        widgets = {
            'profile_picture': forms.FileInput(attrs={'accept': 'image/*'})
        }