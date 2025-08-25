import re


def convert_persian_to_english(text):
    if not text:
        return text

    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }

    for persian, english in persian_to_english.items():
        text = text.replace(persian, english)

    return text


def validate_persian_text(text):
    # بررسی متن فارسی (حداقل 2 حرف)
    if not text or len(text.strip()) < 2:
        return False

    # حذف فاصله و بررسی طول
    text_without_spaces = text.replace(' ', '')
    if len(text_without_spaces) < 2:
        return False

    return True