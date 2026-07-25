import os
from functools import wraps

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # For type checkers and editors
    from flask import (
        Flask, render_template, request, redirect, url_for, flash, session, abort
    )
else:
    try:
        from flask import (
            Flask, render_template, request, redirect, url_for, flash, session, abort
        )
    except ImportError as e:
        raise ImportError(
            "Flask is not installed. Install it with 'pip install flask' to run this application."
        ) from e

from models import db, AdminUser, Product, ContactMessage, Setting, DEFAULT_SETTINGS

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        BASE_DIR, "instance", "dwit_farm.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_defaults()

    register_public_routes(app)
    register_admin_routes(app)

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_defaults():
    """Populate default settings + starter products the first time the app runs."""
    for key, value in DEFAULT_SETTINGS.items():
        if not Setting.query.get(key):
            db.session.add(Setting(key=key, value=value))

    if Product.query.count() == 0:
        starter_products = [
            Product(
                name="Gavran Chicken", tag="Desi & Gavran", tag_color="red",
                art_bg="#FBE3E1",
                description="Naturally raised, free-range chicken with authentic Gavran "
                             "flavour. Sold whole or cut to order.",
                cta_label="Order Now",
                whatsapp_message="I want to order Gavran Chicken",
                sort_order=1,
            ),
            Product(
                name="Farm-Fresh Eggs", tag="Daily Fresh", tag_color="yellow",
                art_bg="#FCEFCD",
                description="Desi eggs collected daily — natural diet, no dyes, no "
                             "preservatives. Sold by the dozen.",
                cta_label="Order Now",
                whatsapp_message="I want to order Farm-Fresh Eggs",
                sort_order=2,
            ),
            Product(
                name="Parent Stock & Chicks", tag="For Farmers", tag_color="blue",
                art_bg="#DDEBFA",
                description="Healthy day-old chicks and breeding birds for anyone "
                             "starting their own poultry line.",
                cta_label="Enquire Now",
                whatsapp_message="I want to enquire about Parent Stock / Chicks",
                sort_order=3,
            ),
        ]
        db.session.add_all(starter_products)

    if AdminUser.query.count() == 0:
        default_admin = AdminUser(username="admin")
        default_admin.set_password("changeme123")
        db.session.add(default_admin)

    db.session.commit()


def get_settings():
    return {s.key: s.value for s in Setting.query.all()}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------------------
# Public site
# ---------------------------------------------------------------------------

def register_public_routes(app):

    @app.context_processor
    def inject_settings():
        return {"settings": get_settings()}

    @app.route("/")
    def index():
        return render_template("index.html", active_page="home")

    @app.route("/about")
    def about():
        return render_template("about.html", active_page="about")

    @app.route("/products")
    def products():
        items = (
            Product.query.filter_by(is_active=True)
            .order_by(Product.sort_order, Product.id)
            .all()
        )
        return render_template("products.html", products=items, active_page="products")

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            message = request.form.get("message", "").strip()

            if not name or not message:
                flash("Please fill in your name and a short message.", "error")
                return redirect(url_for("contact"))

            db.session.add(ContactMessage(
                name=name, phone=phone, email=email, message=message
            ))
            db.session.commit()
            flash("Thanks! We've received your message and will get back to you soon.", "success")
            return redirect(url_for("contact"))

        return render_template("contact.html", active_page="contact")


# ---------------------------------------------------------------------------
# Admin panel
# ---------------------------------------------------------------------------

def register_admin_routes(app):

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = AdminUser.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session["admin_id"] = user.id
                flash("Welcome back!", "success")
                return redirect(request.args.get("next") or url_for("admin_dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin_id", None)
        flash("Logged out.", "success")
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @login_required
    def admin_dashboard():
        return render_template(
            "admin/dashboard.html",
            active="dashboard",
            product_count=Product.query.count(),
            message_count=ContactMessage.query.count(),
            unread_count=ContactMessage.query.filter_by(is_read=False).count(),
        )

    # --- Products -----------------------------------------------------

    @app.route("/admin/products")
    @login_required
    def admin_products():
        items = Product.query.order_by(Product.sort_order, Product.id).all()
        return render_template("admin/products.html", products=items, active="products")

    @app.route("/admin/products/new", methods=["GET", "POST"])
    @login_required
    def admin_product_new():
        if request.method == "POST":
            p = Product(
                name=request.form.get("name", "").strip(),
                tag=request.form.get("tag", "").strip(),
                tag_color=request.form.get("tag_color", "red"),
                art_bg=request.form.get("art_bg", "#FBE3E1"),
                description=request.form.get("description", "").strip(),
                cta_label=request.form.get("cta_label", "Order Now").strip(),
                whatsapp_message=request.form.get("whatsapp_message", "").strip(),
                sort_order=int(request.form.get("sort_order") or 0),
                is_active=bool(request.form.get("is_active")),
            )
            db.session.add(p)
            db.session.commit()
            flash(f'"{p.name}" was added.', "success")
            return redirect(url_for("admin_products"))
        return render_template("admin/product_form.html", product=None, active="products")

    @app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
    @login_required
    def admin_product_edit(product_id):
        p = Product.query.get_or_404(product_id)
        if request.method == "POST":
            p.name = request.form.get("name", "").strip()
            p.tag = request.form.get("tag", "").strip()
            p.tag_color = request.form.get("tag_color", "red")
            p.art_bg = request.form.get("art_bg", "#FBE3E1")
            p.description = request.form.get("description", "").strip()
            p.cta_label = request.form.get("cta_label", "Order Now").strip()
            p.whatsapp_message = request.form.get("whatsapp_message", "").strip()
            p.sort_order = int(request.form.get("sort_order") or 0)
            p.is_active = bool(request.form.get("is_active"))
            db.session.commit()
            flash(f'"{p.name}" was updated.', "success")
            return redirect(url_for("admin_products"))
        return render_template("admin/product_form.html", product=p, active="products")

    @app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
    @login_required
    def admin_product_delete(product_id):
        p = Product.query.get_or_404(product_id)
        db.session.delete(p)
        db.session.commit()
        flash(f'"{p.name}" was deleted.', "success")
        return redirect(url_for("admin_products"))

    # --- Contact messages ----------------------------------------------

    @app.route("/admin/messages")
    @login_required
    def admin_messages():
        items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template("admin/messages.html", messages=items, active="messages")

    @app.route("/admin/messages/<int:message_id>/toggle-read", methods=["POST"])
    @login_required
    def admin_message_toggle_read(message_id):
        m = ContactMessage.query.get_or_404(message_id)
        m.is_read = not m.is_read
        db.session.commit()
        return redirect(url_for("admin_messages"))

    @app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
    @login_required
    def admin_message_delete(message_id):
        m = ContactMessage.query.get_or_404(message_id)
        db.session.delete(m)
        db.session.commit()
        flash("Message deleted.", "success")
        return redirect(url_for("admin_messages"))

    # --- Site settings ---------------------------------------------------

    @app.route("/admin/settings", methods=["GET", "POST"])
    @login_required
    def admin_settings():
        if request.method == "POST":
            for key in DEFAULT_SETTINGS.keys():
                if key in request.form:
                    setting = Setting.query.get(key)
                    if setting is None:
                        setting = Setting(key=key)
                        db.session.add(setting)
                    setting.value = request.form.get(key, "").strip()
            db.session.commit()
            flash("Site settings updated.", "success")
            return redirect(url_for("admin_settings"))
        return render_template("admin/settings.html", settings=get_settings(), active="settings")

    # --- Admin account (change password) ---------------------------------

    @app.route("/admin/account", methods=["GET", "POST"])
    @login_required
    def admin_account():
        user = AdminUser.query.get(session["admin_id"])
        if request.method == "POST":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not user.check_password(current):
                flash("Current password is incorrect.", "error")
            elif len(new) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new != confirm:
                flash("New passwords do not match.", "error")
            else:
                user.set_password(new)
                db.session.commit()
                flash("Password updated.", "success")
                return redirect(url_for("admin_dashboard"))
        return render_template("admin/account.html", user=user, active="account")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
