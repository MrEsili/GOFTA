from flask import Blueprint, abort, current_app, jsonify, request, send_file
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from app import ONLINE_USERS, db, socketio
from app.models import Contact, Conversation, Membership, Message, SavedMessage, User
from app.services.chat import (
    conversation_messages, create_conversation, create_message, is_member,
    membership, private_conversation, serialize_conversation, serialize_message,
    update_read_marker,
)
from app.services.media import safe_path, store_upload

chat_bp = Blueprint("chat", __name__)


def error_response(exc, status=400):
    return jsonify(error=str(exc)), status


def required_conversation(conversation_id):
    conversation = db.session.get(Conversation, conversation_id)
    if not conversation or not is_member(conversation.id, current_user.id):
        abort(404)
    return conversation


@chat_bp.get("/conversations")
@login_required
def conversations():
    memberships = Membership.query.filter_by(user_id=current_user.id).all()
    result = []
    for relation in memberships:
        result.append(serialize_conversation(relation.conversation, current_user.id))
    result.sort(key=lambda item: item["latest_at"], reverse=True)
    return jsonify(conversations=result)


@chat_bp.post("/conversations")
@login_required
def create_chat():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response("ساختار درخواست معتبر نیست.")
    action = data.get("action")
    if action == "direct":
        username = str(data.get("username", "")).strip().lower()
        other = User.query.filter(func.lower(User.username) == username).first()
        if not other:
            return error_response("کاربری با این نام پیدا نشد.", 404)
        if other.id == current_user.id:
            return error_response("برای یادداشت شخصی از پیام‌های ذخیره‌شده استفاده کنید.")
        conversation = private_conversation(current_user, other)
        socketio.emit("conversation_added", {"conversation_id": conversation.id}, to=f"user:{other.id}")
    else:
        kind = data.get("kind")
        requested_members = data.get("members", [])
        if not isinstance(requested_members, list) or len(requested_members) > 100:
            return error_response("فهرست اعضا معتبر نیست.")
        try:
            users = []
            for username in requested_members:
                if not isinstance(username, str) or len(username) > 30:
                    return error_response("نام کاربری عضو معتبر نیست.")
                user = User.query.filter(func.lower(User.username) == str(username).strip().lower()).first()
                if not user:
                    return error_response(f"کاربر «{username}» پیدا نشد.", 404)
                users.append(user)
            conversation = create_conversation(current_user, data.get("title", ""), kind, users)
            for user in users:
                socketio.emit(
                    "conversation_added",
                    {"conversation_id": conversation.id},
                    to=f"user:{user.id}",
                )
        except ValueError as exc:
            return error_response(exc)
    return jsonify(conversation=serialize_conversation(conversation, current_user.id)), 201


@chat_bp.get("/conversations/<int:conversation_id>")
@login_required
def get_conversation(conversation_id):
    conversation = required_conversation(conversation_id)
    return jsonify(
        conversation=serialize_conversation(conversation, current_user.id),
        messages=conversation_messages(conversation, current_user.id),
        members=[{**m.user.public_data(viewer_id=current_user.id), "role": m.role} for m in conversation.memberships],
    )


@chat_bp.get("/conversations/<int:conversation_id>/messages")
@login_required
def get_new_messages(conversation_id):
    conversation = required_conversation(conversation_id)
    try:
        after = max(0, int(request.args.get("after", "0")))
    except ValueError:
        return error_response("شناسهٔ پیام نامعتبر است.")
    messages = Message.query.filter(
        Message.conversation_id == conversation.id, Message.id > after
    ).order_by(Message.id.asc()).limit(100).all()
    if messages:
        update_read_marker(conversation.id, current_user.id)
    return jsonify(messages=[serialize_message(message, current_user.id) for message in messages])


@chat_bp.post("/conversations/<int:conversation_id>/read")
@login_required
def mark_read(conversation_id):
    required_conversation(conversation_id)
    update_read_marker(conversation_id, current_user.id)
    return jsonify(ok=True)


@chat_bp.post("/conversations/<int:conversation_id>/messages")
@login_required
def post_message(conversation_id):
    conversation = required_conversation(conversation_id)
    text = request.form.get("text", "").strip()
    upload = request.files.get("file")
    media_path = media_type = media_name = None
    if upload and upload.filename:
        try:
            media_path, media_type, media_name = store_upload(
                upload, "image" if upload.mimetype.startswith("image/") else "video",
                current_app.config["UPLOAD_ROOT"], current_app.config["MAX_CONTENT_LENGTH"],
            )
        except ValueError as exc:
            return error_response(exc)
    try:
        message = create_message(conversation, current_user, text, media_path, media_type, media_name)
    except (ValueError, PermissionError, LookupError) as exc:
        if media_path:
            path = safe_path(current_app.config["UPLOAD_ROOT"], media_path)
            if path:
                path.unlink(missing_ok=True)
        return error_response(exc, 403 if isinstance(exc, PermissionError) else 400)
    payload = serialize_message(message, current_user.id)
    socketio.emit("new_message", payload, to=f"conversation:{conversation.id}")
    return jsonify(message=payload), 201


@chat_bp.get("/media/<int:message_id>")
@login_required
def media(message_id):
    message = db.session.get(Message, message_id)
    if not message or not message.media_path or not is_member(message.conversation_id, current_user.id):
        abort(404)
    path = safe_path(current_app.config["UPLOAD_ROOT"], message.media_path)
    if not path:
        abort(404)
    return send_file(
        path, as_attachment=request.args.get("download") == "1",
        download_name=message.media_name or path.name, conditional=True, max_age=3600,
    )


@chat_bp.get("/files")
@login_required
def files():
    messages = (
        Message.query.join(Membership, Membership.conversation_id == Message.conversation_id)
        .filter(Membership.user_id == current_user.id, Message.media_path.isnot(None))
        .order_by(Message.created_at.desc())
        .all()
    )
    items = []
    total_bytes = 0
    for message in messages:
        path = safe_path(current_app.config["UPLOAD_ROOT"], message.media_path)
        if not path:
            continue
        size = path.stat().st_size
        total_bytes += size
        items.append({
            "id": message.id,
            "conversation_id": message.conversation_id,
            "name": message.media_name,
            "type": message.media_type,
            "url": f"/api/media/{message.id}",
            "conversation": message.conversation.title,
            "created_at": message.created_at.isoformat(),
            "size": size,
            "can_delete": message.sender_id == current_user.id,
        })
    return jsonify(files=items, total_bytes=total_bytes)


@chat_bp.delete("/files/<int:message_id>")
@login_required
def delete_own_file(message_id):
    message = (
        Message.query.join(Membership, Membership.conversation_id == Message.conversation_id)
        .filter(
            Membership.user_id == current_user.id,
            Message.id == message_id,
            Message.sender_id == current_user.id,
            Message.media_path.isnot(None),
        )
        .first()
    )
    if not message:
        abort(404)
    path = safe_path(current_app.config["UPLOAD_ROOT"], message.media_path)
    if not path:
        abort(404)
    path.unlink()
    conversation_id = message.conversation_id
    if not message.body:
        SavedMessage.query.filter_by(message_id=message.id).delete()
        db.session.delete(message)
    else:
        message.media_path = None
        message.media_type = None
        message.media_name = None
    db.session.commit()
    socketio.emit(
        "media_removed",
        {"conversation_id": conversation_id, "message_id": message_id},
        to=f"conversation:{conversation_id}",
    )
    return jsonify(ok=True)


@chat_bp.get("/conversations/<int:conversation_id>/members")
@login_required
def get_members(conversation_id):
    conversation = required_conversation(conversation_id)
    return jsonify(members=[
        {**m.user.public_data(viewer_id=current_user.id), "role": m.role} for m in conversation.memberships
    ])


@chat_bp.post("/conversations/<int:conversation_id>/members")
@login_required
def add_member(conversation_id):
    conversation = required_conversation(conversation_id)
    actor = membership(conversation.id, current_user.id)
    if conversation.kind not in {"group", "channel"} or not actor or actor.role not in {"owner", "admin"}:
        return error_response("فقط مدیر گفتگو می‌تواند عضو اضافه کند.", 403)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response("ساختار درخواست معتبر نیست.")
    user = User.query.filter(func.lower(User.username) == str(data.get("username", "")).strip().lower()).first()
    if not user:
        return error_response("کاربر پیدا نشد.", 404)
    if is_member(conversation.id, user.id):
        return error_response("این کاربر از قبل عضو است.")
    db.session.add(Membership(user_id=user.id, conversation_id=conversation.id, role="member"))
    db.session.commit()
    socketio.emit(
        "conversation_added",
        {"conversation_id": conversation.id},
        to=f"user:{user.id}",
    )
    return jsonify(ok=True), 201


@chat_bp.delete("/conversations/<int:conversation_id>/members/<int:user_id>")
@login_required
def remove_member(conversation_id, user_id):
    conversation = required_conversation(conversation_id)
    actor = membership(conversation.id, current_user.id)
    target = membership(conversation.id, user_id)
    if (
        conversation.kind not in {"group", "channel"}
        or not actor or actor.role not in {"owner", "admin"}
        or not target or target.role == "owner"
        or (actor.role == "admin" and target.role != "member")
    ):
        return error_response("اجازهٔ حذف این عضو را ندارید.", 403)
    db.session.delete(target)
    db.session.commit()
    socketio.emit(
        "conversation_removed",
        {"conversation_id": conversation.id},
        to=f"user:{user_id}",
    )
    return jsonify(ok=True)


@chat_bp.patch("/conversations/<int:conversation_id>/members/<int:user_id>")
@login_required
def update_member_role(conversation_id, user_id):
    conversation = required_conversation(conversation_id)
    actor, target = membership(conversation.id, current_user.id), membership(conversation.id, user_id)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response("ساختار درخواست معتبر نیست.")
    role = data.get("role")
    if (
        conversation.kind not in {"group", "channel"}
        or not actor or actor.role != "owner"
        or not target or role not in {"admin", "member"}
        or target.role == "owner"
    ):
        return error_response("تغییر نقش فقط در اختیار سازندهٔ گفتگو است.", 403)
    target.role = role
    db.session.commit()
    return jsonify(ok=True)


@chat_bp.post("/conversations/<int:conversation_id>/avatar")
@login_required
def update_conversation_avatar(conversation_id):
    conversation = required_conversation(conversation_id)
    actor = membership(conversation.id, current_user.id)
    if conversation.kind not in {"group", "channel"} or not actor or actor.role not in {"owner", "admin"}:
        return error_response("فقط مدیر می‌تواند تصویر گفتگو را تغییر دهد.", 403)
    upload = request.files.get("avatar")
    try:
        new_path, _, _ = store_upload(
            upload, "conversation", current_app.config["UPLOAD_ROOT"],
            current_app.config["MAX_CONTENT_LENGTH"],
        )
    except ValueError as exc:
        return error_response(exc)
    old_path = conversation.image_path
    conversation.image_path = new_path
    db.session.commit()
    if old_path:
        path = safe_path(current_app.config["UPLOAD_ROOT"], old_path)
        if path:
            path.unlink(missing_ok=True)
    return jsonify(avatar=f"/api/conversations/{conversation.id}/avatar")


@chat_bp.get("/conversations/<int:conversation_id>/avatar")
@login_required
def conversation_avatar(conversation_id):
    conversation = required_conversation(conversation_id)
    if not conversation.image_path:
        abort(404)
    path = safe_path(current_app.config["UPLOAD_ROOT"], conversation.image_path)
    if not path:
        abort(404)
    return send_file(path, conditional=True, max_age=3600)


@chat_bp.get("/users")
@login_required
def search_users():
    term = request.args.get("q", "").strip()
    if len(term) < 2:
        return jsonify(users=[])
    users = User.query.filter(
        User.id != current_user.id,
        or_(User.username.ilike(f"%{term}%"), User.display_name.ilike(f"%{term}%")),
    ).limit(20).all()
    results = []
    for user in users:
        data = user.public_data(viewer_id=current_user.id)
        data.update(
            online=bool(ONLINE_USERS.get(user.id)),
            last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
        )
        results.append(data)
    return jsonify(users=results)


@chat_bp.get("/contacts")
@login_required
def list_contacts():
    relations = Contact.query.filter_by(user_id=current_user.id).all()
    contacts = []
    for relation in relations:
        user = relation.contact_user
        data = user.public_data(viewer_id=current_user.id)
        data.update(
            online=bool(ONLINE_USERS.get(user.id)),
            last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
        )
        contacts.append(data)
    contacts.sort(key=lambda item: (not item["online"], item["display_name"].casefold()))
    return jsonify(contacts=contacts)


@chat_bp.post("/contacts")
@login_required
def add_contact():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return error_response("ساختار درخواست معتبر نیست.")
    username = str(data.get("username", "")).strip().lower()
    user = User.query.filter(func.lower(User.username) == username).first()
    if not user or user.id == current_user.id:
        return error_response("کاربر معتبری پیدا نشد.", 404)
    if Contact.query.filter_by(user_id=current_user.id, contact_user_id=user.id).first():
        return error_response("این مخاطب از قبل اضافه شده است.", 409)
    relation = Contact(user_id=current_user.id, contact_user_id=user.id)
    db.session.add(relation)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response("این مخاطب از قبل اضافه شده است.", 409)
    return jsonify(contact=user.public_data(viewer_id=current_user.id)), 201


@chat_bp.delete("/contacts/<int:user_id>")
@login_required
def remove_contact(user_id):
    relation = Contact.query.filter_by(user_id=current_user.id, contact_user_id=user_id).first()
    if not relation:
        abort(404)
    db.session.delete(relation)
    db.session.commit()
    return jsonify(ok=True)


@chat_bp.post("/messages/<int:message_id>/save")
@login_required
def save_message(message_id):
    message = db.session.get(Message, message_id)
    if not message or not is_member(message.conversation_id, current_user.id):
        abort(404)
    saved = SavedMessage.query.filter_by(user_id=current_user.id, message_id=message.id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return jsonify(saved=False)
    db.session.add(SavedMessage(user_id=current_user.id, message_id=message.id))
    db.session.commit()
    return jsonify(saved=True)


@chat_bp.get("/saved")
@login_required
def saved_messages():
    rows = SavedMessage.query.filter_by(user_id=current_user.id).order_by(SavedMessage.saved_at.desc()).all()
    return jsonify(messages=[serialize_message(row.message, current_user.id) for row in rows])
