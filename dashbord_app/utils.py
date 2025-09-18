def convert_persian_arabic_to_english(text):
    """
    تبدیل اعداد فارسی و عربی به انگلیسی
    """
    if not text:
        return text

    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    arabic_numbers = '٠١٢٣٤٥٦٧٨٩'
    english_numbers = '0123456789'

    translation_table = str.maketrans(persian_numbers + arabic_numbers, english_numbers * 2)
    return text.translate(translation_table)