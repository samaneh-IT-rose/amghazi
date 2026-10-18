"""مسیرهای پنل مدیریت (Admin Panel)"""
import functools
import csv
import io

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request,
    session, url_for, Response,
)

from ..models import (
    Admin, Appointment, Article, Complaint, ContactMessage, Course,
    NewsletterSubscriber, Psychologist, Service, Setting, db,
)
from ..utils import slugify

admin_bp = Blueprint("admin", __name__)


# --------------------------- ابزارها ------------------------------

def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("admin_id") is None:
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def get_current_admin():
    from ..models import Admin
    if session.get("admin_id") is None:
        return None
    return Admin.query.get(session["admin_id"])


def unique_slug(model, text, current_id=None):
    """ساخت اسلاگ یکتا برای مدل داده"""
    base = slugify(text, fallback="item")
    slug, i = base, 2
    while True:
        q = model.query.filter_by(slug=slug)
        if current_id:
            q = q.filter(model.id != current_id)
        if q.first() is None:
            return slug
        slug = "{}-{}".format(base, i)
        i += 1


def csv_response(headers, rows, filename):
    """خروجی CSV با انکودینگ سازگار با اکسل فارسی"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    data = "\ufeff" + buf.getvalue()
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename={}".format(filename)},
    )


# --------------------------- ورود/خروج ----------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id") is not None:
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            session["admin_name"] = admin.name
            session.permanent = True
            nxt = request.args.get("next") or url_for("admin.dashboard")
            if not nxt.startswith("/admin"):
                nxt = url_for("admin.dashboard")
            return redirect(nxt)
        error = "نام کاربری یا رمز عبور اشتباه است."
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


# --------------------------- داشبورد ------------------------------

@admin_bp.route("/")
@login_required
def dashboard():
    stats = {
        "services": Service.query.count(),
        "psychologists": Psychologist.query.count(),
        "articles": Article.query.count(),
        "courses": Course.query.count(),
        "appointments": Appointment.query.count(),
        "pending_appointments": Appointment.query.filter_by(status="pending").count(),
        "messages": ContactMessage.query.count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "complaints": Complaint.query.count(),
        "new_complaints": Complaint.query.filter_by(status="new").count(),
        "newsletter": NewsletterSubscriber.query.count(),
    }
    latest_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
    latest_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    latest_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()

    # آمار نوبت‌ها به تفکیک وضعیت برای نمودار
    status_counts = {
        label: Appointment.query.filter_by(status=code).count()
        for code, label in Appointment.STATUS_CHOICES.items()
    }
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        latest_appointments=latest_appointments,
        latest_messages=latest_messages,
        latest_complaints=latest_complaints,
        status_counts=status_counts,
    )


# --------------------------- خدمات -------------------------------

@admin_bp.route("/services")
@login_required
def services():
    items = Service.query.order_by(Service.sort_order, Service.id).all()
    return render_template("admin/services.html", services=items)


@admin_bp.route("/services/new", methods=["GET", "POST"])
@login_required
def service_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) < 2:
            flash("عنوان خدمت را وارد کنید.", "error")
            return render_template("admin/service_form.html", item=None)
        item = Service(
            title=title,
            slug=unique_slug(Service, title),
            icon=request.form.get("icon", "🌿").strip() or "🌿",
            short_desc=request.form.get("short_desc", "").strip(),
            description=request.form.get("description", "").strip(),
            price=request.form.get("price", 0, type=int),
            duration_minutes=request.form.get("duration_minutes", 45, type=int),
            is_active=bool(request.form.get("is_active")),
            sort_order=request.form.get("sort_order", 0, type=int),
        )
        db.session.add(item)
        db.session.commit()
        flash("خدمت جدید با موفقیت ثبت شد.", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_form.html", item=None)


@admin_bp.route("/services/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def service_edit(item_id):
    item = Service.query.get_or_404(item_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) >= 2:
            item.title = title
            item.slug = unique_slug(Service, title, item.id)
            item.icon = request.form.get("icon", "🌿").strip() or "🌿"
            item.short_desc = request.form.get("short_desc", "").strip()
            item.description = request.form.get("description", "").strip()
            item.price = request.form.get("price", 0, type=int)
            item.duration_minutes = request.form.get("duration_minutes", 45, type=int)
            item.is_active = bool(request.form.get("is_active"))
            item.sort_order = request.form.get("sort_order", 0, type=int)
            db.session.commit()
            flash("تغییرات ذخیره شد.", "success")
            return redirect(url_for("admin.services"))
        flash("عنوان خدمت را وارد کنید.", "error")
    return render_template("admin/service_form.html", item=item)


@admin_bp.route("/services/<int:item_id>/delete", methods=["POST"])
@login_required
def service_delete(item_id):
    item = Service.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash("خدمت حذف شد.", "success")
    except Exception:
        db.session.rollback()
        flash("حذف ممکن نیست؛ ابتدا نوبت‌های مرتبط را مدیریت کنید.", "error")
    return redirect(url_for("admin.services"))


# ------------------------- روانشناسان ----------------------------

@admin_bp.route("/psychologists")
@login_required
def psychologists():
    items = Psychologist.query.order_by(Psychologist.sort_order, Psychologist.id).all()
    return render_template("admin/psychologists.html", psychologists=items)


@admin_bp.route("/psychologists/new", methods=["GET", "POST"])
@login_required
def psychologist_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if len(name) < 3:
            flash("نام مشاور را وارد کنید.", "error")
            return render_template("admin/psychologist_form.html", item=None, courses=[])
        item = Psychologist(
            name=name,
            title=request.form.get("title", "").strip(),
            specialty=request.form.get("specialty", "").strip(),
            degree=request.form.get("degree", "").strip(),
            bio=request.form.get("bio", "").strip(),
            image_url=request.form.get("image_url", "").strip(),
            experience_years=request.form.get("experience_years", 1, type=int),
            consults_count=request.form.get("consults_count", 0, type=int),
            rating=min(5.0, max(0.0, request.form.get("rating", 4.5, type=float))),
            languages=request.form.get("languages", "فارسی").strip(),
            is_active=bool(request.form.get("is_active")),
            sort_order=request.form.get("sort_order", 0, type=int),
        )
        db.session.add(item)
        db.session.commit()
        flash("مشاور جدید ثبت شد.", "success")
        return redirect(url_for("admin.psychologists"))
    return render_template("admin/psychologist_form.html", item=None)


@admin_bp.route("/psychologists/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def psychologist_edit(item_id):
    item = Psychologist.query.get_or_404(item_id)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if len(name) >= 3:
            item.name = name
            item.title = request.form.get("title", "").strip()
            item.specialty = request.form.get("specialty", "").strip()
            item.degree = request.form.get("degree", "").strip()
            item.bio = request.form.get("bio", "").strip()
            item.image_url = request.form.get("image_url", "").strip()
            item.experience_years = request.form.get("experience_years", 1, type=int)
            item.consults_count = request.form.get("consults_count", 0, type=int)
            item.rating = min(5.0, max(0.0, request.form.get("rating", 4.5, type=float)))
            item.languages = request.form.get("languages", "فارسی").strip()
            item.is_active = bool(request.form.get("is_active"))
            item.sort_order = request.form.get("sort_order", 0, type=int)
            db.session.commit()
            flash("تغییرات ذخیره شد.", "success")
            return redirect(url_for("admin.psychologists"))
        flash("نام مشاور را وارد کنید.", "error")
    return render_template("admin/psychologist_form.html", item=item)


@admin_bp.route("/psychologists/<int:item_id>/delete", methods=["POST"])
@login_required
def psychologist_delete(item_id):
    item = Psychologist.query.get_or_404(item_id)
    Course.query.filter_by(teacher_id=item.id).update({"teacher_id": None})
    db.session.delete(item)
    db.session.commit()
    flash("مشاور حذف شد.", "success")
    return redirect(url_for("admin.psychologists"))


# --------------------------- مقالات ------------------------------

@admin_bp.route("/articles")
@login_required
def articles():
    page = request.args.get("page", 1, type=int)
    pagination = Article.query.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template("admin/articles.html", pagination=pagination)


@admin_bp.route("/articles/new", methods=["GET", "POST"])
@login_required
def article_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) < 3:
            flash("عنوان مقاله را وارد کنید.", "error")
            return render_template("admin/article_form.html", item=None)
        item = Article(
            title=title,
            slug=unique_slug(Article, title),
            category=request.form.get("category", "عمومی").strip() or "عمومی",
            excerpt=request.form.get("excerpt", "").strip(),
            content=request.form.get("content", "").strip(),
            author=request.form.get("author", "تحریریه امغازی").strip() or "تحریریه امغازی",
            reading_time=request.form.get("reading_time", 5, type=int),
            icon=request.form.get("icon", "📝").strip() or "📝",
            is_published=bool(request.form.get("is_published")),
        )
        db.session.add(item)
        db.session.commit()
        flash("مقاله منتشر شد.", "success")
        return redirect(url_for("admin.articles"))
    return render_template("admin/article_form.html", item=None)


@admin_bp.route("/articles/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def article_edit(item_id):
    item = Article.query.get_or_404(item_id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) >= 3:
            item.title = title
            item.slug = unique_slug(Article, title, item.id)
            item.category = request.form.get("category", "عمومی").strip() or "عمومی"
            item.excerpt = request.form.get("excerpt", "").strip()
            item.content = request.form.get("content", "").strip()
            item.author = request.form.get("author", "").strip() or item.author
            item.reading_time = request.form.get("reading_time", 5, type=int)
            item.icon = request.form.get("icon", "📝").strip() or "📝"
            item.is_published = bool(request.form.get("is_published"))
            db.session.commit()
            flash("تغییرات ذخیره شد.", "success")
            return redirect(url_for("admin.articles"))
        flash("عنوان مقاله را وارد کنید.", "error")
    return render_template("admin/article_form.html", item=item)


@admin_bp.route("/articles/<int:item_id>/delete", methods=["POST"])
@login_required
def article_delete(item_id):
    item = Article.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("مقاله حذف شد.", "success")
    return redirect(url_for("admin.articles"))


# ----------------------- دوره‌های آموزشی -------------------------

@admin_bp.route("/courses")
@login_required
def courses():
    items = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin/courses.html", courses=items)


@admin_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
def course_new():
    teachers = Psychologist.query.order_by(Psychologist.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) < 3:
            flash("عنوان دوره را وارد کنید.", "error")
            return render_template("admin/course_form.html", item=None, teachers=teachers)
        item = Course(
            title=title,
            teacher_id=request.form.get("teacher_id", type=int) or None,
            summary=request.form.get("summary", "").strip(),
            description=request.form.get("description", "").strip(),
            price=request.form.get("price", 0, type=int),
            sessions_count=request.form.get("sessions_count", 1, type=int),
            duration_minutes=request.form.get("duration_minutes", 90, type=int),
            capacity=request.form.get("capacity", 30, type=int),
            start_date=request.form.get("start_date", "").strip(),
            format=request.form.get("format", "آنلاین").strip(),
            icon=request.form.get("icon", "🎓").strip() or "🎓",
            is_active=bool(request.form.get("is_active")),
        )
        db.session.add(item)
        db.session.commit()
        flash("دوره جدید ثبت شد.", "success")
        return redirect(url_for("admin.courses"))
    return render_template("admin/course_form.html", item=None, teachers=teachers)


@admin_bp.route("/courses/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def course_edit(item_id):
    item = Course.query.get_or_404(item_id)
    teachers = Psychologist.query.order_by(Psychologist.name).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if len(title) >= 3:
            item.title = title
            item.teacher_id = request.form.get("teacher_id", type=int) or None
            item.summary = request.form.get("summary", "").strip()
            item.description = request.form.get("description", "").strip()
            item.price = request.form.get("price", 0, type=int)
            item.sessions_count = request.form.get("sessions_count", 1, type=int)
            item.duration_minutes = request.form.get("duration_minutes", 90, type=int)
            item.capacity = request.form.get("capacity", 30, type=int)
            item.start_date = request.form.get("start_date", "").strip()
            item.format = request.form.get("format", "آنلاین").strip()
            item.icon = request.form.get("icon", "🎓").strip() or "🎓"
            item.is_active = bool(request.form.get("is_active"))
            db.session.commit()
            flash("تغییرات ذخیره شد.", "success")
            return redirect(url_for("admin.courses"))
        flash("عنوان دوره را وارد کنید.", "error")
    return render_template("admin/course_form.html", item=item, teachers=teachers)


@admin_bp.route("/courses/<int:item_id>/delete", methods=["POST"])
@login_required
def course_delete(item_id):
    item = Course.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("دوره حذف شد.", "success")
    return redirect(url_for("admin.courses"))


# --------------------------- نوبت‌ها ------------------------------

@admin_bp.route("/appointments")
@login_required
def appointments():
    status = request.args.get("status", "").strip()
    q = Appointment.query
    if status:
        q = q.filter_by(status=status)
    page = request.args.get("page", 1, type=int)
    pagination = q.order_by(Appointment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/appointments.html", pagination=pagination, current_status=status)


@admin_bp.route("/appointments/<int:item_id>/status", methods=["POST"])
@login_required
def appointment_status(item_id):
    item = Appointment.query.get_or_404(item_id)
    new_status = request.form.get("status", "")
    if new_status in Appointment.STATUS_CHOICES:
        item.status = new_status
        db.session.commit()
        flash("وضعیت نوبت به «{}» تغییر یافت.".format(item.status_label), "success")
    return redirect(request.referrer or url_for("admin.appointments"))


@admin_bp.route("/appointments/<int:item_id>/delete", methods=["POST"])
@login_required
def appointment_delete(item_id):
    item = Appointment.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("نوبت حذف شد.", "success")
    return redirect(request.referrer or url_for("admin.appointments"))


@admin_bp.route("/appointments/export")
@login_required
def appointments_export():
    rows = [
        [
            ap.tracking_code, ap.full_name, ap.phone,
            ap.service.title if ap.service else "-", ap.psychologist.name if ap.psychologist else "-",
            ap.preferred_date, ap.preferred_time, ap.status_label, ap.note or "",
        ]
        for ap in Appointment.query.order_by(Appointment.created_at.desc()).all()
    ]
    return csv_response(
        ["کد پیگیری", "نام", "تلفن", "خدمت", "مشاور", "تاریخ پیشنهادی", "ساعت", "وضعیت", "توضیحات"],
        rows,
        "appointments.csv",
    )


# --------------------------- پیام‌ها ------------------------------

@admin_bp.route("/messages")
@login_required
def messages():
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("admin/messages.html", pagination=pagination)


@admin_bp.route("/messages/<int:item_id>/toggle", methods=["POST"])
@login_required
def message_toggle(item_id):
    item = ContactMessage.query.get_or_404(item_id)
    item.is_read = not item.is_read
    db.session.commit()
    return redirect(request.referrer or url_for("admin.messages"))


@admin_bp.route("/messages/<int:item_id>/delete", methods=["POST"])
@login_required
def message_delete(item_id):
    item = ContactMessage.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("پیام حذف شد.", "success")
    return redirect(request.referrer or url_for("admin.messages"))


# --------------------------- شکایات ------------------------------

@admin_bp.route("/complaints")
@login_required
def complaints():
    status = request.args.get("status", "").strip()
    q = Complaint.query
    if status:
        q = q.filter_by(status=status)
    page = request.args.get("page", 1, type=int)
    pagination = q.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/complaints.html", pagination=pagination, current_status=status)


@admin_bp.route("/complaints/<int:item_id>/update", methods=["POST"])
@login_required
def complaint_update(item_id):
    item = Complaint.query.get_or_404(item_id)
    new_status = request.form.get("status", "")
    if new_status in Complaint.STATUS_CHOICES:
        item.status = new_status
    item.admin_note = request.form.get("admin_note", "").strip()
    db.session.commit()
    flash("شکایت به‌روزرسانی شد.", "success")
    return redirect(request.referrer or url_for("admin.complaints"))


@admin_bp.route("/complaints/<int:item_id>/delete", methods=["POST"])
@login_required
def complaint_delete(item_id):
    item = Complaint.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("شکایت حذف شد.", "success")
    return redirect(request.referrer or url_for("admin.complaints"))


# -------------------------- خبرنامه ------------------------------

@admin_bp.route("/newsletter")
@login_required
def newsletter():
    items = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    return render_template("admin/newsletter.html", subscribers=items)


@admin_bp.route("/newsletter/export")
@login_required
def newsletter_export():
    rows = [[s.email] for s in NewsletterSubscriber.query.all()]
    return csv_response(["ایمیل"], rows, "newsletter.csv")


@admin_bp.route("/newsletter/<int:item_id>/delete", methods=["POST"])
@login_required
def newsletter_delete(item_id):
    item = NewsletterSubscriber.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("عضو حذف شد.", "success")
    return redirect(url_for("admin.newsletter"))


# ------------------------- تنظیمات -------------------------------

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    tab = request.args.get("tab", "site")
    if request.method == "POST":
        form_type = request.form.get("form_type", "site")
        if form_type == "site":
            editable_keys = [
                "site_title", "tagline", "support_phone", "hotline", "email",
                "address", "working_hours", "about_text", "instagram", "telegram", "footer_note",
            ]
            for key in editable_keys:
                if key in request.form:
                    Setting.set(key, request.form.get(key, "").strip())
            db.session.commit()
            flash("تنظیمات سایت ذخیره شد.", "success")
            tab = "site"
        elif form_type == "password":
            current = get_current_admin()
            old_password = request.form.get("old_password", "")
            new_password = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not current or not current.check_password(old_password):
                flash("رمز عبور فعلی اشتباه است.", "error")
            elif len(new_password) < 6:
                flash("رمز جدید باید حداقل ۶ کاراکتر باشد.", "error")
            elif new_password != confirm:
                flash("تکرار رمز جدید مطابقت ندارد.", "error")
            else:
                current.set_password(new_password)
                db.session.commit()
                flash("رمز عبور با موفقیت تغییر یافت.", "success")
            tab = "account"
    return render_template("admin/settings.html", settings=Setting.get_all(), tab=tab)
