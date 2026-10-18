"""مسیرهای بخش عمومی سایت"""
from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for

from ..models import (
    Appointment,
    Article,
    Complaint,
    ContactMessage,
    Course,
    NewsletterSubscriber,
    Psychologist,
    Service,
    Setting,
    db,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.sort_order, Service.id)
        .limit(8)
        .all()
    )
    psychologists = (
        Psychologist.query.filter_by(is_active=True)
        .order_by(Psychologist.sort_order, Psychologist.id)
        .limit(4)
        .all()
    )
    articles = (
        Article.query.filter_by(is_published=True)
        .order_by(Article.created_at.desc())
        .limit(3)
        .all()
    )
    courses = (
        Course.query.filter_by(is_active=True)
        .order_by(Course.created_at.desc())
        .limit(3)
        .all()
    )
    total_psychologists = Psychologist.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    return render_template(
        "index.html",
        services=services,
        psychologists=psychologists,
        articles=articles,
        courses=courses,
        total_psychologists=total_psychologists,
        total_appointments=total_appointments,
    )


# ----------------------------- خدمات -----------------------------

@main_bp.route("/services")
def services():
    items = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.sort_order, Service.id)
        .all()
    )
    return render_template("services.html", services=items)


@main_bp.route("/services/<slug>")
def service_detail(slug):
    item = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Service.query.filter(
        Service.is_active.is_(True), Service.id != item.id
    ).order_by(Service.sort_order).limit(4).all()
    psychologists = Psychologist.query.filter_by(is_active=True).limit(4).all()
    return render_template("service_detail.html", service=item, related=related, psychologists=psychologists)


# ------------------------- روانشناسان ---------------------------

@main_bp.route("/psychologists")
def psychologists():
    items = (
        Psychologist.query.filter_by(is_active=True)
        .order_by(Psychologist.sort_order, Psychologist.id)
        .all()
    )
    return render_template("psychologists.html", psychologists=items)


@main_bp.route("/psychologists/<int:pid>")
def psychologist_detail(pid):
    item = Psychologist.query.filter_by(id=pid, is_active=True).first_or_404()
    courses = Course.query.filter_by(teacher_id=item.id, is_active=True).all()
    return render_template("psychologist_detail.html", psychologist=item, courses=courses)


# ------------------------- دوره‌های آموزشی -----------------------

@main_bp.route("/courses")
def courses():
    items = Course.query.filter_by(is_active=True).order_by(Course.created_at.desc()).all()
    return render_template("courses.html", courses=items)


@main_bp.route("/courses/<int:cid>")
def course_detail(cid):
    item = Course.query.filter_by(id=cid, is_active=True).first_or_404()
    others = Course.query.filter(Course.is_active.is_(True), Course.id != cid).limit(3).all()
    return render_template("course_detail.html", course=item, others=others)


# ---------------------------- مقالات -----------------------------

@main_bp.route("/articles")
def articles():
    page = request.args.get("page", 1, type=int)
    category = request.args.get("cat", "").strip()
    q = Article.query.filter_by(is_published=True)
    categories = [
        c[0]
        for c in Article.query.with_entities(Article.category)
        .filter_by(is_published=True)
        .distinct()
        .all()
        if c[0]
    ]
    if category:
        q = q.filter_by(category=category)
    pagination = q.order_by(Article.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "articles.html", pagination=pagination, categories=sorted(categories), current_cat=category
    )


@main_bp.route("/articles/<slug>")
def article_detail(slug):
    item = Article.query.filter_by(slug=slug, is_published=True).first_or_404()
    item.register_view()
    related = Article.query.filter(
        Article.is_published.is_(True),
        Article.id != item.id,
        Article.category == item.category,
    ).limit(3).all()
    if not related:
        related = Article.query.filter(
            Article.is_published.is_(True), Article.id != item.id
        ).limit(3).all()
    return render_template("article_detail.html", article=item, related=related)


# ------------------------- رزرو نوبت -----------------------------

@main_bp.route("/booking", methods=["GET", "POST"])
def booking():
    services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
    psychologists = Psychologist.query.filter_by(is_active=True).order_by(Psychologist.sort_order).all()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        note = request.form.get("note", "").strip()
        service_id = request.form.get("service_id", type=int)
        psychologist_id = request.form.get("psychologist_id", type=int)
        preferred_date = request.form.get("preferred_date", "").strip()
        preferred_time = request.form.get("preferred_time", "").strip()

        errors = []
        if len(full_name) < 3:
            errors.append("نام و نام خانوادگی را کامل وارد کنید.")
        if not phone.isdigit() or len(phone) < 10:
            errors.append("شماره تماس معتبر وارد کنید (فقط رقم، حداقل ۱۰ رقم).")
        if not service_id:
            errors.append("یکی از خدمات را انتخاب کنید.")

        if errors:
            return render_template(
                "booking.html", services=services, psychologists=psychologists,
                errors=errors, form=request.form,
            )

        ap = Appointment(
            full_name=full_name,
            phone=phone,
            service_id=service_id,
            psychologist_id=psychologist_id or None,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            note=note,
        )
        db.session.add(ap)
        db.session.commit()
        return render_template(
            "booking_success.html", appointment=ap
        )

    preselect = request.args.get("service", type=int)
    return render_template(
        "booking.html", services=services, psychologists=psychologists,
        errors=None, form={}, preselect=preselect,
    )


# ------------------------- تماس و شکایات -------------------------

@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        if len(name) < 2 or len(message) < 5:
            return render_template("contact.html", error="نام و متن پیام را کامل وارد کنید.", form=request.form)
        msg = ContactMessage(
            name=name,
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            subject=request.form.get("subject", "").strip(),
            message=message,
        )
        db.session.add(msg)
        db.session.commit()
        return render_template("contact_success.html")
    return render_template("contact.html", error=None, form={})


@main_bp.route("/complaints", methods=["GET", "POST"])
def complaints():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        if len(name) < 2 or not phone.isdigit() or len(message) < 10:
            return render_template(
                "complaints.html", error="لطفاً نام، شماره تماس معتبر و شرح کامل شکایت را وارد کنید.",
                form=request.form,
            )
        c = Complaint(
            name=name,
            phone=phone,
            subject=request.form.get("subject", "").strip(),
            message=message,
        )
        db.session.add(c)
        db.session.commit()
        return render_template("complaint_success.html", complaint=c)
    return render_template("complaints.html", error=None, form={})


@main_bp.route("/complaint/track")
def complaint_track():
    code = request.args.get("code", "").strip()
    item = None
    if code.upper().startswith("CM-"):
        try:
            cid = int(code[3:])
            item = Complaint.query.get(cid)
        except ValueError:
            item = None
    return render_template("complaint_track.html", code=code, complaint=item)


# -------------------------- خبرنامه ------------------------------

@main_bp.route("/newsletter/subscribe", methods=["POST"])
def newsletter_subscribe():
    email = request.form.get("email", "").strip().lower()
    if "@" not in email or "." not in email:
        return redirect(request.referrer or url_for("main.index"))
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if not existing:
        db.session.add(NewsletterSubscriber(email=email))
        db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


# -------------------------- صفحات ثابت ---------------------------

@main_bp.route("/about")
def about():
    stats = {
        "psychologists": Psychologist.query.filter_by(is_active=True).count(),
        "appointments": Appointment.query.count(),
        "articles": Article.query.filter_by(is_published=True).count(),
        "courses": Course.query.filter_by(is_active=True).count(),
    }
    return render_template("about.html", stats=stats)


@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.route("/quality")
def quality():
    return render_template("quality.html")


# ---------------------------- جستجو ------------------------------

@main_bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    results = {"services": [], "psychologists": [], "articles": [], "courses": []}
    total = 0
    if q:
        like = "%{}%".format(q)
        results["services"] = Service.query.filter(
            Service.is_active.is_(True),
            db.or_(Service.title.like(like), Service.short_desc.like(like)),
        ).limit(10).all()
        results["psychologists"] = Psychologist.query.filter(
            Psychologist.is_active.is_(True),
            db.or_(Psychologist.name.like(like), Psychologist.specialty.like(like), Psychologist.title.like(like)),
        ).limit(10).all()
        results["articles"] = Article.query.filter(
            Article.is_published.is_(True),
            db.or_(Article.title.like(like), Article.excerpt.like(like)),
        ).limit(10).all()
        results["courses"] = Course.query.filter(
            Course.is_active.is_(True),
            db.or_(Course.title.like(like), Course.summary.like(like)),
        ).limit(10).all()
        total = sum(len(v) for v in results.values())
    return render_template("search.html", q=q, results=results, total=total)
