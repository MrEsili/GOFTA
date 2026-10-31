import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("GOFTA_SECRET_KEY", "change-this-local-secret-before-network-use")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(BASE_DIR / 'instance' / 'gofta.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("GOFTA_MAX_UPLOAD_MB", "64")) * 1024 * 1024
    UPLOAD_ROOT = BASE_DIR / "uploads"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SMS_TEST_MODE = os.environ.get("GOFTA_SMS_TEST_MODE", "1").strip().lower() in {"1", "true", "yes"}
    PHONE_OTP_TTL_SECONDS = 300
    PHONE_OTP_RESEND_SECONDS = 60
