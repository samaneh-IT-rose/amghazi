"""ابزارهای کمکی: تبدیل تاریخ شمسی، اعداد فارسی و ..."""
import jdatetime
from markupsafe import Markup, escape

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
MONTHS_JALALI = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def fa_digits(value):
    """تبدیل ارقام لاتین به فارسی"""
    return str(value).translate(PERSIAN_DIGITS)


def to_jalali(dt, with_time=False, long_month=False):
    """تبدیل datetime میلادی به رشته تاریخ شمسی"""
    if dt is None:
        return ""
    j = jdatetime.datetime.fromgregorian(datetime=dt)
    if long_month:
        text = "{} {} {}".format(j.day, MONTHS_JALALI[j.month - 1], j.year)
    else:
        text = "{}/{:02d}/{:02d}".format(j.year, j.month, j.day)
    if with_time:
        text += " - {:02d}:{:02d}".format(j.hour, j.minute)
    return fa_digits(text)


def fa_number(value):
    """عدد با جداکننده هزارگان و ارقام فارسی"""
    try:
        return fa_digits("{:,}".format(int(value)))
    except (TypeError, ValueError):
        return fa_digits(str(value))


def nl2br(value):
    """تبدیل خط جدید به <br> با escape امن"""
    if value is None:
        return Markup("")
    parts = str(escape(value)).split("\n")
    return Markup("<br>".join(parts))


def slugify(text, fallback="item"):
    """ساخت اسلاگ مناسب URL از متن فارسی"""
    import re
    text = (text or "").strip()
    # حروف فارسی حفظ می‌شوند؛ فاصله به خط تیره تبدیل می‌شود
    slug = re.sub(r"[^\w\s\u0600-\u06FF-]", "", text, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug).strip("-").lower()
    return slug[:180] or fallback
