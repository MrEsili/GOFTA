from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(16), unique=True, index=True)
    pending_phone = db.Column(db.String(16))
    phone_verified = db.Column(db.Boolean, nullable=False, default=False)
    phone_visibility = db.Column(db.String(12), nullable=False, default="private")
    display_name = db.Column(db.String(60), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(240), nullable=False, default="")
    avatar_path = db.Column(db.String(255))
    last_seen_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    language = db.Column(db.String(2), nullable=False, default="fa")
    theme = db.Column(db.String(5), nullable=False, default="light")
    font_family = db.Column(db.String(20), nullable=False, default="vazirmatn")
    color_theme = db.Column(db.String(20), nullable=False, default="blue")
    notifications_enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def public_data(self, viewer_id=None):
        show_phone = bool(self.phone and self.phone_verified and (
            self.phone_visibility == "public" or viewer_id == self.id
        ))
        if not show_phone and self.phone and self.phone_verified and self.phone_visibility == "members" and viewer_id is not None:
            shared_conversation = db.session.query(Membership.id).filter(
                Membership.user_id == self.id,
                Membership.conversation_id.in_(
                    db.session.query(Membership.conversation_id).filter_by(user_id=viewer_id)
                ),
            ).first()
            show_phone = shared_conversation is not None
        return {
            "id": self.id, "username": self.username, "display_name": self.display_name,
            "avatar": f"/avatar/{self.id}" if self.avatar_path else None, "bio": self.bio,
            "phone": self.phone if show_phone else None,
        }


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False, default="")
    kind = db.Column(db.String(12), nullable=False, index=True)
    image_path = db.Column(db.String(255))
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    memberships = db.relationship("Membership", back_populates="conversation", cascade="all, delete-orphan")
    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Membership(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "conversation_id", name="uq_membership_user_conversation"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    role = db.Column(db.String(12), nullable=False, default="member")
    last_read_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User")
    conversation = db.relationship("Conversation", back_populates="memberships")


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False, default="")
    media_path = db.Column(db.String(255))
    media_type = db.Column(db.String(12))
    media_name = db.Column(db.String(180))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")


class SavedMessage(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "message_id", name="uq_saved_user_message"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False)
    saved_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    message = db.relationship("Message")


class PhoneVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    phone = db.Column(db.String(16), nullable=False)
    purpose = db.Column(db.String(12), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)


class Contact(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "contact_user_id", name="uq_contact_pair"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    contact_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User", foreign_keys=[user_id])
    contact_user = db.relationship("User", foreign_keys=[contact_user_id])
