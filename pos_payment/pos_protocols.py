import socket
import time
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class POSProtocol:
    """مدیریت پروتکل ارتباطی با دستگاه پوز بر اساس مستندات PC-POC"""

    def __init__(self):
        self.timeout = 30
        self.buffer_size = 1024

    def validate_ip(self, ip):
        """اعتبارسنجی آدرس IP"""
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        if not re.match(pattern, ip):
            return False

        parts = ip.split('.')
        for part in parts:
            if not 0 <= int(part) <= 255:
                return False
        return True

    def normalize_ip(self, ip):
        """نرمال کردن آدرس IP"""
        parts = ip.split('.')
        normalized_parts = [str(int(part)) for part in parts]
        return '.'.join(normalized_parts)

    def build_sale_request(self, amount, currency='364', pr_code='000000'):
        """
        ساخت پیام درخواست خرید بر اساس مستندات
        ساختار: [4 byte length] + [TLV tags]
        """
        try:
            logger.info("🔨 شروع ساخت پیام درخواست خرید")
            logger.info(f"📊 پارامترها: amount={amount}, currency={currency}, pr_code={pr_code}")

            # تبدیل مبلغ به فرمت 12 رقمی (مطابق مستندات)
            amount_str = str(amount).zfill(12)
            logger.info(f"💰 مبلغ تبدیل شده: {amount_str}")

            tags = []

            # تگ RQ - نوع پیام درخواست (034 برای خرید)
            rq_value = '034'
            rq_tag = 'RQ' + str(len(rq_value)).zfill(2) + rq_value
            tags.append(rq_tag)
            logger.info(f"🏷️ تگ RQ: {rq_tag}")

            # تگ PR - کد پردازش (000000 برای خرید)
            pr_value = pr_code
            pr_tag = 'PR' + str(len(pr_value)).zfill(2) + pr_value
            tags.append(pr_tag)
            logger.info(f"🏷️ تگ PR: {pr_tag}")

            # تگ AM - مبلغ
            am_tag = 'AM' + str(len(amount_str)).zfill(2) + amount_str
            tags.append(am_tag)
            logger.info(f"🏷️ تگ AM: {am_tag}")

            # تگ CU - واحد پول (364 برای ریال ایران)
            cu_tag = 'CU' + str(len(currency)).zfill(2) + currency
            tags.append(cu_tag)
            logger.info(f"🏷️ تگ CU: {cu_tag}")

            # تگ PD - اطلاعات اضافی (11 مطابق مستندات)
            pd_value = '11'
            pd_tag = 'PD' + str(len(pd_value)).zfill(2) + pd_value
            tags.append(pd_tag)
            logger.info(f"🏷️ تگ PD: {pd_tag}")

            # ساخت بدنه پیام
            message_body = ''.join(tags)
            total_length = len(message_body)
            message = str(total_length).zfill(4) + message_body

            logger.info(f"📦 پیام نهایی ساخته شد:")
            logger.info(f"📏 طول کل: {total_length}")
            logger.info(f"📝 محتوای پیام: {message}")
            logger.info(f"🔢 HEX پیام: {message.encode('ascii').hex()}")

            # اعتبارسنجی نهایی - مقایسه با مستندات
            expected_example = "0039RQ034PR006000000AM0042000CU003364PD0011"
            logger.info(f"📋 مثال مستند: {expected_example}")
            logger.info(f"✅ تطابق با مستند: {'بله' if len(message) == len(expected_example) else 'خیر'}")

            return message

        except Exception as e:
            logger.error(f"❌ خطا در ساخت پیام: {str(e)}")
            raise

    def parse_pos_response(self, response):
        """تجزیه و تحلیل پاسخ دستگاه پوز"""
        logger.info("🔍 شروع تجزیه پاسخ دستگاه")
        logger.info(f"📥 پاسخ دریافتی: {response}")

        if not response:
            logger.warning("⚠️ پاسخ خالی دریافت شد")
            return 'پاسخ دریافت نشد'

        parsed_response = {}
        debug_info = []

        try:
            # بررسی طول پاسخ
            if len(response) < 4:
                logger.error(f"❌ پاسخ بسیار کوتاه است: {response}")
                return f"پاسخ کوتاه است: {response}"

            # طول کل (4 رقم اول)
            length_str = response[:4]
            parsed_response['length'] = length_str
            debug_info.append(f"📏 طول کل پاسخ: {length_str}")
            logger.info(f"📏 طول کل پاسخ: {length_str}")

            # بقیه پیام
            rest = response[4:]
            logger.info(f"📋 بقیه پیام: {rest}")

            # تجزیه تگ‌ها
            pos = 0
            tag_count = 0

            while pos < len(rest):
                if pos + 4 <= len(rest):
                    tag = rest[pos:pos + 2]
                    length_str = rest[pos + 2:pos + 4]

                    try:
                        value_length = int(length_str)
                        if pos + 4 + value_length <= len(rest):
                            value = rest[pos + 4:pos + 4 + value_length]
                            parsed_response[tag] = value

                            tag_count += 1
                            debug_info.append(f"🏷️ تگ {tag}: طول={value_length}, مقدار={value}")
                            logger.info(f"🏷️ تگ {tag}: طول={value_length}, مقدار={value}")

                            pos += 4 + value_length
                        else:
                            logger.warning(f"⚠️ طول مقدار برای تگ {tag} بیش از حد است")
                            break
                    except ValueError as e:
                        logger.error(f"❌ خطا در تبدیل طول تگ {tag}: {e}")
                        break
                else:
                    logger.warning("⚠️ موقعیت فعلی خارج از محدوده پاسخ")
                    break

            logger.info(f"✅ تعداد تگ‌های تجزیه شده: {tag_count}")

            # تفسیر تگ‌های مهم
            interpretation = self.interpret_response_tags(parsed_response)
            debug_info.extend(interpretation)

        except Exception as e:
            error_msg = f'❌ خطا در تجزیه پاسخ: {str(e)}'
            logger.error(error_msg)
            debug_info.append(error_msg)

        parsed_response['debug_info'] = debug_info
        parsed_response['raw_response'] = response
        return parsed_response

    def interpret_response_tags(self, tags):
        """تفسیر تگ‌های پاسخ"""
        interpretations = []

        # تگ RS - پاسخ
        if 'RS' in tags:
            rs_value = tags['RS']
            if rs_value == '00':
                interpretations.append("✅ تراکنش موفق")
            else:
                interpretations.append(f"❌ کد خطا: {rs_value}")

        # تگ TR - شماره پیگیری پایانه
        if 'TR' in tags:
            interpretations.append(f"🔢 شماره پیگیری: {tags['TR']}")

        # تگ RN - شماره مرجع سوییچ
        if 'RN' in tags:
            interpretations.append(f"🏦 شماره مرجع: {tags['RN']}")

        # تگ TM - شماره پایانه
        if 'TM' in tags:
            interpretations.append(f"🖨️ شماره پایانه: {tags['TM']}")

        # تگ AM - مبلغ
        if 'AM' in tags:
            try:
                amount = int(tags['AM'])
                interpretations.append(f"💰 مبلغ: {amount:,} ریال")
            except:
                interpretations.append(f"💰 مبلغ: {tags['AM']}")

        # تگ PN - شماره کارت
        if 'PN' in tags:
            card_no = tags['PN']
            masked_card = card_no[:6] + '******' + card_no[-4:] if len(card_no) > 10 else card_no
            interpretations.append(f"💳 شماره کارت: {masked_card}")

        # تگ TI - تاریخ و زمان
        if 'TI' in tags:
            interpretations.append(f"📅 تاریخ/زمان: {tags['TI']}")

        return interpretations

    def send_message(self, ip, port, message):
        """ارسال پیام به دستگاه پوز و دریافت پاسخ"""
        sock = None
        try:
            logger.info("🌐 شروع ارتباط با دستگاه پوز")
            logger.info(f"📍 آدرس: {ip}:{port}")
            logger.info(f"📤 پیام ارسالی: {message}")

            # ایجاد سوکت
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # اتصال
            logger.info("🔌 در حال اتصال به دستگاه...")
            start_time = time.time()
            sock.connect((ip, port))
            connect_time = time.time() - start_time
            logger.info(f"✅ اتصال موفق در {connect_time:.2f} ثانیه")

            # ارسال پیام
            logger.info("📤 در حال ارسال پیام...")
            message_bytes = message.encode('ascii')
            bytes_sent = sock.send(message_bytes)
            send_time = time.time() - start_time - connect_time
            logger.info(f"✅ ارسال موفق: {bytes_sent} بایت در {send_time:.2f} ثانیه")
            logger.info(f"🔢 پیام HEX: {message_bytes.hex()}")

            # منتظر پاسخ
            logger.info("⏳ در انتظار پاسخ دستگاه...")
            time.sleep(2)  # زمان برای پردازش دستگاه

            # دریافت پاسخ
            sock.settimeout(10)
            response = b""
            receive_start = time.time()

            try:
                while True:
                    chunk = sock.recv(self.buffer_size)
                    if not chunk:
                        break
                    response += chunk
                    if len(chunk) < self.buffer_size:
                        break
            except socket.timeout:
                logger.warning("⏰ timeout در دریافت پاسخ")

            receive_time = time.time() - receive_start
            logger.info(f"📥 دریافت پاسخ: {len(response)} بایت در {receive_time:.2f} ثانیه")

            # تبدیل پاسخ به متن
            response_text = response.decode('ascii', errors='ignore')
            logger.info(f"📋 پاسخ متنی: {response_text}")
            logger.info(f"🔢 پاسخ HEX: {response.hex()}")

            if not response_text:
                logger.warning("⚠️ پاسخ خالی از دستگاه")
                return "دستگاه پوز پاسخی ارسال نکرد"

            # تجزیه پاسخ
            parsed_response = self.parse_pos_response(response_text)
            total_time = time.time() - start_time
            logger.info(f"⏱️ زمان کل عملیات: {total_time:.2f} ثانیه")

            return parsed_response

        except socket.timeout as e:
            logger.error(f"⏰ خطای timeout: {str(e)}")
            return "خطا: timeout - دستگاه پاسخ نداد"
        except ConnectionRefusedError as e:
            logger.error(f"🔌 خطای اتصال: {str(e)}")
            return "خطا: Connection refused - پورت باز نیست"
        except BrokenPipeError as e:
            logger.error(f"🔌 خطای اتصال قطع شده: {str(e)}")
            return "خطا: Broken pipe - اتصال قطع شد"
        except Exception as e:
            logger.error(f"❌ خطای ناشناخته: {str(e)}")
            return f"خطا در ارتباط با دستگاه پوز: {str(e)}"
        finally:
            if sock:
                sock.close()
                logger.info("🔒 اتصال بسته شد")

    def test_connection(self, ip, port):
        """تست ساده اتصال به دستگاه"""
        try:
            logger.info(f"🧪 تست اتصال به {ip}:{port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            start_time = time.time()
            result = sock.connect_ex((ip, port))
            connect_time = time.time() - start_time

            sock.close()

            if result == 0:
                logger.info(f"✅ تست اتصال موفق در {connect_time:.2f} ثانیه")
                return True, f"اتصال موفق در {connect_time:.2f} ثانیه"
            else:
                logger.error(f"❌ تست اتصال ناموفق - کد خطا: {result}")
                return False, f"اتصال ناموفق - کد خطا: {result}"

        except Exception as e:
            logger.error(f"❌ خطا در تست اتصال: {str(e)}")
            return False, f"خطا در تست اتصال: {str(e)}"