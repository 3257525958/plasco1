
# pos_payment/views.py
import socket
import json
import re
import time
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


# ==================== توابع کمکی ====================
def is_valid_ip(ip):
    """بررسی معتبر بودن آدرس IP"""
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    if not re.match(pattern, ip):
        return False
    parts = ip.split('.')
    for part in parts:
        if not 0 <= int(part) <= 255:
            return False
    return True


def normalize_ip(ip):
    """نرمال کردن آدرس IP"""
    parts = ip.split('.')
    normalized_parts = [str(int(part)) for part in parts]
    return '.'.join(normalized_parts)


# ==================== ویوهای اصلی ====================
def pos_payment_page(request):
    """صفحه اصلی"""
    return render(request, 'pos_payment.html')


@csrf_exempt
@require_http_methods(["POST"])
def check_connection(request):
    """بررسی اتصال به دستگاه پوز"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()

        if result == 0:
            return JsonResponse({
                'status': 'success',
                'message': f'اتصال با دستگاه پوز در {ip}:{port} برقرار شد'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'اتصال با دستگاه پوز در {ip}:{port} برقرار نشد - کد خطا: {result}'
            })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در بررسی اتصال: {str(e)}'
        })


# ==================== توابع ساخت پیام ====================
def build_sale_request(amount):
    """ساخت پیام با فرمت 12 رقمی استاندارد"""
    print(f"🔨 ساخت پیام برای مبلغ: {amount}")

    # تبدیل به 12 رقم با صفرهای ابتدایی
    amount_12_digit = str(amount).zfill(12)
    print(f"💰 مبلغ 12 رقمی: {amount_12_digit}")

    # استفاده از فرمت 12 رقمی استاندارد
    message = f"0047RQ034PR006000000AM012{amount_12_digit}CU003364PD0011"

    print(f"📦 پیام نهایی: {message}")
    print(f"📏 طول: {len(message)}")
    print(f"🔢 HEX: {message.encode('ascii').hex()}")

    return message


# ==================== ارسال تراکنش ====================
@csrf_exempt
@require_http_methods(["POST"])
def send_transaction(request):
    """ارسال تراکنش با فرمت 12 رقمی"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))
        amount = data.get('amount', '1000')

        print(f"💰 ارسال تراکنش برای مبلغ: {amount}")

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        # ساخت پیام با فرمت 12 رقمی
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه...")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((ip, port))
        bytes_sent = sock.send(message.encode('ascii'))

        print(f"✅ {bytes_sent} بایت ارسال شد")
        time.sleep(3)

        response = b""
        try:
            response = sock.recv(1024)
            if response:
                print(f"📥 پاسخ دریافت شد: {len(response)} بایت")
                print(f"📋 محتوای پاسخ: {response.decode('ascii', errors='ignore')}")
        except socket.timeout:
            print("⏰ timeout در دریافت پاسخ")

        sock.close()

        response_text = response.decode('ascii', errors='ignore') if response else ""

        return JsonResponse({
            'status': 'success',
            'message': f'تراکنش {amount} ریال ارسال شد',
            'on_pos': 'مبلغ باید روی پوز نمایش داده شود',
            'debug': {
                'message_sent': message,
                'response': response_text,
                'bytes_sent': bytes_sent,
                'note': 'استفاده از فرمت 12 رقمی استاندارد'
            }
        })

    except Exception as e:
        print(f"❌ خطا: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در ارسال تراکنش: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def send_large_amount(request):
    """ارسال مستقیم مبالغ بزرگ"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))
        amount = data.get('amount', '1000000000')

        print(f"🚀 ارسال مبلغ بزرگ: {amount} ریال")

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        # ساخت پیام با فرمت 12 رقمی
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه...")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((ip, port))
        bytes_sent = sock.send(message.encode('ascii'))

        print(f"✅ {bytes_sent} بایت ارسال شد")
        time.sleep(3)

        response = b""
        try:
            response = sock.recv(1024)
            if response:
                print(f"📥 پاسخ دریافت شد: {len(response)} بایت")
        except socket.timeout:
            print("⏰ timeout در دریافت پاسخ")

        sock.close()

        response_text = response.decode('ascii', errors='ignore') if response else ""

        # فرمت کردن مبلغ برای نمایش
        formatted_amount = f"{int(amount):,}"

        return JsonResponse({
            'status': 'success',
            'message': f'تراکنش {formatted_amount} ریال ارسال شد',
            'on_pos': f'عدد {formatted_amount} باید روی پوز نمایش داده شود',
            'debug': {
                'message_sent': message,
                'response': response_text,
                'bytes_sent': bytes_sent
            }
        })

    except Exception as e:
        print(f"❌ خطا: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در ارسال تراکنش: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def send_200_billion(request):
    """ارسال مستقیم 200 میلیارد ریال"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))

        print("💎 ارسال 200 میلیارد ریال")

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        amount = "200000000000"  # 200 میلیارد ریال
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه...")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((ip, port))
        bytes_sent = sock.send(message.encode('ascii'))

        print(f"✅ {bytes_sent} بایت ارسال شد")
        time.sleep(3)

        response = b""
        try:
            response = sock.recv(1024)
            if response:
                print(f"📥 پاسخ دریافت شد: {len(response)} بایت")
        except socket.timeout:
            print("⏰ timeout در دریافت پاسخ")

        sock.close()

        response_text = response.decode('ascii', errors='ignore') if response else ""

        return JsonResponse({
            'status': 'success',
            'message': 'تراکنش 200,000,000,000 ریال ارسال شد',
            'on_pos': 'عدد 200,000,000,000 باید روی پوز نمایش داده شود',
            'debug': {
                'message_sent': message,
                'response': response_text,
                'bytes_sent': bytes_sent
            }
        })

    except Exception as e:
        print(f"❌ خطا: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در ارسال تراکنش: {str(e)}'
        })


# ==================== تست‌های مختلف ====================
@csrf_exempt
def test_api(request):
    """تست ساده API"""
    return JsonResponse({
        'status': 'success',
        'message': 'API درست کار می‌کند!',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    })


@csrf_exempt
@require_http_methods(["POST"])
def test_protocols(request):
    """تست پروتکل‌های مختلف"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))

        results = []

        # تست‌های ساده
        test_messages = [
            ("TEST", "پیام ساده TEST"),
            ("ECHO", "پیام ECHO"),
            ("0039RQ034PR006000000AM0041000CU003364PD0011", "TLV خرید 1000 ریال"),
            ("0047RQ034PR006000000AM012200000000000CU003364PD0011", "TLV خرید 200 میلیارد ریال")
        ]

        for message, description in test_messages:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((ip, port))
                sock.send(message.encode('ascii'))
                time.sleep(2)
                response = sock.recv(1024)
                sock.close()

                results.append({
                    "protocol": description,
                    "result": f"✅ موفق - پاسخ: {response.decode('ascii', errors='ignore')[:50] if response else 'بدون پاسخ'}"
                })
            except Exception as e:
                results.append({
                    "protocol": description,
                    "result": f"❌ خطا: {str(e)}"
                })

        return JsonResponse({
            'status': 'success',
            'message': 'تست پروتکل‌ها کامل شد',
            'results': results
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در تست پروتکل‌ها: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def test_amounts(request):
    """تست مبالغ مختلف"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))

        print("🧪 تست مبالغ مختلف")

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        # تست مبالغ مختلف
        test_amounts = [
            ("1000", "1,000 ریال"),
            ("10000", "10,000 ریال"),
            ("100000", "100,000 ریال"),
            ("1000000", "1,000,000 ریال"),
            ("10000000", "10,000,000 ریال"),
            ("100000000", "100,000,000 ریال"),
            ("1000000000", "1,000,000,000 ریال"),
            ("200000000000", "200,000,000,000 ریال")
        ]

        results = []

        for amount, description in test_amounts:
            try:
                message = build_sale_request(amount)

                print(f"🧪 تست {description}")

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(30)
                sock.connect((ip, port))
                bytes_sent = sock.send(message.encode('ascii'))
                time.sleep(3)

                response = b""
                try:
                    response = sock.recv(1024)
                except socket.timeout:
                    pass

                sock.close()

                results.append({
                    'amount': description,
                    'status': 'success',
                    'bytes_sent': bytes_sent,
                    'response_length': len(response)
                })

                print(f"✅ {description}: ارسال موفق")

            except Exception as e:
                results.append({
                    'amount': description,
                    'status': 'error',
                    'bytes_sent': 0,
                    'response': f'خطا: {str(e)}'
                })
                print(f"❌ {description}: {e}")

        return JsonResponse({
            'status': 'success',
            'message': 'تست مبالغ مختلف کامل شد',
            'results': results
        })

    except Exception as e:
        print(f"❌ خطا در تست مبالغ: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در تست مبالغ: {str(e)}'
        })
    