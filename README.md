# Dwit Farm — Flask Version

This turns the original static site (`index.html`, `about.html`, `products.html`,
`contact.html`) into a dynamic Flask app backed by SQLite, with an admin panel
so the client can update the site themselves — no code editing required.

## What's dynamic now

- **Products** — added, edited, reordered, hidden, or deleted from the admin
  panel. The Products page always reflects what's in the database.
- **Contact form** — visitors can submit a message; it's saved to the database
  and shows up under **Messages** in the admin panel (phone/email are still
  shown as direct links too).
- **Site settings** — business name, tagline, phone/WhatsApp number, email,
  address, social links, and the homepage/About page text are all editable
  from **Site Settings**, with no code changes.
- **Admin account** — a login-protected admin area, with the ability to
  change the password.

## Project layout

```
dwit_farm_flask/
├── app.py              # Flask app + all routes
├── models.py            # SQLAlchemy models + default seed data
├── requirements.txt
├── instance/
│   └── dwit_farm.db     # SQLite database (auto-created on first run)
├── static/
│   ├── css/styles.css   # original site styling (unchanged, plus admin skin)
│   ├── js/script.js     # original mobile-nav toggle script (unchanged)
│   └── assets/logo.jpg
└── templates/
    ├── base.html, index.html, about.html, products.html, contact.html
    └── admin/           # login, dashboard, products, messages, settings, account
```

## Running it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Visit **http://127.0.0.1:5000/** for the public site.

## Admin panel

Visit **http://127.0.0.1:5000/admin/login**

Default login (created automatically the first time the app runs):

- **Username:** `admin`
- **Password:** `changeme123`

**Important:** log in and change this password immediately under
**Account** in the admin panel — don't leave the default password in place
on a real deployment.

## Notes for deployment

- Set a real `SECRET_KEY` environment variable in production (used to sign
  the login session cookie):
  ```bash
  export SECRET_KEY="some-long-random-string"
  ```
- The SQLite file lives in `instance/dwit_farm.db`. Back this file up
  periodically — it holds all products, messages, and site settings.
- For production, run behind a real WSGI server (e.g. `gunicorn app:app`)
  rather than `python app.py`.
- If you ever want to wipe the database and start fresh with the original
  seed content, just delete `instance/dwit_farm.db` and restart the app —
  it will be recreated automatically with the default products/settings.

## Resetting a forgotten admin password

If the admin password is ever lost, run this once from the project folder:

```bash
python -c "
from app import app
from models import db, AdminUser
with app.app_context():
    user = AdminUser.query.filter_by(username='admin').first()
    user.set_password('a-new-password')
    db.session.commit()
"
```
