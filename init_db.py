"""راه‌اندازی اولیه سامانه امغازی

اجرا:
    python init_db.py

این اسکریپت:
  ۱) جداول دیتابیس SQLite را می‌سازد
  ۲) حساب مدیر پیش‌فرض (admin / admin123) را ایجاد می‌کند
  ۳) داده‌های نمونه (خدمات، مشاوران، مقالات، دوره‌ها) را درج می‌کند
"""
from app import create_app, ensure_admin
from app.models import db
from app.seed import run_seed


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        ensure_admin(app)
        run_seed()
    print("=" * 50)
    print("دیتابیس با موفقیت ساخته شد: amghazi.db")
    print("نام کاربری مدیر: admin")
    print("رمز عبور مدیر:   admin123")
    print("⚠ پس از اولین ورود، رمز را از بخش تنظیمات تغییر دهید.")
    print("=" * 50)


if __name__ == "__main__":
    main()
