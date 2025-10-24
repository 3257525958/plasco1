# pos_payment/pos_manager.py
import socket
import serial
import json
from datetime import datetime


class POSManager:
    def __init__(self, ip=None, port=1362, connection_type='LAN', com_port='COM1', baud_rate=115200):
        self.connection_type = connection_type
        self.ip = ip or '192.168.018.094'  # فرمت 12 رقمی
        self.port = port
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.socket = None
        self.serial_conn = None

        # تنظیمات پیش‌فرض مشابه برنامه C#
        self.sign_code = ""
        self.terminal_id = ""
        self.reference_number = ""
        self.amount = "000000001250"
        self.pr_code = "000000"
        self.currency = "364"

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
            self.socket.connect((self._normalize_ip(self.ip), self.port))
            self.socket.close()
            return True, f"✅ اتصال موفق با پوز در {self.ip}:{self.port}"
        except socket.timeout:
            return False, f"⏰ timeout: دستگاه پوز در {self.ip}:{self.port} پاسخ نداد"
        except ConnectionRefusedError:
            return False, f"❌ connection refused: پورت {self.port} در {self.ip} در دسترس نیست"
        except socket.gaierror:
            return False, f"🌐 آدرس IP {self.ip} معتبر نیست"
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
                timeout=10
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
        """ارسال درخواست پرداخت - شبیه به برنامه C#"""
        steps = []
        try:
            steps.append(f"🚀 شروع فرآیند پرداخت {amount} تومانی")

            # تنظیم مقادیر مشابه برنامه C#
            self.amount = str(amount).zfill(12)

            if self.connection_type == 'LAN':
                steps.append(f"🔌 اتصال LAN به {self.ip}:{self.port}")
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
        """ارسال از طریق LAN - شبیه به برنامه C#"""
        try:
            steps.append("📡 در حال ایجاد سوکت...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)

            steps.append(f"🔌 در حال اتصال به {self.ip}:{self.port}...")
            self.socket.connect((self._normalize_ip(self.ip), self.port))
            steps.append("✅ اتصال برقرار شد")

            steps.append("🔧 در حال ساخت داده‌های تراکنش (مشابه برنامه C#)...")

            # ساخت داده‌های تراکنش مشابه برنامه C#
            transaction_data = self._build_transaction_data()

            steps.append("🚀 در حال ارسال داده به پوز...")
            self.socket.send(transaction_data)
            steps.append("✅ داده ارسال شد")

            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.socket.recv(4096)
            steps.append("✅ پاسخ دریافت شد")

            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_pos_response(response)

            self.socket.close()
            steps.append("🔒 اتصال بسته شد")

            if self._is_transaction_successful(parsed_response):
                steps.append("🎉 تراکنش با موفقیت انجام شد")
                return {
                    'success': True,
                    'message': "پرداخت با موفقیت انجام شد",
                    'response': parsed_response,
                    'steps': steps,
                    'transaction_data': transaction_data.hex()
                }
            else:
                steps.append("❌ تراکنش ناموفق بود")
                return {
                    'success': False,
                    'message': "تراکنش ناموفق بود",
                    'response': parsed_response,
                    'steps': steps,
                    'transaction_data': transaction_data.hex()
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
            steps.append(f"📡 در حال باز کردن پورت {self.com_port}...")
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                timeout=30
            )
            steps.append("✅ پورت سریال باز شد")

            steps.append("🔧 در حال ساخت داده‌های تراکنش...")
            transaction_data = self._build_transaction_data()

            steps.append("🚀 در حال ارسال داده به پوز...")
            self.serial_conn.write(transaction_data)
            steps.append("✅ داده ارسال شد")

            steps.append("⏳ در انتظار پاسخ از پوز...")
            response = self.serial_conn.read(1024)
            steps.append("✅ پاسخ دریافت شد")

            steps.append("🔍 در حال پردازش پاسخ...")
            parsed_response = self._parse_pos_response(response)

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

    def _build_transaction_data(self):
        """
        ساخت داده‌های تراکنش مشابه برنامه C#
        اینجا باید بر اساس مستندات DLL پیاده‌سازی شود
        """
        try:
            # این یک نمونه ساده است - باید بر اساس مستندات دقیق DLL پر شود
            # در برنامه C# از pcpos.send_transaction() استفاده می‌شود

            transaction_template = {
                'command': 'SALE',
                'amount': self.amount,
                'pr_code': self.pr_code,
                'currency': self.currency,
                'terminal_id': self.terminal_id or '00000001',
                'sign_code': self.sign_code,
                'timestamp': datetime.now().strftime('%Y%m%d%H%M%S')
            }

            # تبدیل به فرمت بایت - این قسمت باید با فرمت دقیق DLL همخوانی داشته باشد
            data_str = json.dumps(transaction_template)
            return data_str.encode('utf-8')

        except Exception as e:
            # در صورت خطا، یک داده تست ساده برگردان
            test_data = f"AM{self.amount}PR{self.pr_code}CU{self.currency}".encode('utf-8')
            return test_data

    def _parse_pos_response(self, response):
        """پردازش پاسخ دریافتی از پوز"""
        try:
            if isinstance(response, bytes):
                try:
                    response_text = response.decode('utf-8')
                except UnicodeDecodeError:
                    response_text = response.hex()
            else:
                response_text = str(response)

            # تجزیه پاسخ بر اساس فرمت پوز
            # این قسمت باید بر اساس مستندات دقیق پیاده‌سازی شود
            parsed_response = {
                'raw_response': response_text,
                'timestamp': datetime.now().isoformat(),
                'status': 'received',
                'response_code': self._extract_response_code(response_text),
                'message': self._extract_response_message(response_text)
            }

            return parsed_response
        except Exception as e:
            return {
                'raw_response': str(response),
                'error': f"خطا در پردازش پاسخ: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def _extract_response_code(self, response):
        """استخراج کد پاسخ از پاسخ پوز"""
        # اینجا باید بر اساس فرمت واقعی پاسخ پیاده‌سازی شود
        if '00' in response or 'success' in response.lower():
            return '00'
        return '99'  # کد خطای پیش‌فرض

    def _extract_response_message(self, response):
        """استخراج پیام پاسخ از پاسخ پوز"""
        # اینجا باید بر اساس فرمت واقعی پاسخ پیاده‌سازی شود
        if '00' in response or 'success' in response.lower():
            return 'تراکنش موفق'
        return 'تراکنش ناموفق'

    def _is_transaction_successful(self, response):
        """بررسی موفقیت آمیز بودن تراکنش"""
        if isinstance(response, dict):
            return response.get('response_code') == '00'
        return False

    def _normalize_ip(self, ip_12_digit):
        """تبدیل IP از فرمت 12 رقمی به معمولی برای استفاده در سوکت"""
        try:
            if re.match(r'^\d{3}\.\d{3}\.\d{3}\.\d{3}$', ip_12_digit):
                parts = ip_12_digit.split('.')
                normalized_parts = [str(int(part)) for part in parts]
                return '.'.join(normalized_parts)
            return ip_12_digit
        except:
            return ip_12_digit


# اضافه کردن import مورد نیاز
import re