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
import re


# ==================== مدیریت شبکه و IP ====================

def format_ip_to_12_digits(ip):
    """تبدیل IP به فرمت 12 رقمی با نقطه بین هر سه رقم"""
    try:
        # اگر IP قبلاً فرمت 12 رقمی دارد، برگردان
        if re.match(r'^\d{3}\.\d{3}\.\d{3}\.\d{3}$', ip):
            return ip

        # تقسیم IP به بخش‌ها
        parts = ip.split('.')
        if len(parts) != 4:
            return ip

        # فرمت هر بخش به سه رقم
        formatted_parts = []
        for part in parts:
            formatted_parts.append(part.zfill(3))

        return '.'.join(formatted_parts)
    except:
        return ip


def parse_ip_from_12_digits(ip_12_digit):
    """تبدیل IP از فرمت 12 رقمی به فرمت معمولی"""
    try:
        if re.match(r'^\d{3}\.\d{3}\.\d{3}\.\d{3}$', ip_12_digit):
            parts = ip_12_digit.split('.')
            # حذف صفرهای ابتدایی
            normalized_parts = []
            for part in parts:
                normalized_parts.append(str(int(part)))
            return '.'.join(normalized_parts)
        return ip_12_digit
    except:
        return ip_12_digit


def get_client_real_ip(request):
    """دریافت IP واقعی کاربر"""
    try:
        ip = None

        # روش‌های مختلف تشخیص IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        elif request.META.get('HTTP_X_REAL_IP'):
            ip = request.META.get('HTTP_X_REAL_IP')
        else:
            ip = request.META.get('REMOTE_ADDR')

        # اگر IP لوکال هست، سعی کن IP واقعی شبکه رو پیدا کن
        if ip in ['127.0.0.1', 'localhost', '::1']:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except:
                ip = '127.0.0.1'

        return ip
    except:
        return 'نامشخص'


def get_client_info(request):
    """دریافت اطلاعات کلاینت"""
    try:
        client_ip = get_client_real_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'نامشخص')
        host = request.get_host()

        return {
            'client_ip': client_ip,
            'client_ip_12_digit': format_ip_to_12_digits(client_ip),
            'user_agent': user_agent,
            'host': host,
            'is_mobile': any(device in user_agent.lower() for device in ['mobile', 'android', 'iphone']),
            'timestamp': timezone.now().isoformat(),
            'is_local': client_ip in ['127.0.0.1', 'localhost', '::1']
        }
    except Exception as e:
        return {
            'client_ip': 'نامشخص',
            'client_ip_12_digit': 'نامشخص',
            'user_agent': 'نامشخص',
            'host': 'نامشخص',
            'is_mobile': False,
            'timestamp': timezone.now().isoformat(),
            'is_local': True
        }


def get_server_network_info():
    """دریافت اطلاعات شبکه سرور"""
    try:
        hostname = socket.gethostname()

        local_ips = []
        try:
            all_ips = socket.gethostbyname_ex(hostname)[2]
            local_ips = [ip for ip in all_ips if not ip.startswith("127.")]
        except:
            pass

        if not local_ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                local_ips = [local_ip]
            except:
                local_ips = ['127.0.0.1']

        public_ip = "نیاز به اینترنت"
        try:
            response = requests.get('https://api.ipify.org', timeout=3)
            public_ip = response.text
        except:
            pass

        # تبدیل IPها به فرمت 12 رقمی
        local_ips_12_digit = [format_ip_to_12_digits(ip) for ip in local_ips]

        return {
            'hostname': hostname,
            'local_ips': local_ips,
            'local_ips_12_digit': local_ips_12_digit,
            'public_ip': public_ip,
            'public_ip_12_digit': format_ip_to_12_digits(public_ip),
            'primary_ip': local_ips[0] if local_ips else '127.0.0.1',
            'primary_ip_12_digit': format_ip_to_12_digits(local_ips[0] if local_ips else '127.0.0.1'),
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        return {
            'hostname': 'نامشخص',
            'local_ips': ['127.0.0.1'],
            'local_ips_12_digit': ['127.000.000.001'],
            'public_ip': 'نامشخص',
            'public_ip_12_digit': 'نامشخص',
            'primary_ip': '127.0.0.1',
            'primary_ip_12_digit': '127.000.000.001',
            'timestamp': timezone.now().isoformat()
        }


# ==================== کلاس مدیریت پوز ====================

class POSManager:
    def __init__(self, ip=None, port=1362, connection_type='LAN', com_port='COM1', baud_rate=115200):
        self.connection_type = connection_type
        # تبدیل IP به فرمت معمولی برای استفاده در سوکت
        self.ip = parse_ip_from_12_digits(ip) if ip else '192.168.18.94'
        self.ip_12_digit = format_ip_to_12_digits(self.ip)  # نگهداری فرمت 12 رقمی
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
            self.socket.settimeout(5)
            self.socket.connect((self.ip, self.port))
            self.socket.close()
            return True, f"✅ اتصال موفق با پوز در {self.ip_12_digit}:{self.port}"
        except socket.timeout:
            return False, f"⏰ timeout: دستگاه پوز در {self.ip_12_digit}:{self.port} پاسخ نداد"
        except ConnectionRefusedError:
            return False, f"❌ connection refused: پورت {self.port} در {self.ip_12_digit} در دسترس نیست"
        except socket.gaierror:
            return False, f"🌐 آدرس IP {self.ip_12_digit} معتبر نیست"
        except Exception as e:
            return False, f"🔴 خطا در اتصال: {str(e)}"

    def _test_serial_connection(self):
        """تست ارتباط سریال"""
        try:
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=5
            )
            if self.serial_conn.is_open:
                self.serial_conn.close()
                return True, f"✅ اتصال سریال موفق با {self.com_port}"
            return False, f"❌ اتصال سریال برقرار نشد"
        except serial.SerialException as e:
            return False, f"🔌 خطا در اتصال سریال: {str(e)}"
        except Exception as e:
            return False, f"🔴 خطای ناشناخته در اتصال سریال: {str(e)}"

    def send_payment_request(self, amount=1250):
        """ارسال درخواست پرداخت"""
        steps = []
        try:
            steps.append(f"🚀 شروع فرآیند پرداخت {amount} تومانی")

            if self.connection_type == 'LAN':
                steps.append(f"🔌 اتصال LAN به {self.ip_12_digit}:{self.port}")
                result = self._send_via_lan(amount, steps)
            else:
                steps.append(f"🔌 اتصال سریال به {self.com_port}")
                result = self._send_via_serial(amount, steps)

            return result

        except Exception as e:
            steps.append(f"❌ خطا در ارسال درخواست پرداخت: {str(e)}")
            return {
                'success': False,
                'message': f"خطا در انجام تراکنش: {str(e)}",
                'steps': steps
            }

    def _send_via_lan(self, amount, steps):
        """ارسال از طریق LAN"""
        try:
            steps.append("📡 در حال ایجاد سوکت...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)

            steps.append(f"🔌 در حال اتصال به {self.ip_12_digit}:{self.port}...")
            self.socket.connect((self.ip, self.port))
            steps.append("✅ اتصال برقرار شد")

            steps.append("🔧 در حال ساخت داده‌های تراکنش...")
            transaction_data = self._build_transaction_data(amount)
            data_bytes = self._convert_to_bytes(transaction_data)

            steps.append("🚀 در حال ارسال داده به پوز...")
            self.socket.send(data_bytes)
            steps.append("✅ داده ارسال شد")

            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.socket.recv(1024)
            steps.append("✅ پاسخ دریافت شد")

            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_response(response)

            self.socket.close()
            steps.append("🔒 اتصال بسته شد")

            if self._is_transaction_successful(parsed_response):
                steps.append("🎉 تراکنش با موفقیت انجام شد")
                return {
                    'success': True,
                    'message': "پرداخت با موفقیت انجام شد",
                    'response': parsed_response,
                    'steps': steps,
                    'ip_used': self.ip_12_digit,
                    'port_used': self.port
                }
            else:
                steps.append("❌ تراکنش ناموفق بود")
                return {
                    'success': False,
                    'message': "تراکنش ناموفق بود",
                    'response': parsed_response,
                    'steps': steps,
                    'ip_used': self.ip_12_digit,
                    'port_used': self.port
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

    def _send_via_serial(self, amount, steps):
        """ارسال از طریق سریال"""
        try:
            steps.append(f"📡 در حال باز کردن پورت {self.com_port}...")
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                timeout=30
            )
            steps.append("✅ پورت سریال باز شد")

            steps.append("🔧 در حال ساخت داده‌های تراکنش...")
            transaction_data = self._build_transaction_data(amount)
            data_bytes = self._convert_to_bytes(transaction_data)

            steps.append("🚀 در حال ارسال داده به پوز...")
            self.serial_conn.write(data_bytes)
            steps.append("✅ داده ارسال شد")

            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.serial_conn.read(1024)
            steps.append("✅ پاسخ دریافت شد")

            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_response(response)

            self.serial_conn.close()
            steps.append("🔒 پورت سریال بسته شد")

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

    def _build_transaction_data(self, amount):
        """ساخت داده‌های تراکنش"""
        transaction_data = {
            'command': 'SALE',
            'amount': str(amount).zfill(12),
            'currency': '364',
            'transaction_id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'terminal_id': '00000001',
            'merchant_id': '000000000001'
        }
        return transaction_data

    def _convert_to_bytes(self, data):
        """تبدیل داده‌ها به فرمت بایت"""
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
                try:
                    response_text = response.decode('utf-8')
                except UnicodeDecodeError:
                    response_text = response.hex()
            else:
                response_text = str(response)

            return {
                'raw_response': response_text,
                'timestamp': timezone.now().isoformat(),
                'status': 'received',
                'parsed': "پاسخ دریافت شد - نیاز به پیاده‌سازی پارسر بر اساس مستندات پوز"
            }
        except Exception as e:
            return {
                'raw_response': str(response),
                'error': f"خطا در پردازش پاسخ: {str(e)}",
                'timestamp': timezone.now().isoformat()
            }

    def _is_transaction_successful(self, response):
        """بررسی موفقیت آمیز بودن تراکنش"""
        return 'error' not in response


# ==================== ویوهای اصلی ====================

def pos_dashboard(request):
    """صفحه اصلی با اطلاعات سرور و کلاینت"""
    server_network_info = get_server_network_info()
    client_info = get_client_info(request)

    context = {
        # اطلاعات سرور
        'server_local_ips': server_network_info['local_ips'],
        'server_local_ips_12_digit': server_network_info['local_ips_12_digit'],
        'server_public_ip': server_network_info['public_ip'],
        'server_public_ip_12_digit': server_network_info['public_ip_12_digit'],
        'server_hostname': server_network_info['hostname'],
        'server_primary_ip': server_network_info['primary_ip'],
        'server_primary_ip_12_digit': server_network_info['primary_ip_12_digit'],

        # اطلاعات کلاینت
        'client_ip': client_info['client_ip'],
        'client_ip_12_digit': client_info['client_ip_12_digit'],
        'client_user_agent': client_info['user_agent'],
        'client_is_mobile': client_info['is_mobile'],
        'client_is_local': client_info['is_local'],
        'client_host': client_info['host'],

        'timestamp': server_network_info['timestamp']
    }

    return render(request, 'pos_payment/dashboard.html', context)


@csrf_exempt
def get_network_info_api(request):
    """API برای دریافت اطلاعات شبکه"""
    if request.method == 'GET':
        network_info = get_server_network_info()
        client_info = get_client_info(request)

        return JsonResponse({
            'success': True,
            'server': network_info,
            'client': client_info
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
                'ip_used': pos.ip_12_digit,
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
                amount=1250,
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

                if 'response' in result:
                    transaction.response_code = '00'
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
    network_info = get_server_network_info()
    client_info = get_client_info(request)

    context = {
        'local_ips': network_info['local_ips_12_digit'],
        'primary_ip': network_info['primary_ip_12_digit'],
        'hostname': network_info['hostname'],
        'client_ip': client_info['client_ip_12_digit'],
        'client_is_local': client_info['is_local']
    }

    return render(request, 'pos_payment/guide.html', context)


def pos_settings(request):
    """تنظیمات پوز"""
    network_info = get_server_network_info()

    # تنظیمات پیش‌فرض
    default_settings = {
        'default_ip': '192.168.018.094',  # IP پیش‌فرض دستگاه پوز به فرمت 12 رقمی
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