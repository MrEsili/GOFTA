import re

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from app import db
from app.models import PhoneVerification, User, utcnow
from app.services.phone_auth import (
    issue_phone_code, normalize_phone, phone_exists, verify_phone_code,
)

auth_bp = Blueprint("auth", __name__)
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        if request.form.get("action") == "verify_phone_login":
            challenge = db.session.get(PhoneVerification, request.form.get("challenge_id", type=int))
            if not challenge or challenge.purpose != "login":
                flash("درخواست تأیید پیدا نشد؛ دوباره وارد شوید.", "error")
                return render_template("auth.html", mode="login")
            valid, error = verify_phone_code(challenge, request.form.get("code", ""))
            if not valid:
                flash(error, "error")
                return render_template(
                    "auth.html", mode="login", otp_challenge=True,
                    phone=challenge.phone, challenge_id=challenge.id,
                    test_code=None,
                )
            user = db.session.get(User, challenge.user_id)
            if not user or not user.phone_verified or user.phone != challenge.phone:
                db.session.delete(challenge)
                db.session.commit()
                flash("حساب شمارهٔ تلفن معتبر نیست.", "error")
                return render_template("auth.html", mode="login")
            db.session.delete(challenge)
            db.session.commit()
            login_user(user, remember=False)
            user.last_seen_at = utcnow()
            db.session.commit()
            return redirect(url_for("index"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        phone = normalize_phone(username)
        if phone:
            user = User.query.filter_by(phone=phone, phone_verified=True).first()
            if not user or not user.check_password(password):
                flash("نام کاربری/شماره یا گذرواژه درست نیست.", "error")
                return render_template("auth.html", mode="login")
            try:
                challenge, code = issue_phone_code(user, phone, "login")
            except (ValueError, RuntimeError) as exc:
                flash(str(exc), "error")
                return render_template("auth.html", mode="login")
            return render_template(
                "auth.html", mode="login", otp_challenge=True, phone=phone,
                challenge_id=challenge.id,
                test_code=code if current_app.config.get("SMS_TEST_MODE") else None,
            )
        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if user and user.check_password(password):
            login_user(user, remember=False)
            user.last_seen_at = utcnow()
            db.session.commit()
            return redirect(url_for("index"))
        flash("نام کاربری یا گذرواژه درست نیست.", "error")
    return render_template("auth.html", mode="login")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        phone_input = request.form.get("phone", "").strip()
        phone = normalize_phone(phone_input) if phone_input else None
        if not USERNAME_RE.fullmatch(username):
            flash("نام کاربری باید ۳ تا ۳۰ حرف لاتین، عدد یا زیرخط باشد.", "error")
        elif not 2 <= len(display_name) <= 60:
            flash("نام نمایشی باید بین ۲ تا ۶۰ نویسه باشد.", "error")
        elif len(password) < 8:
            flash("گذرواژه باید دست‌کم ۸ نویسه باشد.", "error")
        elif User.query.filter(func.lower(User.username) == username).first():
            flash("این نام کاربری قبلاً استفاده شده است.", "error")
        elif phone_input and not phone:
            flash("شماره تلفن معتبر نیست؛ با پیش‌شماره کشور مانند ‎+989123456789 وارد کنید.", "error")
        elif phone and phone_exists(phone):
            flash("این شمارهٔ تلفن قبلاً تأیید و ثبت شده است.", "error")
        else:
            user = User(username=username, display_name=display_name, pending_phone=phone)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("index"))
    return render_template("auth.html", mode="register")


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.last_seen_at = utcnow()
        db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))
