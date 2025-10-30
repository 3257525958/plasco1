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

        # ایجاد شعبه پیش‌فرض - فقط با فیلدهای موجود
        try:
            branch, created = Branch.objects.get_or_create(
                name='شعبه مرکزی',
                defaults={
                    'address': 'آدرس پیش‌فرض - لطفا ویرایش کنید',
                    # فیلدهای 'is_active' و 'phone' را حذف کردیم
                }
            )
            if created:
                self.stdout.write(f'✅ شعبه پیش‌فرض ایجاد شد: {branch.name}')
            else:
                self.stdout.write(f'✅ شعبه پیش‌فرض موجود است: {branch.name}')
        except Exception as e:
            self.stdout.write(f'⚠️ خطا در ایجاد شعبه: {e}')
            # اگر باز هم خطا داد، فقط با name ایجاد کن
            try:
                branch, created = Branch.objects.get_or_create(
                    name='شعبه مرکزی'
                )
                if created:
                    self.stdout.write(f'✅ شعبه پیش‌فرض ایجاد شد (ساده): {branch.name}')
                else:
                    self.stdout.write(f'✅ شعبه پیش‌فرض موجود است: {branch.name}')
            except Exception as e2:
                self.stdout.write(f'❌ خطا در ایجاد شعبه پیش‌فرض: {e2}')

        # ایجاد فروشنده پیش‌فرض - فقط با فیلدهای موجود
        try:
            froshande, created = Froshande.objects.get_or_create(
                name='فروشنده پیش‌فرض',
                defaults={
                    'phone': '09120000000',
                    'address': 'آدرس پیش‌فرض',
                    # فیلد 'is_active' را حذف کردیم
                }
            )
            if created:
                self.stdout.write(f'✅ فروشنده پیش‌فرض ایجاد شد: {froshande.name}')
            else:
                self.stdout.write(f'✅ فروشنده پیش‌فرض موجود است: {froshande.name}')
        except Exception as e:
            self.stdout.write(f'⚠️ خطا در ایجاد فروشنده: {e}')
            # اگر باز هم خطا داد، فقط با name ایجاد کن
            try:
                froshande, created = Froshande.objects.get_or_create(
                    name='فروشنده پیش‌فرض'
                )
                if created:
                    self.stdout.write(f'✅ فروشنده پیش‌فرض ایجاد شد (ساده): {froshande.name}')
                else:
                    self.stdout.write(f'✅ فروشنده پیش‌فرض موجود است: {froshande.name}')
            except Exception as e2:
                self.stdout.write(f'❌ خطا در ایجاد فروشنده پیش‌فرض: {e2}')

        self.stdout.write('🎉 آماده‌سازی داده‌های پایه تکمیل شد')