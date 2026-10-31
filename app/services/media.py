import secrets
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}
IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _extension(filename):
    safe = secure_filename(filename or "")
    return safe.rsplit(".", 1)[-1].lower() if "." in safe else ""


def store_upload(file_storage, category, root, max_bytes):
    if not file_storage or not file_storage.filename:
        raise ValueError("فایلی انتخاب نشده است.")
    extension = _extension(file_storage.filename)
    allowed = IMAGE_EXTENSIONS if category in {"profile", "conversation", "image"} else VIDEO_EXTENSIONS
    if extension not in allowed:
        raise ValueError("پسوند این فایل پشتیبانی نمی‌شود.")
    content = file_storage.stream.read(max_bytes + 1)
    if not content:
        raise ValueError("فایل خالی است.")
    if len(content) > max_bytes:
        raise ValueError("حجم فایل از حد مجاز بیشتر است.")
    media_type = "image" if category in {"profile", "conversation", "image"} else "video"
    if media_type == "image":
        try:
            from io import BytesIO
            with Image.open(BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                    raise ValueError("نوع واقعی تصویر پشتیبانی نمی‌شود.")
                if image.width * image.height > 40_000_000:
                    raise ValueError("ابعاد تصویر بیش از حد بزرگ است.")
                image.verify()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ValueError("فایل تصویر معتبر نیست.") from exc
    elif not _valid_video_signature(extension, content):
        raise ValueError("ساختار فایل ویدئویی معتبر نیست.")
    folder = Path(root) / ("profiles" if category == "profile" else "conversations" if category == "conversation" else "media")
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{secrets.token_hex(20)}.{extension}"
    (folder / name).write_bytes(content)
    return f"{folder.name}/{name}", media_type, secure_filename(file_storage.filename)[:180]


def _valid_video_signature(extension, content):
    if extension == "webm":
        return content.startswith(bytes.fromhex("1A45DFA3"))
    if extension in {"mp4", "mov", "m4v"}:
        return (
            len(content) >= 12
            and content[4:8] == b"ftyp"
            and content[8:12] in {b"isom", b"iso2", b"iso5", b"mp41", b"mp42", b"avc1", b"M4V ", b"qt  "}
        )
    return False


def safe_path(root, relative):
    path = (Path(root) / relative).resolve()
    base = Path(root).resolve()
    if not path.is_relative_to(base) or not path.is_file():
        return None
    return path
