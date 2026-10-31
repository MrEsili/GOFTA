from app import db
from app.models import Conversation, Membership, Message, utcnow


def is_member(conversation_id, user_id):
    return db.session.query(Membership.id).filter_by(
        conversation_id=conversation_id, user_id=user_id
    ).first() is not None


def membership(conversation_id, user_id):
    return Membership.query.filter_by(conversation_id=conversation_id, user_id=user_id).first()


def can_post(conversation, user_id):
    member = membership(conversation.id, user_id) if conversation else None
    return bool(member and (conversation.kind != "channel" or member.role in {"owner", "admin"}))


def create_message(conversation, sender, text="", media_path=None, media_type=None, media_name=None):
    if not conversation:
        raise LookupError("گفت‌وگو پیدا نشد.")
    if not can_post(conversation, sender.id):
        raise PermissionError("اجازهٔ ارسال پیام در این گفتگو را ندارید.")
    text = (text or "").strip()
    if len(text) > 4000:
        raise ValueError("متن پیام بیش از حد طولانی است.")
    if not text and not media_path:
        raise ValueError("متن یا فایل پیام را وارد کنید.")
    message = Message(
        conversation=conversation, sender=sender, body=text,
        media_path=media_path, media_type=media_type, media_name=media_name,
    )
    db.session.add(message)
    db.session.commit()
    return message


def serialize_message(message, viewer_id=None):
    return {
        "id": message.id, "conversation_id": message.conversation_id,
        "body": message.body, "media_type": message.media_type,
        "media_url": f"/api/media/{message.id}" if message.media_path else None,
        "media_name": message.media_name,
        "created_at": message.created_at.isoformat(),
        "time": message.created_at.astimezone().strftime("%H:%M"),
        "mine": message.sender_id == viewer_id if viewer_id is not None else False,
        "sender": message.sender.public_data(viewer_id=viewer_id),
    }


def private_conversation(user, other):
    candidates = Conversation.query.filter_by(kind="direct").join(Membership).filter(
        Membership.user_id == user.id
    ).all()
    for conversation in candidates:
        if {m.user_id for m in conversation.memberships} == {user.id, other.id}:
            return conversation
    conversation = Conversation(kind="direct", title="", created_by_id=user.id)
    db.session.add(conversation)
    db.session.flush()
    db.session.add_all([
        Membership(user_id=user.id, conversation_id=conversation.id, role="owner"),
        Membership(user_id=other.id, conversation_id=conversation.id, role="member"),
    ])
    db.session.commit()
    return conversation


def create_conversation(owner, title, kind, members=()):
    if kind not in {"group", "channel"}:
        raise ValueError("نوع گفتگو معتبر نیست.")
    title = (title or "").strip()
    if not 2 <= len(title) <= 80:
        raise ValueError("نام گفتگو باید بین ۲ تا ۸۰ نویسه باشد.")
    conversation = Conversation(title=title, kind=kind, created_by_id=owner.id)
    db.session.add(conversation)
    db.session.flush()
    ids = {owner.id}
    for member in members:
        if member and member.id != owner.id:
            ids.add(member.id)
    for user_id in ids:
        db.session.add(Membership(
            user_id=user_id, conversation_id=conversation.id,
            role="owner" if user_id == owner.id else "member",
        ))
    db.session.commit()
    return conversation


def serialize_conversation(conversation, user_id):
    member = membership(conversation.id, user_id)
    if conversation.kind == "direct":
        other = next((m.user for m in conversation.memberships if m.user_id != user_id), None)
        title = other.display_name if other else "گفتگوی خصوصی"
        avatar = f"/avatar/{other.id}" if other and other.avatar_path else None
    else:
        title = conversation.title
        avatar = f"/api/conversations/{conversation.id}/avatar" if conversation.image_path else None
    latest = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.desc()).first()
    unread = 0
    if member:
        unread = Message.query.filter(
            Message.conversation_id == conversation.id,
            Message.sender_id != user_id,
            Message.created_at > member.last_read_at,
        ).count()
    return {
        "id": conversation.id, "kind": conversation.kind, "title": title, "avatar": avatar,
        "preview": latest.body if latest and latest.body else (
            "عکس" if latest and latest.media_type == "image" else "ویدئو" if latest else ""
        ),
        "latest_at": latest.created_at.isoformat() if latest else conversation.created_at.isoformat(),
        "unread": unread, "can_post": can_post(conversation, user_id),
        "role": member.role if member else "member",
    }


def update_read_marker(conversation_id, user_id):
    member = membership(conversation_id, user_id)
    if member:
        member.last_read_at = utcnow()
        db.session.commit()


def conversation_messages(conversation, user_id):
    return [
        serialize_message(message, user_id)
        for message in Message.query.filter_by(conversation_id=conversation.id)
        .order_by(Message.created_at.asc()).limit(500).all()
    ]
