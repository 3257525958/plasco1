from django import template

register = template.Library()


@register.filter(name='convert_to_words')
def convert_to_words(value):
    try:
        number = int(float(value))
    except (ValueError, TypeError):
        return ""

    ones = ['', 'یک', 'دو', 'سه', 'چهار', 'پنج', 'شش', 'هفت', 'هشت', 'نه']
    teens = ['ده', 'یازده', 'دوازده', 'سیزده', 'چهارده', 'پانزده', 'شانزده', 'هفده', 'هجده', 'نوزده']
    tens = ['', '', 'بیست', 'سی', 'چهل', 'پنجاه', 'شصت', 'هفتاد', 'هشتاد', 'نود']
    hundreds = ['', 'صد', 'دویست', 'سیصد', 'چهارصد', 'پانصد', 'ششصد', 'هفتصد', 'هشتصد', 'نهصد']
    thousands = ['', 'هزار', 'میلیون', 'میلیارد']

    if number == 0:
        return 'صفر'

    if number < 0:
        return 'منفی ' + convert_to_words(abs(number))

    words = ''
    index = 0

    while number > 0:
        part = number % 1000
        if part > 0:
            part_words = ''

            # صدگان
            if part >= 100:
                part_words += hundreds[part // 100] + ' و '
                part %= 100

            # دهگان و یکان
            if part >= 20:
                part_words += tens[part // 10] + ' و '
                part %= 10
            elif part >= 10:
                part_words += teens[part - 10] + ' و '
                part = 0

            if part > 0:
                part_words += ones[part] + ' و '

            # حذف " و " آخر
            part_words = part_words.rstrip(' و ')

            words = part_words + ' ' + thousands[index] + ' ' + words

        index += 1
        number //= 1000

    return words.strip() + ' تومان'