# pos_payment/pos_manager.py
import socket
import serial
import json
from datetime import datetime


class POSManager:
    def __init__(self):
        self.connection_type = 'LAN'  # یا 'SERIAL'
        self.ip = '192.168.18.94'
        self.port = 1362
        self.com_port = 'COM1'
        self.baud_rate = 115200
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
            return True, "اتصال با دستگاه پوز برقرار شد"
        except socket.timeout:
            return False, "Timeout: دستگاه پوز پاسخ نمی‌دهد"
        except ConnectionRefusedError:
            return False, "Connection Refused: پورت یا آی‌پی نادرست است"
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
                return True, "اتصال سریال با دستگاه پوز برقرار شد"
            return False, "اتصال سریال برقرار نشد"
        except serial.SerialException as e:
            return False, f"خطا در اتصال سریال: {str(e)}"
        except Exception as e:
            return False, f"خطای ناشناخته در اتصال سریال: {str(e)}"

    def send_payment_request(self, amount=1250):
        """ارسال درخواست پرداخت"""
        try:
            # ساخت داده‌های تراکنش
            transaction_data = self._build_transaction_data(amount)

            # برقراری ارتباط
            if self.connection_type == 'LAN':
                return self._send_via_lan(transaction_data)
            else:
                return self._send_via_serial(transaction_data)

        except Exception as e:
            return {
                'success': False,
                'message': f"خطا در ارسال درخواست پرداخت: {str(e)}",
                'step': 'ارسال درخواست'
            }

    def _build_transaction_data(self, amount):
        """ساخت داده‌های تراکنش به فرمت TLV"""
        # این قسمت باید بر اساس مستندات فنی پوز پر شود
        # این یک نمونه ساده است
        amount_str = str(amount).zfill(12)

        transaction_data = {
            'PR': '000000',  # کد پرداخت
            'AM': amount_str,  # مبلغ
            'CU': '364',  # کد ارز
        }

        return transaction_data

    def _send_via_lan(self, data):
        """ارسال از طریق LAN"""
        steps = []
        try:
            # مرحله 1: ایجاد سوکت
            steps.append("📡 در حال ایجاد سوکت...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)

            # مرحله 2: اتصال به دستگاه
            steps.append(f"🔌 در حال اتصال به {self.ip}:{self.port}...")
            self.socket.connect((self.ip, self.port))
            steps.append("✅ اتصال برقرار شد")

            # مرحله 3: تبدیل داده به بایت
            steps.append("🔧 در حال تبدیل داده‌ها...")
            data_bytes = self._convert_to_bytes(data)

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

            return {
                'success': True,
                'message': "پرداخت با موفقیت انجام شد",
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

    def _send_via_serial(self, data):
        """ارسال از طریق سریال"""
        steps = []
        try:
            # مرحله 1: باز کردن پورت سریال
            steps.append(f"📡 در حال باز کردن پورت {self.com_port}...")
            self.serial_conn = serial.Serial(
                port=self.com_port,
                baudrate=self.baud_rate,
                timeout=30
            )
            steps.append("✅ پورت سریال باز شد")

            # مرحله 2: تبدیل داده به بایت
            steps.append("🔧 در حال تبدیل داده‌ها...")
            data_bytes = self._convert_to_bytes(data)

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

            return {
                'success': True,
                'message': "پرداخت با موفقیت انجام شد",
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

    def _convert_to_bytes(self, data):
        """تبدیل داده‌ها به فرمت بایت"""
        # این قسمت باید بر اساس پروتکل دستگاه پیاده‌سازی شود
        # این یک نمونه ساده است
        return json.dumps(data).encode('utf-8')

    def _parse_response(self, response):
        """پردازش پاسخ دریافتی"""
        try:
            if isinstance(response, bytes):
                response = response.decode('utf-8')

            # این قسمت باید بر اساس فرمت پاسخ دستگاه پیاده‌سازی شود
            return {
                'raw_response': response,
                'parsed': "پاسخ دریافت شد - نیاز به پارس کردن بر اساس مستندات"
            }
        except Exception as e:
            return {
                'raw_response': str(response),
                'error': f"خطا در پردازش پاسخ: {str(e)}"
            }