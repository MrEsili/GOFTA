import secrets
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "برای ادامه وارد حساب شوید."
socketio = SocketIO(async_mode="threading")
ONLINE_USERS = {}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    root = Path(app.config["UPLOAD_ROOT"])
    for folder in ("profiles", "media", "conversations"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(profile_bp)

    @app.before_request
    def establish_csrf():
        if "_csrf_token" not in session:
            session["_csrf_token"] = secrets.token_urlsafe(32)
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            expected = session.get("_csrf_token")
            supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
            if not expected or not secrets.compare_digest(expected, supplied or ""):
                return jsonify(error="درخواست نامعتبر است؛ صفحه را تازه‌سازی کنید.") if request.path.startswith("/api/") else (
                    "درخواست نامعتبر است؛ صفحه را تازه‌سازی کنید.", 400
                )

    @app.get("/")
    def index():
        if not current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for("auth.login"))
        return render_template("chat.html")

    @app.errorhandler(413)
    def file_too_large(_):
        return jsonify(error="حجم فایل از حد مجاز بیشتر است."), 413

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return jsonify(error="مورد درخواستی پیدا نشد."), 404
        return "صفحه پیدا نشد.", 404

    with app.app_context():
        db.create_all()
        user_columns = {column["name"] for column in inspect(db.engine).get_columns("user")}
        for column_name, column_definition in (
            ("font_family", "VARCHAR(20) NOT NULL DEFAULT 'vazirmatn'"),
            ("color_theme", "VARCHAR(20) NOT NULL DEFAULT 'blue'"),
            ("notifications_enabled", "BOOLEAN NOT NULL DEFAULT 1"),
            ("phone", "VARCHAR(16)"),
            ("pending_phone", "VARCHAR(16)"),
            ("phone_verified", "BOOLEAN NOT NULL DEFAULT 0"),
            ("phone_visibility", "VARCHAR(12) NOT NULL DEFAULT 'private'"),
            ("last_seen_at", "DATETIME"),
        ):
            if column_name not in user_columns:
                db.session.execute(text(f"ALTER TABLE user ADD COLUMN {column_name} {column_definition}"))
        db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_user_phone ON user (phone)"))
        db.session.execute(text(
            "UPDATE user SET last_seen_at = CURRENT_TIMESTAMP WHERE last_seen_at IS NULL"
        ))
        db.session.commit()

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@socketio.on("connect")
def socket_user_connected():
    if current_user.is_authenticated:
        ONLINE_USERS.setdefault(current_user.id, set()).add(request.sid)
        join_room(f"user:{current_user.id}")


@socketio.on("disconnect")
def socket_user_disconnected():
    if not current_user.is_authenticated:
        return
    connections = ONLINE_USERS.get(current_user.id)
    if connections:
        connections.discard(request.sid)
        if not connections:
            ONLINE_USERS.pop(current_user.id, None)
            from app.models import User, utcnow
            user = db.session.get(User, current_user.id)
            if user:
                user.last_seen_at = utcnow()
                db.session.commit()


@socketio.on("join_conversation")
def socket_join_conversation(data):
    if not current_user.is_authenticated:
        return
    from app.services.chat import is_member
    try:
        conversation_id = int(data.get("conversation_id"))
    except (TypeError, ValueError, AttributeError):
        return
    if is_member(conversation_id, current_user.id):
        join_room(f"conversation:{conversation_id}")


@socketio.on("leave_conversation")
def socket_leave_conversation(data):
    if not current_user.is_authenticated:
        return
    try:
        conversation_id = int(data.get("conversation_id"))
    except (TypeError, ValueError, AttributeError):
        return
    from flask_socketio import leave_room
    leave_room(f"conversation:{conversation_id}")


@socketio.on("send_message")
def socket_send_message(data):
    if not current_user.is_authenticated:
        emit("message_error", {"error": "برای ارسال پیام وارد شوید."})
        return
    from app.services.chat import create_message, serialize_message
    from app.models import Conversation
    try:
        conversation_id = int(data.get("conversation_id"))
        text = str(data.get("text", "")).strip()
        conversation = db.session.get(Conversation, conversation_id)
        message = create_message(conversation, current_user, text)
    except (TypeError, ValueError, AttributeError, PermissionError, LookupError) as exc:
        emit("message_error", {"error": str(exc) or "ارسال پیام ممکن نشد."})
        return
    emit("new_message", serialize_message(message), to=f"conversation:{conversation_id}")
