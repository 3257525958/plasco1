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


def receive_full_response(sock, timeout=30):
    """دریافت کامل پاسخ از سوکت با مدیریت timeout"""
    print("⏳ شروع دریافت پاسخ از دستگاه پوز...")

    sock.settimeout(timeout)
    response = b""
    start_time = time.time()

    try:
        while True:
            try:
                chunk = sock.recv(1024)
                if chunk:
                    response += chunk
                    print(f"📥 دریافت بسته داده: {len(chunk)} بایت")
                    print(f"📋 محتوای بسته: {chunk}")
                    print(f"🔢 HEX بسته: {chunk.hex()}")

                    # اگر داده کم دریافت شد یا timeout کوچک باشد، منتظر داده بیشتر می‌مانیم
                    if len(chunk) < 1024:
                        # کمی صبر می‌کنیم تا اگر داده دیگری هست دریافت شود
                        time.sleep(0.5)
                        sock.settimeout(2)  # timeout کوتاه برای بررسی داده‌های باقیمانده
                        try:
                            continue
                        except socket.timeout:
                            break
                else:
                    break
            except socket.timeout:
                print("⏰ timeout در دریافت داده - احتمالاً پاسخ کامل دریافت شده")
                break
            except Exception as e:
                print(f"❌ خطا در دریافت داده: {e}")
                break

    except Exception as e:
        print(f"❌ خطای کلی در دریافت پاسخ: {e}")

    end_time = time.time()
    print(f"✅ دریافت پاسخ کامل در {end_time - start_time:.2f} ثانیه")
    return response


def get_transaction_status(response_length, response_text):
    """تعیین وضعیت تراکنش بر اساس طول پیام پاسخ"""
    print(f"🔍 تحلیل وضعیت تراکنش - طول پاسخ: {response_length}")

    # اگر پاسخی دریافت نشده باشد
    if response_length == 0:
        return "⚠️ هیچ پاسخی از دستگاه پوز دریافت نشد. ممکن است تراکنش در حال پردازش باشد یا ارتباط قطع شده است."

    # استخراج طول پیام از 4 کاراکتر اول (در صورت موجود بودن)
    length_part = ""
    if response_text and len(response_text) >= 4:
        length_part = response_text[:4]
        print(f"📏 طول پیام از 4 کاراکتر اول: {length_part}")

    # تشخیص وضعیت بر اساس طول پیام
    status_info = {
        'length': response_length,
        'length_part': length_part,
        'message': '',
        'status_type': 'unknown'
    }

    # تشخیص بر اساس طول پیام
    if response_length == 130:  # 0130 به صورت دهدهی
        status_info['message'] = "✅ پرداخت موفق بود - تراکنش با موفقیت انجام شد"
        status_info['status_type'] = 'success'
    elif response_length == 29:  # 0029 به صورت دهدهی
        status_info['message'] = "❌ رمز کارت اشتباه بود - لطفا مجدداً تلاش کنید"
        status_info['status_type'] = 'error'
    elif response_length == 24:  # 0018 به صورت دهدهی؟ بررسی کنید
        status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
        status_info['status_type'] = 'cancelled'
    elif response_length == 18:  # 0018 به صورت دهدهی
        status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
        status_info['status_type'] = 'cancelled'
    else:
        # اگر طول شناخته شده نبود، بر اساس length_part چک می‌کنیم
        if length_part == "0130":
            status_info['message'] = "✅ پرداخت موفق بود - تراکنش با موفقیت انجام شد"
            status_info['status_type'] = 'success'
        elif length_part == "0029":
            status_info['message'] = "❌ رمز کارت اشتباه بود - لطفا مجدداً تلاش کنید"
            status_info['status_type'] = 'error'
        elif length_part == "0018":
            status_info['message'] = "⚠️ پرداخت کنسل شد - کاربر عملیات را لغو کرد"
            status_info['status_type'] = 'cancelled'
        else:
            status_info['message'] = f"🔍 وضعیت نامشخص - طول پاسخ: {response_length}, کد: {length_part}"
            status_info['status_type'] = 'unknown'

    print(f"📋 نتیجه تحلیل: {status_info['message']}")
    return status_info


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

        print(f"🔌 درخواست بررسی اتصال به {ip}:{port}")

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
            message = f'اتصال با دستگاه پوز در {ip}:{port} برقرار شد'
            print(f"✅ {message}")
            return JsonResponse({
                'status': 'success',
                'message': message
            })
        else:
            message = f'اتصال با دستگاه پوز در {ip}:{port} برقرار نشد - کد خطا: {result}'
            print(f"❌ {message}")
            return JsonResponse({
                'status': 'error',
                'message': message
            })

    except Exception as e:
        error_message = f'خطا در بررسی اتصال: {str(e)}'
        print(f"❌ {error_message}")
        return JsonResponse({
            'status': 'error',
            'message': error_message
        })


# ==================== ارسال تراکنش ====================
@csrf_exempt
@require_http_methods(["POST"])
def send_transaction(request):
    """ارسال تراکنش با فرمت 12 رقمی و دریافت پاسخ"""
    try:
        data = json.loads(request.body)
        ip = data.get('ip', '').strip()
        port = int(data.get('port', 1362))
        amount = data.get('amount', '1000')

        print(f"💰 شروع تراکنش برای مبلغ: {amount} ریال")
        print(f"📍 آدرس دستگاه: {ip}:{port}")

        if not ip:
            return JsonResponse({'status': 'error', 'message': 'آدرس IP نمی‌تواند خالی باشد'})

        ip = normalize_ip(ip)
        if not is_valid_ip(ip):
            return JsonResponse({'status': 'error', 'message': 'آدرس IP معتبر نیست'})

        # ساخت پیام با فرمت 12 رقمی
        message = build_sale_request(amount)

        print(f"📤 ارسال پیام به دستگاه پوز...")

        # ارسال به دستگاه
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)
        sock.connect((ip, port))

        # ارسال پیام
        bytes_sent = sock.send(message.encode('ascii'))
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # دریافت پاسخ
        print("⏳ منتظر پاسخ از دستگاه پوز...")
        response = receive_full_response(sock, timeout=30)

        sock.close()

        # تحلیل پاسخ
        response_text = ""
        response_hex = ""

        if response:
            response_text = response.decode('ascii', errors='ignore')
            response_hex = response.hex()

            print(f"📥 پاسخ کامل دریافت شد:")
            print(f"📏 طول پاسخ: {len(response)} بایت")
            print(f"📝 محتوای متنی: {response_text}")
            print(f"🔢 محتوای HEX: {response_hex}")

        else:
            print("⚠️ هیچ پاسخی از دستگاه دریافت نشد")

        # تحلیل وضعیت تراکنش بر اساس طول پیام
        status_info = get_transaction_status(len(response), response_text)

        # ساخت پیام برای نمایش به کاربر
        alert_message = f"وضعیت تراکنش:\n\n{status_info['message']}\n\n"
        alert_message += f"مبلغ: {amount} ریال\n"
        alert_message += f"طول پیام پاسخ: {status_info['length']} بایت\n"

        if status_info['length_part']:
            alert_message += f"کد وضعیت: {status_info['length_part']}"

        return JsonResponse({
            'status': 'success',
            'message': f'تراکنش {amount} ریال ارسال شد',
            'alert_message': alert_message,
            'transaction_status': status_info,
            'response_data': {
                'raw_response': response_text,
                'hex_response': response_hex,
                'response_length': len(response),
                'length_part': status_info['length_part']
            },
            'debug': {
                'message_sent': message,
                'bytes_sent': bytes_sent,
                'note': 'پاسخ کامل از دستگاه دریافت و تحلیل شد'
            }
        })

    except socket.timeout as e:
        error_message = f'خطا: timeout - دستگاه پوز پاسخ نداد: {str(e)}'
        print(f"❌ {error_message}")
        return JsonResponse({
            'status': 'error',
            'message': 'تراکنش ارسال شد اما پاسخی دریافت نشد',
            'alert_message': error_message
        })

    except ConnectionRefusedError as e:
        error_message = f'خطا: Connection refused - پورت باز نیست: {str(e)}'
        print(f"❌ {error_message}")
        return JsonResponse({
            'status': 'error',
            'message': 'اتصال به دستگاه برقرار نشد',
            'alert_message': error_message
        })

    except Exception as e:
        error_message = f'خطا در ارسال تراکنش: {str(e)}'
        print(f"❌ {error_message}")
        return JsonResponse({
            'status': 'error',
            'message': 'خطا در ارسال تراکنش',
            'alert_message': error_message
        })