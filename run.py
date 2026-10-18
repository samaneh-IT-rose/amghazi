"""فایل اجرای سامانه امغازی

اجرای محلی:
    python run.py

اجرای تولیدی (پیشنهادی):
    gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
"""
from app import create_app, ensure_admin
from app.models import db

app = create_app()
ensure_admin(app)


# صفحات خطا
@app.errorhandler(404)
def not_found(e):
    from flask import render_template
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    from flask import render_template
    return render_template("500.html"), 500


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
