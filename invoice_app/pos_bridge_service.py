# pos_bridge_service.py
# این فایل را روی تمام کامپیوترهای ویندوزی کپی کنید

from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import time
import logging
import os
from datetime import datetime
import sys

# ایجاد پوشه logs اگر وجود ندارد
if not os.path.exists('logs'):
    os.makedirs('logs')

# تنظیمات پیشرفته logging
log_filename = f"logs/pos_bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('POS_Bridge_Service')

app = Flask(__name__)
CORS(app)  # فعال کردن CORS برای همه دامنه‌ها


def get_local_ip():
    """دریافت IP本地 کامپیوتر"""
    try:
        # ایجاد یک اتصال تستی برای فهمیدن IP本地
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


def send_to_pos_device(ip, port, amount):
    """ارسال مستقیم به دستگاه پوز از شبکه داخلی"""
    try:
        logger.info(f"🔧 ارسال به پوز: {amount} ریال به {ip}:{port}")

        # اعتبارسنجی IP
        if not ip or not ip.count('.') == 3:
            return {'status': 'error', 'message': 'آدرس IP معتبر نیست'}

        # ساخت پیام
        amount_str = str(amount).zfill(12)
        message = f"0047RQ034PR006000000AM012{amount_str}CU003364PD0011"

        logger.info(f"📦 پیام ساخته شد: {message}")
        logger.info(f"🔢 پیام HEX: {message.encode('ascii').hex()}")

        # ایجاد سوکت و ارسال
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(20)

        logger.info(f"🔌 در حال اتصال به {ip}:{port}...")
        sock.connect((ip, port))
        logger.info("✅ اتصال موفق")

        # ارسال پیام
        bytes_sent = sock.send(message.encode('ascii'))
        logger.info(f"✅ {bytes_sent} بایت ارسال شد")

        # منتظر ماندن برای نمایش روی دستگاه
        logger.info("⏳ منتظر نمایش مبلغ روی دستگاه پوز...")
        time.sleep(3)

        # دریافت پاسخ
        response = b""
        try:
            sock.settimeout(15)
            response = sock.recv(1024)
            if response:
                logger.info(f"📥 پاسخ دریافت شد: {len(response)} بایت")
                logger.info(f"📋 محتوای پاسخ: {response.decode('ascii', errors='ignore')}")
                logger.info(f"🔢 پاسخ HEX: {response.hex()}")
            else:
                logger.warning("⚠️ پاسخ خالی از دستگاه پوز")
        except socket.timeout:
            logger.warning("⚠️ timeout در دریافت پاسخ از دستگاه پوز")
        except Exception as recv_error:
            logger.error(f"❌ خطا در دریافت پاسخ: {recv_error}")
        finally:
            sock.close()
            logger.info("🔒 اتصال بسته شد")

        response_text = response.decode('ascii', errors='ignore') if response else ""

        # تحلیل پاسخ
        status_message = "تراکنش ارسال شد"
        if len(response) == 0:
            status_message = "⚠️ دستگاه پوز پاسخی ارسال نکرد - ممکن است تراکنش در حال پردازش باشد"
        elif len(response) >= 4:
            length_part = response_text[:4]
            if length_part == "0130":
                status_message = "✅ پرداخت موفق بود"
            elif length_part == "0029":
                status_message = "❌ رمز کارت اشتباه بود"
            elif length_part == "0018":
                status_message = "⚠️ پرداخت کنسل شد"

        return {
            'status': 'success',
            'message': status_message,
            'response': response_text,
            'response_length': len(response),
            'debug': {
                'bytes_sent': bytes_sent,
                'response_hex': response.hex() if response else None
            }
        }

    except ConnectionRefusedError:
        error_msg = f"❌ اتصال رد شد - دستگاه پوز در {ip}:{port} روشن نیست یا پورت باز نیست"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}

    except socket.timeout:
        error_msg = f"⏰ اتصال timeout خورد - دستگاه پوز در {ip} پاسخ نداد"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}

    except Exception as e:
        error_msg = f"❌ خطای غیرمنتظره: {str(e)}"
        logger.error(error_msg)
        return {'status': 'error', 'message': error_msg}


@app.route('/health', methods=['GET'])
def health_check():
    """بررسی وضعیت سرویس"""
    local_ip = get_local_ip()
    return jsonify({
        'status': 'active',
        'service': 'POS Bridge Service',
        'local_ip': local_ip,
        'timestamp': datetime.now().isoformat(),
        'message': 'سرویس فعال و آماده به کار است'
    })


@app.route('/pos/payment', methods=['POST'])
def process_payment():
    """پردازش درخواست پرداخت"""
    start_time = time.time()
    try:
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'داده‌های JSON دریافت نشد'}), 400

        # دریافت پارامترها
        ip = data.get('ip')
        port = data.get('port', 1362)
        amount = data.get('amount')

        # اعتبارسنجی
        validation_errors = []
        if not ip:
            validation_errors.append('IP الزامی است')
        if not amount:
            validation_errors.append('مبلغ الزامی است')
        try:
            amount = int(amount)
            if amount <= 0:
                validation_errors.append('مبلغ باید بزرگتر از صفر باشد')
        except (ValueError, TypeError):
            validation_errors.append('مبلغ باید عدد باشد')

        if validation_errors:
            return jsonify({
                'status': 'error',
                'message': ' | '.join(validation_errors)
            }), 400

        logger.info(f"💰 درخواست پرداخت جدید: {amount:,} ریال -> {ip}:{port}")

        # ارسال به دستگاه پوز
        result = send_to_pos_device(ip, port, amount)

        # محاسبه زمان اجرا
        execution_time = round(time.time() - start_time, 2)
        result['execution_time'] = execution_time
        logger.info(f"⏱️ زمان اجرا: {execution_time} ثانیه")

        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ خطا در پردازش درخواست: {e}")
        return jsonify({
            'status': 'error',
            'message': f'خطا در پردازش درخواست: {str(e)}'
        }), 500


@app.route('/pos/test', methods=['POST'])
def test_connection():
    """تست ارتباط با دستگاه پوز"""
    try:
        data = request.get_json()
        ip = data.get('ip', '192.168.1.1')
        port = data.get('port', 1362)

        # تست با مبلغ کوچک
        test_amount = 1000  # 1000 ریال = 100 تومان

        logger.info(f"🧪 تست ارتباط با پوز: {ip}:{port}")
        result = send_to_pos_device(ip, port, test_amount)

        return jsonify({
            'test': True,
            'test_amount': test_amount,
            'test_ip': ip,
            'test_port': port,
            **result
        })

    except Exception as e:
        logger.error(f"❌ خطا در تست ارتباط: {e}")
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/info', methods=['GET'])
def service_info():
    """اطلاعات سرویس"""
    local_ip = get_local_ip()
    return jsonify({
        'service_name': 'POS Bridge Service',
        'version': '1.0',
        'local_ip': local_ip,
        'status': 'running',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'endpoints': {
            'health': '/health',
            'payment': '/pos/payment',
            'test': '/pos/test',
            'info': '/info'
        }
    })


if __name__ == '__main__':
    local_ip = get_local_ip()
    logger.info("🚀 سرویس واسط پوز راه‌اندازی شد...")
    logger.info(f"📡 در حال گوش دادن روی: http://{local_ip}:5000")
    logger.info(f"🔧 برای تست سلامت: http://{local_ip}:5000/health")
    logger.info(f"📊 برای اطلاعات سرویس: http://{local_ip}:5000/info")
    logger.info("⏹️ برای توقف سرویس: Ctrl+C")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 سرویس متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطا در راه‌اندازی سرویس: {e}")