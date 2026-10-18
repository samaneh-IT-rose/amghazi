"""پیکربندی اصلی برنامه «امغازی» — سامانه مشاوره و مدیریت محتوا"""
import os

# پوشه ریشه پروژه (محل قرارگیری همین فایل config.py)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """تنظیمات پایه برنامه"""

    # کلید امنیتی — در محیط عملیاتی حتماً از متغیر محیطی مقداردهی کنید
    SECRET_KEY = os.environ.get("SECRET_KEY", "amghazi-change-this-secret-key-in-production")

    # مسیر دیتابیس SQLite
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "amghazi.db"))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DATABASE_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # نام سایت
    SITE_NAME = "امغازی"
    SITE_TAGLINE = "مرکز مشاوره روانشناسی و سلامت روان"

    # نام کاربری و رمز عبور پیش‌فرض مدیر (فقط بار اول ساخته می‌شود)
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    ADMIN_NAME = os.environ.get("ADMIN_NAME", "مدیر سامانه")

    # اندازه مجاز آپلود فایل (بایت) — ۵ مگابایت
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # تعداد آیتم در هر صفحه (صفحه‌بندی)
    ITEMS_PER_PAGE = 9
