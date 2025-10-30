# sync_app/management/commands/setup_basic_data.py
from django.core.management.base import BaseCommand
from cantact_app.models import Branch
from dashbord_app.models import Froshande
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'آماده‌سازی داده‌های پایه برای سینک'

    def handle(self, *args, **options):
        self.stdout.write('🚀 شروع آماده‌سازی داده‌های پایه...')

        # ایجاد کاربر پیش‌فرض اگر وجود ندارد
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'مدیر',
                'last_name': 'سیستم',
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write('✅ کاربر پیش‌فرض ایجاد شد')
        else:
            self.stdout.write('✅ کاربر پیش‌فرض موجود است')

        # ایجاد شعبه پیش‌فرض
        branch, created = Branch.objects.get_or_create(
            name='شعبه مرکزی',
            defaults={
                'address': 'آدرس پیش‌فرض - لطفا ویرایش کنید',
                'phone': '02100000000',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✅ شعبه پیش‌فرض ایجاد شد: {branch.name}')
        else:
            self.stdout.write(f'✅ شعبه پیش‌فرض موجود است: {branch.name}')

        # ایجاد فروشنده پیش‌فرض
        froshande, created = Froshande.objects.get_or_create(
            name='فروشنده پیش‌فرض',
            defaults={
                'phone': '09120000000',
                'address': 'آدرس پیش‌فرض',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'✅ فروشنده پیش‌فرض ایجاد شد: {froshande.name}')
        else:
            self.stdout.write(f'✅ فروشنده پیش‌فرض موجود است: {froshande.name}')

        self.stdout.write('🎉 آماده‌سازی داده‌های پایه تکمیل شد')