import socket
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import struct


def payment_page(request):
    """صفحه اصلی پرداخت"""
    return render(request, 'payment.html')


@csrf_exempt
def send_amount_to_pos(request):
    """ارسال مبلغ به دستگاه پوز"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            prcode = data.get('prcode', '000000')

            if not amount:
                return JsonResponse({
                    'status': 'error',
                    'message': 'لطفا مبلغ را وارد کنید'
                })

            # تنظیمات دستگاه پوز
            POS_IP = '87.107.134.151'
            POS_PORT = 4080

            # ساخت داده TLV
            tlv_data = build_tlv_data(amount, prcode)

            # ارسال به دستگاه پوز
            response_data = send_tcp_data(tlv_data, POS_IP, POS_PORT)

            # پردازش پاسخ
            parsed_response = parse_pos_response(response_data)

            return JsonResponse({
                'status': 'success',
                'message': 'تراکنش با موفقیت ارسال شد',
                'raw_response': response_data,
                'parsed_response': parsed_response
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در ارسال به دستگاه پوز: {str(e)}'
            })

    return JsonResponse({'status': 'invalid_method'})


def build_tlv_data(amount, prcode):
    """ساخت داده TLV بر اساس پروتکل دستگاه پوز"""

    # تبدیل مبلغ به فرمت 12 رقمی
    amount_padded = amount.zfill(12)

    # ساختار TLV بر اساس برنامه C#
    tlv_parts = []

    # PR - کد پرداخت (6 کاراکتر)
    tlv_parts.append(f"PR{len(prcode):02d}{prcode}")

    # AM - مبلغ (12 کاراکتر)
    tlv_parts.append(f"AM{len(amount_padded):02d}{amount_padded}")

    # CU - کد ارز (3 کاراکتر)
    currency_code = "364"
    tlv_parts.append(f"CU{len(currency_code):02d}{currency_code}")

    # R1 - رسید دارنده کارت (اختیاری)
    card_receipt = "پرداخت فروشگاه"
    tlv_parts.append(f"R1{len(card_receipt):02d}{card_receipt}")

    # R2 - رسید پذیرنده (اختیاری)
    merchant_receipt = "پرداخت نوین"
    tlv_parts.append(f"R2{len(merchant_receipt):02d}{merchant_receipt}")

    # T1 - عنوان دارنده کارت (اختیاری)
    card_title = "مشتری"
    tlv_parts.append(f"T1{len(card_title):02d}{card_title}")

    # T2 - عنوان پذیرنده (اختیاری)
    merchant_title = "فروشگاه"
    tlv_parts.append(f"T2{len(merchant_title):02d}{merchant_title}")

    # IBAN1 و Amount1 (برای پرداخت چندحسابی)
    iban1 = "IR680540102330100402176602"
    amount1 = amount_padded
    tlv_parts.append(f"A1{len(amount1):02d}{amount1}")
    tlv_parts.append(f"ID1{len(iban1):02d}{iban1}")

    # D1 - شناسه پرداخت
    payment_id1 = "2296387756"
    tlv_parts.append(f"D1{len(payment_id1):02d}{payment_id1}")

    # جمع آوری تمام بخش‌ها
    tlv_string = "".join(tlv_parts)

    # اضافه کردن طول کل در ابتدا (بر اساس نمونه C#)
    total_length = len(tlv_string)
    final_data = f"RQ{total_length:04d}{tlv_string}"

    return final_data.encode('utf-8')


def send_tcp_data(data, ip, port):
    """ارسال داده via TCP به دستگاه پوز"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(30)
            sock.connect((ip, port))

            # ارسال داده
            sock.sendall(data)

            # دریافت پاسخ
            response = b""
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk

            return response.decode('utf-8', errors='ignore')

    except socket.timeout:
        raise Exception("تایم‌اوت اتصال - دستگاه پاسخ نمی‌دهد")
    except ConnectionResetError:
        raise Exception("دستگاه ارتباط را قطع کرد")
    except socket.error as e:
        raise Exception(f"خطای ارتباط: {str(e)}")


def parse_pos_response(response):
    """تجزیه و تحلیل پاسخ دستگاه پوز"""
    if not response:
        return "پاسخ خالی از دستگاه"

    # کدهای خطا بر اساس مستندات صفحه 7
    error_codes = {
        '12': 'تراکنش ناموفق',
        '50': 'مبلغ تراکنش با مبلغ مجاز',
        '51': 'موجودی کافی نیست',
        '54': 'کارت منقضی شده است',
        '55': 'رمز کارت اشتباه است',
        '56': 'کارت نامعتبر است',
        '58': 'امکان پذیرش تراکنش وجود ندارد',
        '61': 'مبلغ تراکنش بیش از حد مجاز',
        '65': 'تعداد دفعات مجاز ورود رمز اشتباه',
        '99': 'خطای سوییچ'
    }

    # تجزیه پاسخ (ساده شده)
    parsed = {
        'raw': response,
        'status': 'unknown',
        'message': 'در حال پردازش...'
    }

    # بررسی کد خطا در پاسخ
    for code, message in error_codes.items():
        if code in response:
            parsed['status'] = 'error'
            parsed['message'] = message
            break
    else:
        if '00' in response or 'success' in response.lower():
            parsed['status'] = 'success'
            parsed['message'] = 'تراکنش موفق'

    return parsed


@csrf_exempt
def test_connection(request):
    """تست ارتباط با دستگاه پوز"""
    try:
        POS_IP = '87.107.134.151'
        POS_PORT = 4080

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((POS_IP, POS_PORT))

            return JsonResponse({
                'status': 'success',
                'message': 'ارتباط با دستگاه پوز برقرار شد'
            })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'خطا در ارتباط با دستگاه پوز: {str(e)}'
        })