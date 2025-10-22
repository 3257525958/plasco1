# pos_payment/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import POSTransaction
import json
import socket
import requests
import serial
from datetime import datetime


# ==================== مدیریت شبکه و IP ====================

def get_all_ip_addresses():
    """دریافت تمام آدرس‌های IP دستگاه"""
    ip_addresses = []

    try:
        # دریافت hostname
        hostname = socket.gethostname()

        # دریافت تمام IPهای مرتبط
        all_ips = socket.gethostbyname_ex(hostname)[2]

        # حذف IPهای loopback و لینک-لوکال
        ip_addresses = [
            ip for ip in all_ips
            if not ip.startswith("127.") and not ip.startswith("169.254.")
        ]

        # اگر IP داخلی پیدا نشد، سعی می‌کنیم از روش‌های دیگر پیدا کنیم
        if not ip_addresses:
            try:
                # ایجاد سوکت موقت برای تشخیص IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                ip_addresses.append(local_ip)
            except Exception as e:
                print(f"خطا در تشخیص IP با سوکت: {e}")

    except Exception as e:
        print(f"خطا در دریافت IP: {e}")

    return ip_addresses


def get_public_ip():
    """دریافت IP عمومی"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text
    except requests.RequestException:
        try:
            response = requests.get('https://ident.me', timeout=5)
            return response.text
        except requests.RequestException:
            return "نامشخص"


def get_network_info():
    """دریافت کامل اطلاعات شبکه"""
    local_ips = get_all_ip_addresses()
    public_ip = get_public_ip()
    hostname = socket.gethostname()

    return {
        'hostname': hostname,
        'local_ips': local_ips,
        'public_ip': public_ip,
        'primary_ip': local_ips[0] if local_ips else '127.0.0.1',
        'timestamp': timezone.now().isoformat()
    }


# ==================== کلاس مدیریت پوز ====================

class POSManager:
    def __init__(self, ip=None, port=1362, connection_type='LAN', com_port='COM1', baud_rate=115200):
        self.connection_type = connection_type
        self.ip = ip or '192.168.18.94'
        self.port = port
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.socket = None
        self.serial_conn = None

    def test_connection(self):
        """تست ارتباط با دستگاه پوز"""
        try:
            if self.connection_type == 'LAN':
                return self._test_lan_connection()
            else:
                return self._test_serial_connection()
        except Exception as e:
            return False, f"خطا در تست ارتباط: {str(e)}"

    def _test_lan_connection(self):
        """تست ارتباط LAN"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.ip, self.port))
            self.socket.close()
            return True, f"اتصال با دستگاه پوز در {self.ip}:{self.port} برقرار شد"
        except socket.timeout:
            return False, f"Timeout: دستگاه پوز در {self.ip}:{self.port} پاسخ نمی‌دهد"
        except ConnectionRefusedError:
            return False, f"Connection Refused: پورت {self.port} در {self.ip} در دسترس نیست"
        except socket.gaierror:
            return False, f"آدرس IP {self.ip} معتبر نیست"
        except Exception as e:
            return False, f"خطا در اتصال LAN: {str(e)}"

    def _test_serial_connection(self):
        """تست ارتباط سریال"""
        try:
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=10
            )
            if self.serial_conn.is_open:
                self.serial_conn.close()
                return True, f"اتصال سریال با دستگاه پوز در {self.com_port} برقرار شد"
            return False, f"اتصال سریال در {self.com_port} برقرار نشد"
        except serial.SerialException as e:
            return False, f"خطا در اتصال سریال: {str(e)}"
        except Exception as e:
            return False, f"خطای ناشناخته در اتصال سریال: {str(e)}"

    def send_payment_request(self, amount=1250):
        """ارسال درخواست پرداخت"""
        steps = []
        try:
            steps.append(f"🚀 شروع فرآیند پرداخت {amount} تومانی")

            # برقراری ارتباط
            if self.connection_type == 'LAN':
                steps.append(f"🔌 اتصال به {self.ip}:{self.port}")
                result = self._send_via_lan(steps)
            else:
                steps.append(f"🔌 اتصال سریال به {self.com_port}")
                result = self._send_via_serial(steps)

            return result

        except Exception as e:
            steps.append(f"❌ خطا در ارسال درخواست پرداخت: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در انجام تراکنش: {str(e)}",
                'steps': steps
            }

    def _send_via_lan(self, steps):
        """ارسال از طریق LAN"""
        try:
            # مرحله 1: ایجاد سوکت
            steps.append("📡 در حال ایجاد سوکت...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)

            # مرحله 2: اتصال به دستگاه
            steps.append(f"🔌 در حال اتصال به {self.ip}:{self.port}...")
            self.socket.connect((self.ip, self.port))
            steps.append("✅ اتصال برقرار شد")

            # مرحله 3: ساخت داده تراکنش
            steps.append("🔧 در حال ساخت داده‌های تراکنش...")
            transaction_data = self._build_transaction_data()
            data_bytes = self._convert_to_bytes(transaction_data)

            # مرحله 4: ارسال داده
            steps.append("🚀 در حال ارسال داده به پوز...")
            self.socket.send(data_bytes)
            steps.append("✅ داده ارسال شد")

            # مرحله 5: دریافت پاسخ
            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.socket.recv(1024)
            steps.append("✅ پاسخ دریافت شد")

            # مرحله 6: پردازش پاسخ
            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_response(response)

            # مرحله 7: بستن اتصال
            self.socket.close()
            steps.append("🔒 اتصال بسته شد")

            # بررسی موفقیت آمیز بودن تراکنش
            if self._is_transaction_successful(parsed_response):
                steps.append("🎉 تراکنش با موفقیت انجام شد")
                return {
                    'success': True,
                    'message': "پرداخت با موفقیت انجام شد",
                    'response': parsed_response,
                    'steps': steps
                }
            else:
                steps.append("❌ تراکنش ناموفق بود")
                return {
                    'success': False,
                    'message': "تراکنش ناموفق بود",
                    'response': parsed_response,
                    'steps': steps
                }

        except socket.timeout:
            steps.append("❌ خطا: Timeout - دستگاه پاسخ نداد")
            return {
                'success': False,
                'message': "دستگاه پوز در زمان مشخص پاسخ نداد",
                'steps': steps
            }
        except Exception as e:
            steps.append(f"❌ خطا: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در ارسال از طریق LAN: {str(e)}",
                'steps': steps
            }

    def _send_via_serial(self, steps):
        """ارسال از طریق سریال"""
        try:
            # مرحله 1: باز کردن پورت سریال
            steps.append(f"📡 در حال باز کردن پورت {self.com_port}...")
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                timeout=30
            )
            steps.append("✅ پورت سریال باز شد")

            # مرحله 2: ساخت داده تراکنش
            steps.append("🔧 در حال ساخت داده‌های تراکنش...")
            transaction_data = self._build_transaction_data()
            data_bytes = self._convert_to_bytes(transaction_data)

            # مرحله 3: ارسال داده
            steps.append("🚀 در حال ارسال داده به پوز...")
            self.serial_conn.write(data_bytes)
            steps.append("✅ داده ارسال شد")

            # مرحله 4: دریافت پاسخ
            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.serial_conn.read(1024)
            steps.append("✅ پاسخ دریافت شد")

            # مرحله 5: پردازش پاسخ
            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_response(response)

            # مرحله 6: بستن پورت
            self.serial_conn.close()
            steps.append("🔒 پورت سریال بسته شد")

            # بررسی موفقیت آمیز بودن تراکنش
            if self._is_transaction_successful(parsed_response):
                steps.append("🎉 تراکنش با موفقیت انجام شد")
                return {
                    'success': True,
                    'message': "پرداخت با موفقیت انجام شد",
                    'response': parsed_response,
                    'steps': steps
                }
            else:
                steps.append("❌ تراکنش ناموفق بود")
                return {
                    'success': False,
                    'message': "تراکنش ناموفق بود",
                    'response': parsed_response,
                    'steps': steps
                }

        except Exception as e:
            steps.append(f"❌ خطا: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در ارسال از طریق سریال: {str(e)}",
                'steps': steps
            }

    def _build_transaction_data(self):
        """ساخت داده‌های تراکنش (ساده شده)"""
        # این قسمت باید بر اساس مستندات فنی پوز پر شود
        transaction_data = {
            'command': 'SALE',
            'amount': '00000001250',  # 1250 تومان
            'currency': '364',
            'transaction_id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'terminal_id': '00000001'
        }
        return transaction_data

    def _convert_to_bytes(self, data):
        """تبدیل داده‌ها به فرمت بایت"""
        # این یک نمونه ساده است - باید بر اساس پروتکل دستگاه پیاده‌سازی شود
        if isinstance(data, dict):
            return json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            return data.encode('utf-8')
        else:
            return str(data).encode('utf-8')

    def _parse_response(self, response):
        """پردازش پاسخ دریافتی"""
        try:
            if isinstance(response, bytes):
                # سعی در decode کردن
                try:
                    response_text = response.decode('utf-8')
                except UnicodeDecodeError:
                    response_text = response.hex()
            else:
                response_text = str(response)

            # این قسمت باید بر اساس فرمت پاسخ دستگاه پیاده‌سازی شود
            return {
                'raw_response': response_text,
                'timestamp': timezone.now().isoformat(),
                'status': 'received',
                'parsed': "نیاز به پیاده‌سازی پارسر بر اساس مستندات پوز"
            }
        except Exception as e:
            return {
                'raw_response': str(response),
                'error': f"خطا در پردازش پاسخ: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }

    def _is_transaction_successful(self, response):
        """بررسی موفقیت آمیز بودن تراکنش"""
        # این تابع باید بر اساس کدهای پاسخ دستگاه پیاده‌سازی شود
        # در این نمونه ساده، فرض می‌کنیم اگر خطایی نباشد تراکنش موفق است
        return 'error' not in response


# ==================== ویوهای اصلی ====================

def pos_dashboard(request):
    """صفحه اصلی مدیریت پوز"""
    network_info = get_network_info()

    context = {
        'local_ips': network_info['local_ips'],
        'public_ip': network_info['public_ip'],
        'hostname': network_info['hostname'],
        'primary_ip': network_info['primary_ip'],
        'timestamp': network_info['timestamp']
    }

    return render(request, 'pos_payment/dashboard.html', context)


@csrf_exempt
def get_network_info_api(request):
    """API برای دریافت اطلاعات شبکه"""
    if request.method == 'GET':
        network_info = get_network_info()
        return JsonResponse({
            'success': True,
            **network_info
        })

    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@csrf_exempt
def test_connection(request):
    """تست ارتباط با پوز"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # ایجاد نمونه POSManager با تنظیمات دریافتی
            pos = POSManager(
                ip=data.get('ip'),
                port=int(data.get('port', 1362)),
                connection_type=data.get('connection_type', 'LAN'),
                com_port=data.get('com_port', 'COM1')
            )

            # تست ارتباط
            success, message = pos.test_connection()

            return JsonResponse({
                'success': success,
                'message': message,
                'ip_used': pos.ip,
                'port_used': pos.port,
                'connection_type': pos.connection_type
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیستند'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"خطا در تست ارتباط: {str(e)}"
            })

    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@csrf_exempt
def make_payment(request):
    """انجام تراکنش پرداخت"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # ایجاد تراکنش در دیتابیس
            transaction = POSTransaction.objects.create(
                amount=1250,  # مبلغ ثابت 1250 تومان
                status='pending',
                transaction_date=timezone.now()
            )

            # ایجاد نمونه POSManager با تنظیمات دریافتی
            pos = POSManager(
                ip=data.get('ip'),
                port=int(data.get('port', 1362)),
                connection_type=data.get('connection_type', 'LAN'),
                com_port=data.get('com_port', 'COM1')
            )

            # ارسال درخواست پرداخت
            result = pos.send_payment_request(amount=1250)

            # بروزرسانی وضعیت تراکنش در دیتابیس
            if result['success']:
                transaction.status = 'success'
                transaction.response_message = result['message']

                # ذخیره پاسخ در صورت وجود
                if 'response' in result:
                    transaction.response_code = '00'  # کد موفقیت فرضی
                    transaction.reference_number = result['response'].get('timestamp', 'N/A')
            else:
                transaction.status = 'failed'
                transaction.response_message = result['message']

            transaction.save()

            # اضافه کردن اطلاعات تراکنش به پاسخ
            result['transaction_id'] = transaction.id
            result['transaction_date'] = transaction.transaction_date.isoformat()

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ارسالی معتبر نیستند',
                'steps': ['❌ خطا: داده‌های ارسالی معتبر نیستند']
            })
        except Exception as e:
            # در صورت خطا نیز تراکنش را ذخیره می‌کنیم
            try:
                transaction = POSTransaction.objects.create(
                    amount=1250,
                    status='failed',
                    response_message=f"خطای سیستمی: {str(e)}",
                    transaction_date=timezone.now()
                )
            except:
                pass

            return JsonResponse({
                'success': False,
                'message': f"خطا در انجام تراکنش: {str(e)}",
                'steps': [f'❌ خطای سیستمی: {str(e)}']
            })

    return JsonResponse({'success': False, 'message': 'Method not allowed'})


def transaction_history(request):
    """تاریخچه تراکنش‌ها"""
    transactions = POSTransaction.objects.all().order_by('-transaction_date')

    # آمار تراکنش‌ها
    stats = {
        'total': transactions.count(),
        'success': transactions.filter(status='success').count(),
        'failed': transactions.filter(status='failed').count(),
        'pending': transactions.filter(status='pending').count(),
    }

    context = {
        'transactions': transactions,
        'stats': stats
    }

    return render(request, 'pos_payment/history.html', context)


def transaction_detail(request, transaction_id):
    """جزئیات تراکنش"""
    transaction = get_object_or_404(POSTransaction, id=transaction_id)

    context = {
        'transaction': transaction
    }

    return render(request, 'pos_payment/transaction_detail.html', context)


@csrf_exempt
def clear_transactions(request):
    """پاک کردن تاریخچه تراکنش‌ها (برای تست)"""
    if request.method == 'POST':
        try:
            count, _ = POSTransaction.objects.all().delete()
            return JsonResponse({
                'success': True,
                'message': f'{count} تراکنش پاک شد',
                'deleted_count': count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در پاک کردن تراکنش‌ها: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Method not allowed'})


# ==================== ویوهای کمکی ====================

def pos_guide(request):
    """راهنمای تنظیمات پوز"""
    network_info = get_network_info()

    context = {
        'local_ips': network_info['local_ips'],
        'primary_ip': network_info['primary_ip'],
        'hostname': network_info['hostname']
    }

    return render(request, 'pos_payment/guide.html', context)


def pos_settings(request):
    """تنظیمات پوز"""
    network_info = get_network_info()

    # تنظیمات پیش‌فرض
    default_settings = {
        'default_ip': network_info['primary_ip'],
        'default_port': 1362,
        'default_com_port': 'COM1',
        'default_baud_rate': 115200,
        'default_amount': 1250,
        'timeout': 30
    }

    context = {
        'network_info': network_info,
        'settings': default_settings
    }

    return render(request, 'pos_payment/settings.html', context)


# ==================== هندلر خطاها ====================

def handler404(request, exception):
    """هندلر خطای 404"""
    return JsonResponse({
        'success': False,
        'message': 'صفحه مورد نظر یافت نشد'
    }, status=404)


def handler500(request):
    """هندلر خطای 500"""
    return JsonResponse({
        'success': False,
        'message': 'خطای داخلی سرور'
    }, status=500)