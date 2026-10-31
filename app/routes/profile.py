from flask import Blueprint, abort, current_app, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.models import PhoneVerification, User
from app.services.media import safe_path, store_upload
from app.services.phone_auth import (
    VISIBILITIES, issue_phone_code, normalize_phone, phone_exists, verify_phone_code,
)

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/avatar/<int:user_id>")
@login_required
def avatar(user_id):
    from flask import send_file
    user = db.session.get(User, user_id)
    if not user or not user.avatar_path:
        abort(404)
    path = safe_path(current_app.config["UPLOAD_ROOT"], user.avatar_path)
    if not path:
        abort(404)
    return send_file(path, conditional=True, max_age=3600)


@profile_bp.get("/api/me")
@login_required
def get_me():
    data = current_user.public_data(viewer_id=current_user.id)
    data.update(
        language=current_user.language, theme=current_user.theme,
        font_family=current_user.font_family, color_theme=current_user.color_theme,
        phone_input=current_user.pending_phone or current_user.phone or "",
        phone_verified=current_user.phone_verified and (
            not current_user.pending_phone or current_user.pending_phone == current_user.phone
        ),
        phone_visibility=current_user.phone_visibility,
        notifications_enabled=current_user.notifications_enabled,
    )
    from flask import session
    data["csrf_token"] = session.get("_csrf_token")
    return jsonify(data)


@profile_bp.post("/api/profile")
@login_required
def update_profile():
    display_name = request.form.get("display_name", "").strip()
    bio = request.form.get("bio", "").strip()
    visibility = request.form.get("phone_visibility", current_user.phone_visibility)
    if not 2 <= len(display_name) <= 60 or len(bio) > 240 or visibility not in VISIBILITIES:
        return jsonify(error="نام باید ۲ تا ۶۰ و توضیحات حداکثر ۲۴۰ نویسه باشد."), 400
    old_avatar = current_user.avatar_path
    upload = request.files.get("avatar")
    new_avatar = None
    if upload and upload.filename:
        try:
            new_avatar, _, _ = store_upload(
                upload, "profile", current_app.config["UPLOAD_ROOT"],
                current_app.config["MAX_CONTENT_LENGTH"],
            )
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
    current_user.display_name = display_name
    current_user.bio = bio
    current_user.phone_visibility = visibility
    if request.form.get("remove_phone") == "true":
        current_user.phone = None
        current_user.pending_phone = None
        current_user.phone_verified = False
    if new_avatar:
        current_user.avatar_path = new_avatar
    elif request.form.get("remove_avatar") == "true":
        current_user.avatar_path = None
    db.session.commit()
    if old_avatar and current_user.avatar_path != old_avatar:
        old_path = safe_path(current_app.config["UPLOAD_ROOT"], old_avatar)
        if old_path:
            old_path.unlink(missing_ok=True)
    return jsonify(user=current_user.public_data(viewer_id=current_user.id))


@profile_bp.post("/api/phone/send")
@login_required
def send_phone_code():
    data = request.get_json(silent=True) or {}
    phone = normalize_phone(data.get("phone"))
    if not phone:
        return jsonify(error="شماره تلفن معتبر نیست؛ پیش‌شماره کشور را هم وارد کنید."), 400
    if phone_exists(phone, current_user.id):
        return jsonify(error="این شمارهٔ تلفن قبلاً به حساب دیگری متصل شده است."), 409
    try:
        challenge, code = issue_phone_code(current_user, phone, "verify")
    except (ValueError, RuntimeError) as exc:
        return jsonify(error=str(exc)), 400
    current_user.pending_phone = phone
    db.session.commit()
    result = {"ok": True, "expires_in": current_app.config["PHONE_OTP_TTL_SECONDS"]}
    if current_app.config.get("SMS_TEST_MODE"):
        result["test_code"] = code
    return jsonify(result)


@profile_bp.post("/api/phone/verify")
@login_required
def verify_phone():
    data = request.get_json(silent=True) or {}
    challenge = PhoneVerification.query.filter_by(
        user_id=current_user.id, purpose="verify"
    ).order_by(PhoneVerification.created_at.desc()).first()
    if not challenge:
        return jsonify(error="کد تأیید فعالی پیدا نشد؛ ابتدا کد تازه بگیرید."), 400
    valid, error = verify_phone_code(challenge, data.get("code", ""))
    if not valid:
        return jsonify(error=error), 400
    if phone_exists(challenge.phone, current_user.id):
        db.session.delete(challenge)
        db.session.commit()
        return jsonify(error="این شمارهٔ تلفن قبلاً به حساب دیگری متصل شده است."), 409
    current_user.phone = challenge.phone
    current_user.pending_phone = None
    current_user.phone_verified = True
    db.session.delete(challenge)
    db.session.commit()
    return jsonify(user=current_user.public_data(viewer_id=current_user.id))


@profile_bp.delete("/api/phone")
@login_required
def remove_phone():
    current_user.phone = None
    current_user.pending_phone = None
    current_user.phone_verified = False
    current_user.phone_visibility = "private"
    PhoneVerification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify(ok=True)


@profile_bp.post("/api/settings")
@login_required
def save_settings():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify(error="ساختار درخواست معتبر نیست."), 400
    language, theme = data.get("language"), data.get("theme")
    font_family, color_theme = data.get("font_family"), data.get("color_theme")
    notifications_enabled = data.get("notifications_enabled", current_user.notifications_enabled)
    if (
        language not in {"fa", "en"}
        or theme not in {"light", "dark"}
        or font_family not in {"vazirmatn", "system"}
        or color_theme not in {"blue", "violet", "green", "rose", "amber", "teal"}
        or not isinstance(notifications_enabled, bool)
    ):
        return jsonify(error="تنظیمات نامعتبر است."), 400
    current_user.language, current_user.theme = language, theme
    current_user.font_family, current_user.color_theme = font_family, color_theme
    current_user.notifications_enabled = notifications_enabled
    db.session.commit()
    return jsonify(ok=True)
