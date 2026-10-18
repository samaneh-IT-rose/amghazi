"""ایجاد و پیکربندی اپلیکیشن Flask — سامانه امغازی"""
import os

import jdatetime
from flask import Flask, session

from .models import Admin, ContactMessage, db
from .utils import fa_digits, fa_number, nl2br, to_jalali

DEFAULT_TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "templates")
DEFAULT_STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")


def create_app(config_object="config.Config"):
    app = Flask(__name__, template_folder=DEFAULT_TEMPLATE_FOLDER, static_folder=DEFAULT_STATIC_FOLDER)
    app.config.from_object(config_object)

    # راه‌اندازی دیتابیس
    db.init_app(app)

    # ثبت فیلترهای قالب
    app.jinja_env.filters.update(
        fa=fa_digits,
        fa_num=fa_number,
        jalali=to_jalali,
        nl2br=nl2br,
    )

    # ثبت Blueprint ها
    from .routes.main import main_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # متغیرهای سراسری قالب‌ها
    @app.context_processor
    def inject_globals():
        settings = {}
        unread = 0
        try:
            from .models import Setting
            settings = Setting.get_all()
            unread = ContactMessage.query.filter_by(is_read=False).count()
        except Exception:
            pass  # قبل از ساخت دیتابیس خطا نمی‌دهیم
        return {
            "S": settings,
            "site_name": "امغازی",
            "unread_messages": unread,
            "is_admin": session.get("admin_id") is not None,
            "now_year": jdatetime.datetime.now().year,
        }

    @app.cli.command("init-db")
    def init_db_command():
        """ساخت جداول و داده اولیه از طریق: flask init-db"""
        from .seed import run_seed
        with app.app_context():
            db.create_all()
            run_seed()
        print("دیتابیس ساخته و داده اولیه ثبت شد.")

    return app


def ensure_admin(app):
    """اطمینان از وجود حساب مدیر پیش‌فرض"""
    with app.app_context():
        db.create_all()
        if Admin.query.count() == 0:
            admin = Admin(
                username=app.config["ADMIN_USERNAME"],
                name=app.config["ADMIN_NAME"],
            )
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
