import hashlib
import hmac
import re
import secrets
from datetime import timedelta, timezone

from flask import current_app

from app import db
from app.models import PhoneVerification, User, utcnow

PHONE_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
PHONE_CLEAN_RE = re.compile(r"[^\d+]")
OTP_RE = re.compile(r"^\d{6}$")
VISIBILITIES = {"private", "members", "public"}


def normalize_phone(value):
    phone = PHONE_CLEAN_RE.sub("", str(value or "").translate(PHONE_DIGITS))
    if phone.startswith("00"):
        phone = f"+{phone[2:]}"
    elif phone.startswith("09") and len(phone) == 11:
        phone = f"+98{phone[1:]}"
    elif not phone.startswith("+"):
        return None
    digits = phone[1:] if phone.startswith("+") else ""
    if not digits.isdigit() or not 8 <= len(digits) <= 15:
        return None
    return f"+{digits}"


def _code_hash(user_id, phone, purpose, code):
    secret = str(current_app.config["SECRET_KEY"]).encode()
    value = f"{user_id}:{phone}:{purpose}:{code}".encode()
    return hmac.new(secret, value, hashlib.sha256).hexdigest()


def issue_phone_code(user, phone, purpose):
    if not current_app.config.get("SMS_TEST_MODE"):
        raise RuntimeError("ارسال پیامک تنظیم نشده است؛ فقط حالت آزمایشی در دسترس است.")
    now = utcnow()
    recent = PhoneVerification.query.filter_by(user_id=user.id, purpose=purpose).order_by(
        PhoneVerification.created_at.desc()
    ).first()
    if recent:
        created_at = recent.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if (now - created_at).total_seconds() < current_app.config["PHONE_OTP_RESEND_SECONDS"]:
            raise ValueError("برای ارسال دوبارهٔ کد کمی صبر کنید.")
    PhoneVerification.query.filter_by(user_id=user.id, purpose=purpose).delete()
    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = PhoneVerification(
        user_id=user.id,
        phone=phone,
        purpose=purpose,
        code_hash=_code_hash(user.id, phone, purpose, code),
        expires_at=now + timedelta(seconds=current_app.config["PHONE_OTP_TTL_SECONDS"]),
    )
    db.session.add(challenge)
    db.session.commit()
    return challenge, code


def verify_phone_code(challenge, code):
    code = str(code or "").translate(PHONE_DIGITS)
    if not OTP_RE.fullmatch(code):
        return False, "کد تأیید باید ۶ رقم باشد."
    expires_at = challenge.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if utcnow() >= expires_at:
        db.session.delete(challenge)
        db.session.commit()
        return False, "کد تأیید منقضی شده است."
    if challenge.attempts >= 5:
        db.session.delete(challenge)
        db.session.commit()
        return False, "تعداد تلاش‌ها بیش از حد مجاز است؛ کد تازه بگیرید."
    challenge.attempts += 1
    expected = _code_hash(challenge.user_id, challenge.phone, challenge.purpose, str(code))
    if not hmac.compare_digest(challenge.code_hash, expected):
        if challenge.attempts >= 5:
            db.session.delete(challenge)
        db.session.commit()
        return False, "کد تأیید درست نیست."
    return True, ""


def phone_exists(phone, exclude_user_id=None):
    query = User.query.filter(User.phone == phone)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.first() is not None
