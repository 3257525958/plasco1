from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from cantact_app.models import Branch
import random


class Command(BaseCommand):
    help = 'ایجاد داده‌های تستی برای برنامه'

    def handle(self, *args, **options):
        self.stdout.write("🎯 در حال ایجاد داده‌های تستی...")

        # ایجاد کاربران
        users = [
            {'username': 'test_user1', 'password': '123456', 'email': 'test1@company.com'},
            {'username': 'test_user2', 'password': '123456', 'email': 'test2@company.com'},
        ]

        for user_data in users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'email': user_data['email']}
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f"✅ کاربر ایجاد شد: {user_data['username']}")

        # ایجاد مشتریان
        customers = [
            {'name': 'مشتری نمونه ۱', 'phone': '09121111111', 'address': 'آدرس نمونه ۱'},
            {'name': 'مشتری نمونه ۲', 'phone': '09122222222', 'address': 'آدرس نمونه ۲'},
            {'name': 'مشتری نمونه ۳', 'phone': '09123333333', 'address': 'آدرس نمونه ۳'},
        ]

        for customer_data in customers:
            customer, created = Customer.objects.get_or_create(
                name=customer_data['name'],
                defaults=customer_data
            )
            if created:
                self.stdout.write(f"✅ مشتری ایجاد شد: {customer_data['name']}")

        self.stdout.write(self.style.SUCCESS("🎉 داده‌های تستی با موفقیت ایجاد شدند!"))