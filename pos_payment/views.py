# pos_payment/views.py
import socket
import json
import re
import time
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


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
    """حذف صفرهای ابتدایی از آدرس IP"""
    parts = ip.split('.')
    normalized_parts = [str(int(part)) for part in parts]
    return '.'.join(normalized_parts)


def pos_payment_page(request):
    return render(request, 'pos_payment.html')


@csrf_exempt
def check_connection(request):
    """بررسی اتصال به دستگاه پوز"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip', '').strip()
            port = int(data.get('port', 1362))

            # اعتبارسنجی IP
            if not ip:
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP نمی‌تواند خالی باشد'
                })

            # نرمال کردن IP (حذف صفرهای ابتدایی)
            try:
                ip = normalize_ip(ip)
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': 'فرمت آدرس IP نامعتبر است'
                })

            # بررسی معتبر بودن IP
            if not is_valid_ip(ip):
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP معتبر نیست. فرمت صحیح: 192.168.1.100'
                })

            # ایجاد سوکت و تست اتصال
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            try:
                result = sock.connect_ex((ip, port))

                if result == 0:
                    return JsonResponse({
                        'status': 'success',
                        'message': f'اتصال با دستگاه پوز در {ip}:{port} برقرار شد'
                    })
                else:
                    error_messages = {
                        10061: "اتصال رد شد - پورت ممکن است بسته باشد",
                        10060: "اتصال timeout - دستگاه پاسخ نمی‌دهد",
                        11001: "آدرس IP یافت نشد - دستگاه در شبکه موجود نیست",
                        11002: "نام هاست یافت نشد",
                        11003: "خطای غیرمنتظره در اتصال"
                    }
                    message = error_messages.get(result, f"خطای اتصال: کد {result}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'{message} (آدرس: {ip}:{port})'
                    })

            except socket.timeout:
                return JsonResponse({
                    'status': 'error',
                    'message': f'اتصال timeout - دستگاه در {ip}:{port} پاسخ نمی‌دهد'
                })
            except ConnectionRefusedError:
                return JsonResponse({
                    'status': 'error',
                    'message': f'اتصال رد شد - پورت {port} روی دستگاه {ip} بسته است'
                })
            finally:
                sock.close()

        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'مقدار پورت نامعتبر است: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در بررسی اتصال: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'فقط درخواست POST پذیرفته می‌شود'
    })


@csrf_exempt
def send_transaction(request):
    """ارسال تراکنش به دستگاه پوز"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip', '').strip()
            port = int(data.get('port', 1362))
            amount = data.get('amount')

            if not ip:
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP نمی‌تواند خالی باشد'
                })

            # نرمال کردن IP
            try:
                ip = normalize_ip(ip)
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': 'فرمت آدرس IP نامعتبر است'
                })

            if not is_valid_ip(ip):
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP معتبر نیست'
                })

            if not amount:
                return JsonResponse({
                    'status': 'error',
                    'message': 'مبلغ نمی‌تواند خالی باشد'
                })

            # ساخت پیام تراکنش
            message = build_sale_request(amount)

            # ارسال به دستگاه پوز
            response = send_to_pos(ip, port, message)

            return JsonResponse({
                'status': 'success',
                'message': 'تراکنش ارسال شد',
                'response': response
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در ارسال تراکنش: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'فقط درخواست POST پذیرفته می‌شود'
    })


def build_sale_request(amount, currency='364', pr_code='000000'):
    """ساخت پیام درخواست خرید بر اساس مستندات TLV"""

    # تبدیل مبلغ به فرمت مورد نیاز (12 رقم)
    amount_str = str(amount).zfill(12)

    # ساخت تگ‌ها بر اساس مستندات
    tags = []

    # تگ RQ - نوع پیام درخواست
    rq_value = '034'
    tags.append('RQ' + str(len(rq_value)).zfill(2) + rq_value)

    # تگ PR - کد پردازش
    pr_value = pr_code
    tags.append('PR' + str(len(pr_value)).zfill(2) + pr_value)

    # تگ AM - مبلغ
    am_value = amount_str
    tags.append('AM' + str(len(am_value)).zfill(2) + am_value)

    # تگ CU - واحد پول
    cu_value = currency
    tags.append('CU' + str(len(cu_value)).zfill(2) + cu_value)

    # تگ PD - اطلاعات اضافی
    pd_value = '11'
    tags.append('PD' + str(len(pd_value)).zfill(2) + pd_value)

    # ساخت بدنه پیام
    message_body = ''.join(tags)

    # محاسبه طول کل و اضافه کردن به ابتدای پیام
    total_length = len(message_body)
    message = str(total_length).zfill(4) + message_body

    print(f"پیام ساخته شده: {message}")
    print(f"طول پیام: {total_length}")

    return message


def send_to_pos(ip, port, message):
    """ارسال پیام به دستگاه پوز و دریافت پاسخ"""
    try:
        # ایجاد اتصال سوکت
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60)  # افزایش timeout به 60 ثانیه
        sock.connect((ip, port))

        print(f"ارسال پیام به {ip}:{port}")
        print(f"پیام ارسالی: {message}")
        print(f"پیام HEX: {message.encode('ascii').hex()}")

        # ارسال پیام
        bytes_sent = sock.send(message.encode('ascii'))
        print(f"تعداد بایت‌های ارسال شده: {bytes_sent}")

        # منتظر پاسخ بمانیم
        time.sleep(2)  # منتظر 2 ثانیه برای پردازش دستگاه

        # دریافت پاسخ
        response = b""
        sock.settimeout(10)  # timeout برای دریافت پاسخ

        try:
            while True:
                chunk = sock.recv(1024)
                if not chunk:
                    break
                response += chunk
                # اگر پاسخ کامل دریافت شده، خارج شو
                if len(chunk) < 1024:
                    break
        except socket.timeout:
            print("Timeout در دریافت پاسخ")

        response_text = response.decode('ascii', errors='ignore')
        print(f"پاسخ دریافتی: {response_text}")
        print(f"پاسخ HEX: {response.hex()}")
        print(f"طول پاسخ: {len(response)} بایت")

        sock.close()

        if not response_text:
            return "دستگاه پوز پاسخی ارسال نکرد"

        # تجزیه پاسخ
        return parse_pos_response(response_text)

    except socket.timeout:
        return "خطا: timeout - دستگاه پاسخ نداد"
    except ConnectionRefusedError:
        return "خطا: Connection refused - پورت باز نیست"
    except BrokenPipeError:
        return "خطا: Broken pipe - اتصال قطع شد"
    except Exception as e:
        return f"خطا در ارتباط با دستگاه پوز: {str(e)}"


def parse_pos_response(response):
    """تجزیه و تحلیل پاسخ دستگاه پوز"""
    if not response:
        return 'پاسخ دریافت نشد'

    parsed_response = {}

    try:
        # طول کل (4 رقم اول)
        if len(response) >= 4:
            length = response[:4]
            parsed_response['length'] = length

            # بقیه پیام
            rest = response[4:]

            # تجزیه تگ‌ها
            pos = 0
            while pos < len(rest):
                if pos + 4 <= len(rest):
                    tag = rest[pos:pos + 2]
                    length_str = rest[pos + 2:pos + 4]

                    try:
                        value_length = int(length_str)
                        if pos + 4 + value_length <= len(rest):
                            value = rest[pos + 4:pos + 4 + value_length]
                            parsed_response[tag] = value
                            pos += 4 + value_length
                        else:
                            break
                    except:
                        break
                else:
                    break
        else:
            return f"پاسخ کوتاه است: {response}"

    except Exception as e:
        return f'خطا در تجزیه پاسخ: {str(e)} - پاسخ اصلی: {response}'

    return parsed_response


# ویو تست برای دیباگ
@csrf_exempt
def test_api(request):
    """تست ساده برای بررسی کارکرد API"""
    return JsonResponse({
        'status': 'success',
        'message': 'API درست کار می‌کند!',
        'debug': 'این یک پاسخ تستی است'
    })


# ویو جدید برای تست پیام ساده
@csrf_exempt
def test_simple_message(request):
    """ارسال پیام ساده برای تست"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip', '').strip()
            port = int(data.get('port', 1362))

            # پیام تست ساده
            test_message = "TEST"
            response = send_to_pos(ip, port, test_message)

            return JsonResponse({
                'status': 'success',
                'message': 'پیام تست ارسال شد',
                'response': response
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'خطا در ارسال پیام تست: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'فقط درخواست POST پذیرفته می‌شود'
    })


# pos_payment/views.py - اضافه کردن این ویو جدید
@csrf_exempt
def test_protocols(request):
    """تست پروتکل‌های مختلف ارتباطی"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ip = data.get('ip', '').strip()
            port = int(data.get('port', 1362))

            if not ip:
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP نمی‌تواند خالی باشد'
                })

            # نرمال کردن IP
            try:
                ip = normalize_ip(ip)
            except:
                return JsonResponse({
                    'status': 'error',
                    'message': 'فرمت آدرس IP نامعتبر است'
                })

            if not is_valid_ip(ip):
                return JsonResponse({
                    'status': 'error',
                    'message': 'آدرس IP معتبر نیست'
                })

            results = []

            # تست 1: پیام ساده
            print("🧪 تست 1: پیام ساده 'TEST'")
            result1 = send_test_message(ip, port, "TEST")
            results.append({"protocol": "ساده TEST", "result": result1})

            # تست 2: پیام ECHO
            print("🧪 تست 2: پیام 'ECHO'")
            result2 = send_test_message(ip, port, "ECHO")
            results.append({"protocol": "ECHO", "result": result2})

            # تست 3: پیام INIT
            print("🧪 تست 3: پیام 'INIT'")
            result3 = send_test_message(ip, port, "INIT")
            results.append({"protocol": "INIT", "result": result3})

            # تست 4: پیام TLV ساده
            print("🧪 تست 4: پیام TLV ساده")
            simple_tlv = "0020RQ034PR006000000AM0041000CU003364"
            result4 = send_test_message(ip, port, simple_tlv)
            results.append({"protocol": "TLV ساده", "result": result4})

            # تست 5: پیام با فرمت binary
            print("🧪 تست 5: پیام binary")
            result5 = send_binary_message(ip, port)
            results.append({"protocol": "Binary", "result": result5})

            # تست 6: پیام با STX/ETX
            print("🧪 تست 6: پیام با STX/ETX")
            result6 = send_stx_etx_message(ip, port)
            results.append({"protocol": "STX/ETX", "result": result6})

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

    return JsonResponse({
        'status': 'error',
        'message': 'فقط درخواست POST پذیرفته می‌شود'
    })


def send_test_message(ip, port, message):
    """ارسال پیام تست"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))

        print(f"📤 ارسال پیام: {message}")
        bytes_sent = sock.send(message.encode('ascii'))
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # دریافت پاسخ
        time.sleep(2)
        sock.settimeout(5)

        try:
            response = sock.recv(1024)
            if response:
                response_text = response.decode('ascii', errors='ignore')
                print(f"📥 پاسخ دریافت شد: {response_text}")
                sock.close()
                return f"پاسخ: {response_text}"
            else:
                sock.close()
                return "پاسخ خالی"
        except socket.timeout:
            sock.close()
            return "Timeout - پاسخی دریافت نشد"

    except Exception as e:
        return f"خطا: {str(e)}"


def send_binary_message(ip, port):
    """ارسال پیام binary"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))

        # پیام binary ساده
        binary_message = b'\x02\x00\x26\x00\x00\x00\x00\x01\x07\x01\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03'

        print(f"📤 ارسال پیام binary: {binary_message.hex()}")
        bytes_sent = sock.send(binary_message)
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # دریافت پاسخ
        time.sleep(2)
        sock.settimeout(5)

        try:
            response = sock.recv(1024)
            if response:
                response_hex = response.hex()
                print(f"📥 پاسخ binary دریافت شد: {response_hex}")
                sock.close()
                return f"پاسخ HEX: {response_hex}"
            else:
                sock.close()
                return "پاسخ خالی"
        except socket.timeout:
            sock.close()
            return "Timeout - پاسخی دریافت نشد"

    except Exception as e:
        return f"خطا: {str(e)}"


def send_stx_etx_message(ip, port):
    """ارسال پیام با STX/ETX"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))

        # پیام با STX (0x02) و ETX (0x03)
        message_body = "RQ034PR006000000AM0041000CU003364"
        stx_etx_message = b'\x02' + message_body.encode('ascii') + b'\x03'

        print(f"📤 ارسال پیام STX/ETX: {stx_etx_message.hex()}")
        bytes_sent = sock.send(stx_etx_message)
        print(f"✅ {bytes_sent} بایت ارسال شد")

        # دریافت پاسخ
        time.sleep(2)
        sock.settimeout(5)

        try:
            response = sock.recv(1024)
            if response:
                response_hex = response.hex()
                print(f"📥 پاسخ STX/ETX دریافت شد: {response_hex}")
                sock.close()
                return f"پاسخ HEX: {response_hex}"
            else:
                sock.close()
                return "پاسخ خالی"
        except socket.timeout:
            sock.close()
            return "Timeout - پاسخی دریافت نشد"

    except Exception as e:
        return f"خطا: {str(e)}"