import io
import re
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app import create_app, db, socketio
from app.models import Conversation, Membership, Message, PhoneVerification, User


class GoftaAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "UPLOAD_ROOT": root / "uploads",
            "MAX_CONTENT_LENGTH": 2 * 1024 * 1024,
            "SMS_TEST_MODE": True,
        })
        self.client = self.app.test_client()
        self.register(self.client, "alice", "Alice")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_dir.cleanup()

    @staticmethod
    def csrf(client):
        with client.session_transaction() as session:
            return session["_csrf_token"]

    def register(self, client, username, display_name):
        client.get("/register")
        return client.post("/register", data={
            "csrf_token": self.csrf(client), "username": username,
            "display_name": display_name, "password": "secure-pass-123",
        }, follow_redirects=True)

    def create_user(self, username, display_name):
        with self.app.app_context():
            user = User(username=username, display_name=display_name)
            user.set_password("secure-pass-123")
            db.session.add(user)
            db.session.commit()
        return user

    def login_as(self, client, username):
        client.get("/login")
        return client.post("/login", data={
            "csrf_token": self.csrf(client), "username": username, "password": "secure-pass-123",
        })

    def post_json(self, client, path, payload, method="POST"):
        return client.open(path, method=method, json=payload, headers={"X-CSRF-Token": self.csrf(client)})

    def make_png(self, color=(20, 120, 200)):
        stream = io.BytesIO()
        Image.new("RGB", (4, 4), color).save(stream, format="PNG")
        stream.seek(0)
        return stream

    def test_registration_login_and_persistent_hashed_password(self):
        with self.app.app_context():
            alice = User.query.filter_by(username="alice").one()
            self.assertNotEqual(alice.password_hash, "secure-pass-123")
            self.assertTrue(alice.check_password("secure-pass-123"))
        self.client.post("/logout", headers={"X-CSRF-Token": self.csrf(self.client)})
        response = self.client.post("/login", data={
            "csrf_token": self.csrf(self.client), "username": "alice", "password": "secure-pass-123",
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"conversation-view", response.data)

    def test_persian_font_and_color_palette_settings_persist(self):
        response = self.post_json(self.client, "/api/settings", {
            "language": "fa", "theme": "dark",
            "font_family": "vazirmatn", "color_theme": "violet",
        })
        self.assertEqual(response.status_code, 200)
        settings = self.client.get("/api/me").json
        self.assertEqual(settings["font_family"], "vazirmatn")
        self.assertEqual(settings["color_theme"], "violet")
        self.assertEqual(settings["theme"], "dark")

        invalid = self.post_json(self.client, "/api/settings", {
            "language": "fa", "theme": "light",
            "font_family": "unknown", "color_theme": "violet",
        })
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(self.client.get("/api/me").json["font_family"], "vazirmatn")

    def test_contacts_search_and_start_private_conversation(self):
        self.create_user("bob", "Bob Example")
        results = self.client.get("/api/users?q=BOB")
        self.assertEqual(results.status_code, 200)
        self.assertEqual([user["username"] for user in results.json["users"]], ["bob"])
        by_display_name = self.client.get("/api/users?q=Example")
        self.assertEqual([user["username"] for user in by_display_name.json["users"]], ["bob"])
        self.assertEqual(self.client.get("/api/users?q=b").json["users"], [])
        self.assertEqual(self.client.get("/api/users?q=alice").json["users"], [])
        direct = self.post_json(self.client, "/api/conversations", {
            "action": "direct", "username": results.json["users"][0]["username"],
        })
        self.assertEqual(direct.status_code, 201)
        self.assertEqual(direct.json["conversation"]["kind"], "direct")

    def test_contacts_can_be_added_listed_and_removed(self):
        self.create_user("bob", "Bob")
        added = self.post_json(self.client, "/api/contacts", {"username": "bob"})
        self.assertEqual(added.status_code, 201, added.json)
        self.assertEqual(added.json["contact"]["username"], "bob")
        contacts = self.client.get("/api/contacts")
        self.assertEqual(contacts.status_code, 200)
        self.assertEqual(len(contacts.json["contacts"]), 1)
        bob = contacts.json["contacts"][0]
        self.assertEqual(bob["display_name"], "Bob")
        self.assertIn("online", bob)
        duplicate = self.post_json(self.client, "/api/contacts", {"username": "bob"})
        self.assertEqual(duplicate.status_code, 409)
        removed = self.client.open(
            f"/api/contacts/{bob['id']}", method="DELETE",
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(self.client.get("/api/contacts").json["contacts"], [])

    def test_group_and_channel_members_can_be_removed_by_authorized_managers(self):
        self.create_user("bob", "Bob")
        self.create_user("carol", "Carol")
        group = self.post_json(self.client, "/api/conversations", {
            "kind": "group", "title": "Friends", "members": ["bob", "carol"],
        })
        group_id = group.json["conversation"]["id"]
        with self.app.app_context():
            bob_id = User.query.filter_by(username="bob").one().id
            carol_id = User.query.filter_by(username="carol").one().id
        bob_client = self.app.test_client()
        self.login_as(bob_client, "bob")
        forbidden = bob_client.open(
            f"/api/conversations/{group_id}/members/{carol_id}",
            method="DELETE", headers={"X-CSRF-Token": self.csrf(bob_client)},
        )
        self.assertEqual(forbidden.status_code, 403)
        removed = self.client.open(
            f"/api/conversations/{group_id}/members/{bob_id}",
            method="DELETE", headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(bob_client.get(f"/api/conversations/{group_id}").status_code, 404)
        self.assertEqual(len(self.client.get(f"/api/conversations/{group_id}/members").json["members"]), 2)

        channel = self.post_json(self.client, "/api/conversations", {
            "kind": "channel", "title": "News", "members": ["bob"],
        })
        channel_id = channel.json["conversation"]["id"]
        channel_removed = self.client.open(
            f"/api/conversations/{channel_id}/members/{bob_id}",
            method="DELETE", headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(channel_removed.status_code, 200)
        self.assertEqual(bob_client.get(f"/api/conversations/{channel_id}").status_code, 404)

        direct = self.post_json(self.client, "/api/conversations", {
            "action": "direct", "username": "carol",
        })
        direct_id = direct.json["conversation"]["id"]
        direct_target_id = carol_id
        invalid_direct_removal = self.client.open(
            f"/api/conversations/{direct_id}/members/{direct_target_id}",
            method="DELETE", headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(invalid_direct_removal.status_code, 403)

    def test_notification_preference_is_persisted_and_validated(self):
        self.assertTrue(self.client.get("/api/me").json["notifications_enabled"])
        settings = self.post_json(self.client, "/api/settings", {
            "language": "fa", "theme": "light", "font_family": "vazirmatn",
            "color_theme": "blue", "notifications_enabled": False,
        })
        self.assertEqual(settings.status_code, 200)
        self.assertFalse(self.client.get("/api/me").json["notifications_enabled"])
        invalid = self.post_json(self.client, "/api/settings", {
            "language": "fa", "theme": "light", "font_family": "vazirmatn",
            "color_theme": "blue", "notifications_enabled": "false",
        })
        self.assertEqual(invalid.status_code, 400)

    def test_phone_verification_phone_login_and_visibility_levels(self):
        phone_client = self.app.test_client()
        phone_client.get("/register")
        registration = phone_client.post("/register", data={
            "csrf_token": self.csrf(phone_client), "username": "alicephone",
            "display_name": "Alice Phone", "password": "secure-pass-123",
            "phone": "+989123456789",
        })
        self.assertEqual(registration.status_code, 302)
        me = phone_client.get("/api/me").json
        self.assertEqual(me["phone_input"], "+989123456789")
        self.assertFalse(me["phone_verified"])

        sent = self.post_json(phone_client, "/api/phone/send", {"phone": "09123456789"})
        self.assertEqual(sent.status_code, 200, sent.json)
        code = sent.json["test_code"]
        self.assertRegex(code, r"^\d{6}$")
        verified = self.post_json(phone_client, "/api/phone/verify", {"code": code})
        self.assertEqual(verified.status_code, 200, verified.json)
        self.assertEqual(phone_client.get("/api/me").json["phone"], "+989123456789")

        changed = self.post_json(phone_client, "/api/phone/send", {"phone": "+989133456789"})
        self.assertEqual(changed.status_code, 200, changed.json)
        pending = phone_client.get("/api/me").json
        self.assertEqual(pending["phone_input"], "+989133456789")
        self.assertEqual(pending["phone"], "+989123456789")
        self.assertFalse(pending["phone_verified"])
        change_verified = self.post_json(
            phone_client, "/api/phone/verify", {"code": changed.json["test_code"]},
        )
        self.assertEqual(change_verified.status_code, 200, change_verified.json)
        self.assertEqual(phone_client.get("/api/me").json["phone"], "+989133456789")

        phone_client.post("/logout", headers={"X-CSRF-Token": self.csrf(phone_client)})
        challenge_response = phone_client.post("/login", data={
            "csrf_token": self.csrf(phone_client), "username": "+989133456789",
            "password": "secure-pass-123",
        })
        self.assertEqual(challenge_response.status_code, 200)
        self.assertIn(b"verify_phone_login", challenge_response.data)
        self.assertIn("کد آزمایشی:".encode(), challenge_response.data)
        login_code = re.search(rb"<strong>(\d{6})</strong>", challenge_response.data)
        self.assertIsNotNone(login_code)
        with self.app.app_context():
            challenge = PhoneVerification.query.filter_by(purpose="login").one()
            challenge_id = challenge.id
        login = phone_client.post("/login", data={
            "csrf_token": self.csrf(phone_client), "action": "verify_phone_login",
            "challenge_id": challenge_id, "code": login_code.group(1).decode(),
        })
        self.assertEqual(login.status_code, 302)
        self.assertEqual(phone_client.get("/api/me").json["username"], "alicephone")

    def test_phone_visibility_is_private_members_or_public(self):
        self.create_user("bob", "Bob")
        with self.app.app_context():
            bob_id = User.query.filter_by(username="bob").one().id
        self.create_user("carol", "Carol")
        with self.app.app_context():
            bob = db.session.get(User, bob_id)
            bob.phone = "+989111111111"
            bob.phone_verified = True
            bob.phone_visibility = "members"
            db.session.commit()
        direct = self.post_json(self.client, "/api/conversations", {
            "action": "direct", "username": "bob",
        })
        self.assertEqual(direct.status_code, 201)
        self.assertEqual(self.client.get("/api/users?q=bob").json["users"][0]["phone"], "+989111111111")

        carol_client = self.app.test_client()
        self.login_as(carol_client, "carol")
        self.assertIsNone(carol_client.get("/api/users?q=bob").json["users"][0]["phone"])
        with self.app.app_context():
            bob = db.session.get(User, bob_id)
            bob.phone_visibility = "public"
            db.session.commit()
        self.assertEqual(carol_client.get("/api/users?q=bob").json["users"][0]["phone"], "+989111111111")
        with self.app.app_context():
            bob = db.session.get(User, bob_id)
            bob.phone_visibility = "private"
            db.session.commit()
        self.assertIsNone(self.client.get("/api/users?q=bob").json["users"][0]["phone"])

    def test_direct_group_channel_and_message_flow(self):
        self.create_user("bob", "Bob")
        direct = self.post_json(self.client, "/api/conversations", {"action": "direct", "username": "bob"})
        self.assertEqual(direct.status_code, 201)
        direct_id = direct.json["conversation"]["id"]
        response = self.client.post(
            f"/api/conversations/{direct_id}/messages",
            data={"text": "سلام"},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["message"]["body"], "سلام")
        group = self.post_json(self.client, "/api/conversations", {
            "kind": "group", "title": "دوستان", "members": ["bob"],
        })
        channel = self.post_json(self.client, "/api/conversations", {
            "kind": "channel", "title": "خبرها", "members": ["bob"],
        })
        self.assertEqual(group.status_code, 201)
        self.assertEqual(channel.status_code, 201)
        with self.app.app_context():
            self.assertEqual(Conversation.query.count(), 3)
            self.assertEqual(Membership.query.filter_by(conversation_id=group.json["conversation"]["id"]).count(), 2)

    def test_channel_write_permissions_and_member_media_access(self):
        self.create_user("bob", "Bob")
        channel = self.post_json(self.client, "/api/conversations", {"kind": "channel", "title": "خبرها"})
        channel_id = channel.json["conversation"]["id"]
        outsider = self.app.test_client()
        self.create_user("eve", "Eve")
        self.login_as(outsider, "eve")
        denied = outsider.post(
            f"/api/conversations/{channel_id}/messages", data={"text": "نه"},
            headers={"X-CSRF-Token": self.csrf(outsider)},
        )
        self.assertEqual(denied.status_code, 404)
        post = self.client.post(
            f"/api/conversations/{channel_id}/messages", data={"text": "خبر"},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(post.status_code, 201)
        message_id = post.json["message"]["id"]
        self.assertEqual(outsider.get(f"/api/media/{message_id}").status_code, 404)

    def test_image_video_upload_and_profile_avatar_replacement(self):
        self.create_user("bob", "Bob")
        direct = self.post_json(self.client, "/api/conversations", {"action": "direct", "username": "bob"})
        chat_id = direct.json["conversation"]["id"]
        image_response = self.client.post(
            f"/api/conversations/{chat_id}/messages",
            data={"file": (self.make_png(), "picture.png")},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(image_response.status_code, 201, image_response.json)
        image_message = image_response.json["message"]
        media_response = self.client.get(image_message["media_url"])
        self.assertEqual(media_response.status_code, 200)
        self.assertEqual(media_response.mimetype, "image/png")
        media_response.close()
        download_response = self.client.get(image_message["media_url"] + "?download=1")
        self.assertEqual(download_response.status_code, 200)
        download_response.close()

        video_bytes = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2"
        video_response = self.client.post(
            f"/api/conversations/{chat_id}/messages",
            data={"file": (io.BytesIO(video_bytes), "clip.mp4")},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(video_response.status_code, 201, video_response.json)
        video_media = self.client.get(video_response.json["message"]["media_url"])
        self.assertEqual(video_media.status_code, 200)
        self.assertEqual(video_media.mimetype, "video/mp4")
        video_media.close()

        profile_response = self.client.post(
            "/api/profile", data={
                "display_name": "Alice Updated", "bio": "Hello",
                "avatar": (self.make_png((220, 40, 40)), "avatar.png"),
            }, headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(profile_response.status_code, 200, profile_response.json)
        with self.app.app_context():
            alice = User.query.filter_by(username="alice").one()
            old_avatar = alice.avatar_path
        avatar_response = self.client.get(profile_response.json["user"]["avatar"])
        self.assertEqual(avatar_response.status_code, 200)
        avatar_response.close()
        second = self.client.post(
            "/api/profile", data={
                "display_name": "Alice Updated", "bio": "Hello",
                "avatar": (self.make_png((20, 180, 40)), "new.png"),
            }, headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(second.status_code, 200)
        self.assertFalse((Path(self.app.config["UPLOAD_ROOT"]) / old_avatar).exists())
        self.assertEqual(self.client.post(
            "/api/profile", data={"display_name": "Alice Updated", "bio": "Hello", "remove_avatar": "true"},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        ).status_code, 200)
        with self.app.app_context():
            self.assertIsNone(db.session.get(User, alice.id).avatar_path)

    def test_file_manager_lists_downloads_and_deletes_only_own_files(self):
        self.create_user("bob", "Bob")
        direct = self.post_json(self.client, "/api/conversations", {"action": "direct", "username": "bob"})
        conversation_id = direct.json["conversation"]["id"]
        upload = self.client.post(
            f"/api/conversations/{conversation_id}/messages",
            data={"file": (self.make_png(), "managed.png")},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(upload.status_code, 201)
        message = upload.json["message"]
        manager = self.client.get("/api/files")
        self.assertEqual(manager.status_code, 200)
        self.assertEqual(len(manager.json["files"]), 1)
        file_info = manager.json["files"][0]
        self.assertEqual(file_info["id"], message["id"])
        self.assertTrue(file_info["can_delete"])
        self.assertEqual(file_info["conversation_id"], conversation_id)
        self.assertGreater(file_info["size"], 0)
        self.assertEqual(manager.json["total_bytes"], file_info["size"])
        download = self.client.get(file_info["url"] + "?download=1")
        self.assertEqual(download.status_code, 200)
        download.close()

        bob_client = self.app.test_client()
        self.login_as(bob_client, "bob")
        peer_files = bob_client.get("/api/files")
        self.assertEqual(len(peer_files.json["files"]), 1)
        self.assertFalse(peer_files.json["files"][0]["can_delete"])
        denied = bob_client.open(
            f"/api/files/{message['id']}", method="DELETE",
            headers={"X-CSRF-Token": self.csrf(bob_client)},
        )
        self.assertEqual(denied.status_code, 404)

        with self.app.app_context():
            relative_path = db.session.get(Message, message["id"]).media_path
        local_path = Path(self.app.config["UPLOAD_ROOT"]) / relative_path
        self.assertTrue(local_path.exists())
        deleted = self.client.open(
            f"/api/files/{message['id']}", method="DELETE",
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(local_path.exists())
        self.assertEqual(self.client.get("/api/files").json, {"files": [], "total_bytes": 0})
        self.assertEqual(self.client.get(message["media_url"]).status_code, 404)

    def test_realtime_socket_delivery_and_saved_message(self):
        self.create_user("bob", "Bob")
        self.create_user("carol", "Carol")
        carol_client = self.app.test_client()
        self.login_as(carol_client, "carol")
        direct = self.post_json(self.client, "/api/conversations", {"action": "direct", "username": "carol"})
        conversation_id = direct.json["conversation"]["id"]
        alice_socket = socketio.test_client(self.app, flask_test_client=self.client)
        carol_socket = socketio.test_client(self.app, flask_test_client=carol_client)
        alice_socket.emit("join_conversation", {"conversation_id": conversation_id})
        carol_socket.emit("join_conversation", {"conversation_id": conversation_id})
        response = self.client.post(
            f"/api/conversations/{conversation_id}/messages", data={"text": "زنده"},
            headers={"X-CSRF-Token": self.csrf(self.client)},
        )
        self.assertEqual(response.status_code, 201)
        events = carol_socket.get_received()
        self.assertTrue(any(event["name"] == "new_message" for event in events))
        message_id = response.json["message"]["id"]
        saved = self.post_json(self.client, f"/api/messages/{message_id}/save", {})
        self.assertTrue(saved.json["saved"])
        self.assertEqual(len(self.client.get("/api/saved").json["messages"]), 1)
        alice_socket.disconnect()
        carol_socket.disconnect()


if __name__ == "__main__":
    unittest.main()
