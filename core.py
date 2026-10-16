"""Shared application core: app factory, SQLite helpers, secure auth (register / login / profile),
CSRF protection, demo account seeding and UI context.

Every project calls `create_app(...)` with its own UI theme, DB schema and optional demo seeder.
"""
import functools
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    avatar_color TEXT DEFAULT '#7F5AF0',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);
"""
DEMO_EMAIL, DEMO_PASSWORD = "demo@example.com", "Demo@1234"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
AVATAR_COLORS = ["#7F5AF0", "#2CB67D", "#FF416C", "#00C9FF", "#F7B32B", "#E85D75", "#3A86FF", "#FB5607"]


# --------------------------------------------------------------------------- database
def get_db():
    if "db" not in g:
        from flask import current_app
        g.db = sqlite3.connect(current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def query(sql, args=(), one=False):
    rows = [dict(r) for r in get_db().execute(sql, args).fetchall()]
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------- auth helpers
def login_required(view):
    @functools.wraps(view)
    def wrapped(*a, **kw):
        if g.user is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Authentication required"), 401
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*a, **kw)
    return wrapped


def _secret(app):
    path = os.path.join(app.instance_path, "secret.key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    return open(path).read().strip()


def password_problems(pw):
    probs = []
    if len(pw) < 8:
        probs.append("at least 8 characters")
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        probs.append("letters and numbers")
    return probs


# --------------------------------------------------------------------------- factory
def create_app(import_name, ui: dict, schema: str = "", seed_demo=None, on_register=None):
    app = Flask(import_name, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or _secret(app),
        DATABASE=os.environ.get("DATABASE") or os.path.join(app.instance_path, "app.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        UI=ui,
    )

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        db = get_db()
        db.executescript(BASE_SCHEMA + schema)
        db.commit()
        if not query("SELECT id FROM users WHERE email=?", (DEMO_EMAIL,), one=True):
            uid = execute("INSERT INTO users(name,email,password,avatar_color) VALUES(?,?,?,?)",
                          ("Demo User", DEMO_EMAIL, generate_password_hash(DEMO_PASSWORD), ui.get("accent1", "#7F5AF0")))
            if seed_demo:
                seed_demo(uid)

    # ---------------------------------------------------------------- request hooks
    @app.before_request
    def load_user_and_csrf():
        uid = session.get("uid")
        g.user = query("SELECT * FROM users WHERE id=?", (uid,), one=True) if uid else None
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not token or not secrets.compare_digest(token, session["csrf"]):
                if request.path.startswith("/api/"):
                    return jsonify(error="Invalid CSRF token — refresh the page"), 400
                abort(400, "Invalid CSRF token — please refresh the page and try again.")

    @app.context_processor
    def inject():
        return dict(ui=app.config["UI"], user=g.get("user"), csrf_token=session.get("csrf", ""),
                    demo_email=DEMO_EMAIL, demo_password=DEMO_PASSWORD, year=datetime.now().year)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    # ---------------------------------------------------------------- auth routes
    @app.route("/")
    def index():
        return redirect(url_for(ui["home"]) if g.user else url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if g.user:
            return redirect(url_for(ui["home"]))
        if request.method == "POST":
            if session.get("lock_until", 0) > time.time():
                flash(f"Too many attempts. Try again in {int(session['lock_until'] - time.time())}s.", "danger")
                return render_template("auth.html", mode="login"), 429
            email = request.form.get("email", "").strip().lower()
            pw = request.form.get("password", "")
            u = query("SELECT * FROM users WHERE email=?", (email,), one=True)
            if u and check_password_hash(u["password"], pw):
                nxt = request.args.get("next") or ""
                session.clear()
                session["uid"] = u["id"]
                session["csrf"] = secrets.token_hex(16)
                session.permanent = bool(request.form.get("remember"))
                execute("UPDATE users SET last_login=? WHERE id=?", (now(), u["id"]))
                flash(f"Welcome back, {u['name'].split()[0]}! 👋", "success")
                return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for(ui["home"]))
            fails = session.get("fails", 0) + 1
            session["fails"] = fails
            if fails >= 5:
                session["lock_until"], session["fails"] = time.time() + 30, 0
            flash("Invalid email or password.", "danger")
        return render_template("auth.html", mode="login")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if g.user:
            return redirect(url_for(ui["home"]))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            pw, pw2 = request.form.get("password", ""), request.form.get("confirm", "")
            errors = []
            if len(name) < 2:
                errors.append("Please enter your full name.")
            if not EMAIL_RE.match(email):
                errors.append("Please enter a valid email address.")
            if probs := password_problems(pw):
                errors.append("Password needs " + " and ".join(probs) + ".")
            if pw != pw2:
                errors.append("Passwords do not match.")
            if not request.form.get("terms"):
                errors.append("Please accept the terms to continue.")
            if not errors and query("SELECT id FROM users WHERE email=?", (email,), one=True):
                errors.append("An account with this email already exists.")
            if errors:
                for e in errors:
                    flash(e, "danger")
                return render_template("auth.html", mode="register", form=request.form), 400
            uid = execute("INSERT INTO users(name,email,password,avatar_color,last_login) VALUES(?,?,?,?,?)",
                          (name, email, generate_password_hash(pw), secrets.choice(AVATAR_COLORS), now()))
            if on_register:
                on_register(uid)
            session.clear()
            session["uid"] = uid
            session["csrf"] = secrets.token_hex(16)
            flash(f"Account created — welcome to {ui['name']}, {name.split()[0]}! 🎉", "success")
            return redirect(url_for(ui["home"]))
        return render_template("auth.html", mode="register", form={})

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            action = request.form.get("action")
            if action == "profile":
                name = request.form.get("name", "").strip()
                color = request.form.get("avatar_color", g.user["avatar_color"])
                if len(name) >= 2:
                    execute("UPDATE users SET name=?, avatar_color=? WHERE id=?", (name, color, g.user["id"]))
                    flash("Profile updated.", "success")
            elif action == "password":
                if not check_password_hash(g.user["password"], request.form.get("current", "")):
                    flash("Current password is incorrect.", "danger")
                elif probs := password_problems(request.form.get("new", "")):
                    flash("New password needs " + " and ".join(probs) + ".", "danger")
                else:
                    execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash(request.form["new"]), g.user["id"]))
                    flash("Password changed successfully.", "success")
            elif action == "delete" and request.form.get("confirm_email", "").lower() == g.user["email"]:
                if g.user["email"] == DEMO_EMAIL:
                    flash("The shared demo account can't be deleted.", "warning")
                else:
                    execute("DELETE FROM users WHERE id=?", (g.user["id"],))
                    session.clear()
                    flash("Your account and data were deleted.", "info")
                    return redirect(url_for("register"))
            return redirect(url_for("profile"))
        return render_template("profile.html", colors=AVATAR_COLORS)

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="This page drifted into space."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, message=getattr(e, "description", "Bad request")), 400

    return app
