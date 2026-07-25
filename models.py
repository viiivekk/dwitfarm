from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class AdminUser(db.Model):
    """The single (or few) admin account(s) that can log in and edit the site."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    """A product/offering shown on the Products page."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    tag = db.Column(db.String(60), default="")            # small badge, e.g. "Desi & Gavran"
    tag_color = db.Column(db.String(20), default="red")    # red | yellow | blue (matches CSS classes)
    art_bg = db.Column(db.String(20), default="#FBE3E1")   # background color behind the icon
    description = db.Column(db.Text, default="")
    cta_label = db.Column(db.String(60), default="Order Now")
    whatsapp_message = db.Column(db.String(255), default="")
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def whatsapp_link(self, phone):
        from urllib.parse import quote
        text = quote(self.whatsapp_message or f"I want to order {self.name}")
        return f"https://wa.me/{phone}?text={text}"


class ContactMessage(db.Model):
    """An inquiry submitted through the public contact form."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), default="")
    email = db.Column(db.String(120), default="")
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class Setting(db.Model):
    """Simple key/value store for editable site text (hero copy, contact info, socials...)."""
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, default="")


DEFAULT_SETTINGS = {
    "site_name": "Dwit Farm",
    "tagline": "Manor · Palghar",
    "phone_e164": "919226466497",          # digits only, used for wa.me / tel: links
    "phone_display": "+91 92264 66497",
    "email": "patilumesh38.up6@gmail.com",
    "address": "Manor, Taluka Wada, Palghar, Maharashtra",
    "youtube_url": "https://www.youtube.com/@dwit-farm_38.",
    "facebook_url": "https://www.facebook.com/dwitfarm/",
    "instagram_url": "https://www.instagram.com/dwitfarm/",

    "hero_eyebrow": "Desi & Gavran Poultry · Manor, Palghar",
    "hero_title": 'Farm-fresh chicken &amp; eggs, raised the <span class="accent-red">old-fashioned</span> way.',
    "hero_lede": (
        "No shortcuts, no chemicals — just open pastures, natural grain, and birds that "
        'grow at their own pace. The same farming our <span class="accent-blue">YouTube</span> '
        "family has watched us practice every day."
    ),

    "about_intro_title": "We are naturals — and we farm like it.",
    "about_intro_text": (
        "Based in the quiet outskirts of Manor, Palghar, Dwit Farm is dedicated to reviving "
        "the purest form of poultry farming, one batch of birds at a time."
    ),
    "about_body_title": "Slowing down, on purpose.",
    "about_body_text": (
        "In a world moving toward artificial growth and shortcuts, Dwit Farm chooses to slow "
        "down and let nature lead. We specialise in raising authentic Desi and Gavran poultry "
        "using traditional, organic methods — the same methods we document and teach every "
        "week on our YouTube channel, for anyone who wants to start farming the honest way."
    ),

    "footer_tagline": (
        "Natural Desi &amp; Gavran poultry farming in Manor, Palghar — raised in the open, "
        "shared on YouTube."
    ),
}
