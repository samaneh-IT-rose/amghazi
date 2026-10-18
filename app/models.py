"""مدل‌های دیتابیس سامانه امغازی (SQLite + SQLAlchemy)"""
import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    """حساب کاربری مدیران پنل مدیریت"""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(120), default="مدیر سامانه")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Service(db.Model):
    """خدمات مشاوره"""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(180), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(16), default="🌿")  # ایموجی نمایشی
    short_desc = db.Column(db.String(300), default="")
    description = db.Column(db.Text, default="")  # متن کامل (HTML ساده مجاز)
    price = db.Column(db.Integer, default=0)  # تومان — صفر یعنی «تماس بگیرید»
    duration_minutes = db.Column(db.Integer, default=45)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="service", lazy="dynamic")

    @property
    def price_display(self):
        return "{:,} تومان".format(self.price) if self.price else "تماس بگیرید"


class Psychologist(db.Model):
    """روانشناسان و مشاوران"""

    __tablename__ = "psychologists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(150), default="")  # مثال: کارشناس ارشد روانشناسی بالینی
    specialty = db.Column(db.String(150), default="")  # حوزه تخصصی
    degree = db.Column(db.String(120), default="")
    bio = db.Column(db.Text, default="")
    image_url = db.Column(db.String(400), default="")  # آدرس تصویر (اختیاری)
    experience_years = db.Column(db.Integer, default=1)
    consults_count = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=4.5)  # از ۵
    languages = db.Column(db.String(200), default="فارسی")
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="psychologist", lazy="dynamic")

    @property
    def initials(self):
        """حروف اول نام برای نمایش آواتار متنی"""
        parts = (self.name or "؟").strip().split()
        return "".join(p[0] for p in parts[:2])


class Course(db.Model):
    """دوره‌های آموزشی"""

    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("psychologists.id"), nullable=True)
    summary = db.Column(db.String(400), default="")
    description = db.Column(db.Text, default="")
    price = db.Column(db.Integer, default=0)
    sessions_count = db.Column(db.Integer, default=1)
    duration_minutes = db.Column(db.Integer, default=90)
    capacity = db.Column(db.Integer, default=30)
    start_date = db.Column(db.String(30), default="")  # تاریخ شمسی به صورت متن
    format = db.Column(db.String(30), default="آنلاین")  # آنلاین / حضوری / ضبط‌شده
    icon = db.Column(db.String(16), default="🎓")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("Psychologist", backref="courses", foreign_keys=[teacher_id])

    @property
    def price_display(self):
        return "{:,} تومان".format(self.price) if self.price else "رایگان"


class Article(db.Model):
    """مقالات مجله سلامت روان"""

    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    slug = db.Column(db.String(280), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), default="عمومی")
    excerpt = db.Column(db.String(500), default="")
    content = db.Column(db.Text, default="")  # HTML ساده مجاز
    author = db.Column(db.String(120), default="تحریریه امغازی")
    reading_time = db.Column(db.Integer, default=5)  # دقیقه
    views = db.Column(db.Integer, default=0)
    icon = db.Column(db.String(16), default="📝")
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def register_view(self):
        self.views = (self.views or 0) + 1
        db.session.commit()


class Appointment(db.Model):
    """نوبت‌های رزرو مشاوره"""

    STATUS_CHOICES = {
        "pending": "در انتظار بررسی",
        "confirmed": "تأیید شده",
        "done": "انجام شده",
        "canceled": "لغو شده",
    }

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=True)
    psychologist_id = db.Column(db.Integer, db.ForeignKey("psychologists.id"), nullable=True)
    preferred_date = db.Column(db.String(30), default="")  # تاریخ پیشنهادی (شمسی)
    preferred_time = db.Column(db.String(20), default="")
    note = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def status_label(self):
        return self.STATUS_CHOICES.get(self.status, self.status)

    @property
    def tracking_code(self):
        return "AG-{:06d}".format(self.id or 0)


class ContactMessage(db.Model):
    """پیام‌های فرم تماس با ما"""

    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), default="")
    phone = db.Column(db.String(20), default="")
    subject = db.Column(db.String(200), default="")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Complaint(db.Model):
    """ثبت شکایات"""

    STATUS_CHOICES = {
        "new": "ثبت شده",
        "in_progress": "در حال بررسی",
        "resolved": "حل شده",
        "rejected": "رد شده",
    }

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(200), default="")
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="new", index=True)
    admin_note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def status_label(self):
        return self.STATUS_CHOICES.get(self.status, self.status)

    @property
    def tracking_code(self):
        return "CM-{:06d}".format(self.id or 0)


class NewsletterSubscriber(db.Model):
    """خبرنامه ایمیل"""

    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Setting(db.Model):
    """تنظیمات سایت (key/value)"""

    __tablename__ = "settings"

    key = db.Column(db.String(60), primary_key=True)
    value = db.Column(db.Text, default="")

    DEFAULTS = {
        "site_title": "امغازی | مرکز مشاوره روانشناسی",
        "tagline": "سلامت روان شما، اولویت ماست",
        "support_phone": "۰۲۱-۹۱۰۰۰۰۰۰",
        "hotline": "۱۵۴۸",
        "email": "info@amghazi.example",
        "address": "تهران، خیابان ولیعصر، مرکز مشاوره امغازی",
        "working_hours": "همه روزه ۸ صبح تا ۱۲ شب",
        "about_text": "مرکز مشاوره امغازی با هدف ارتقای سلامت روان جامعه، خدمات مشاوره تلفنی و آنلاین را با بهره‌گیری از مشاوران متخصص ارائه می‌دهد.",
        "instagram": "",
        "telegram": "",
        "footer_note": "کلیه حقوق این سامانه محفوظ است.",
    }

    @classmethod
    def get_all(cls):
        rows = {s.key: s.value for s in cls.query.all()}
        merged = dict(cls.DEFAULTS)
        merged.update(rows)
        return merged

    @classmethod
    def get(cls, key):
        row = cls.query.get(key)
        if row is not None:
            return row.value
        return cls.DEFAULTS.get(key, "")

    @classmethod
    def set(cls, key, value):
        row = cls.query.get(key)
        if row is None:
            row = cls(key=key, value=value)
            db.session.add(row)
        else:
            row.value = value
