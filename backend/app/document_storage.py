import hashlib
import os
import re
import stat
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, status

from app.config import get_settings

OFFICE_WORD = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
OFFICE_SHEET = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": OFFICE_WORD,
    ".xlsx": OFFICE_SHEET,
}


def validate_upload(
    file_name: str | None, declared_type: str | None, content: bytes
) -> tuple[str, str]:
    maximum = get_settings().document_max_upload_bytes
    if maximum <= 0:
        raise RuntimeError("DOCUMENT_MAX_UPLOAD_BYTES muss größer als 0 sein.")
    if not content:
        raise HTTPException(status_code=422, detail="Die Datei ist leer.")
    if len(content) > maximum:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Die Datei überschreitet das Limit von {maximum} Bytes.",
        )

    raw_name = (file_name or "").replace("\\", "/").rsplit("/", 1)[-1]
    safe_name = "".join(
        character for character in raw_name if character.isprintable() and character not in "\r\n"
    ).strip()
    if not safe_name or len(safe_name) > 255:
        raise HTTPException(status_code=422, detail="Der Dateiname ist ungültig.")

    extension = Path(safe_name).suffix.lower()
    expected_type = ALLOWED_TYPES.get(extension)
    if expected_type is None:
        raise HTTPException(status_code=415, detail="Dieses Dateiformat ist nicht zugelassen.")
    if (declared_type or "").split(";", 1)[0].strip().lower() != expected_type:
        raise HTTPException(
            status_code=415, detail="Dateiendung und MIME-Typ stimmen nicht überein."
        )

    if expected_type == "application/pdf":
        valid_signature = content.startswith(b"%PDF-")
    elif expected_type == "image/png":
        valid_signature = content.startswith(b"\x89PNG\r\n\x1a\n")
    elif expected_type == "image/jpeg":
        valid_signature = content.startswith(b"\xff\xd8\xff")
    else:
        valid_signature = _is_ooxml_document(content, expected_type)
    if not valid_signature:
        raise HTTPException(status_code=415, detail="Die Dateisignatur ist ungültig.")

    return safe_name, expected_type


def _is_ooxml_document(content: bytes, media_type: str) -> bool:
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            names = set(archive.namelist())
            if "[Content_Types].xml" not in names:
                return False
            required = "word/document.xml" if media_type == OFFICE_WORD else "xl/workbook.xml"
            return required in names and not any(
                name.startswith(("word/vbaProject", "xl/vbaProject")) for name in names
            )
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return False


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _storage_root() -> Path:
    root = get_settings().document_storage_path.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    return root


def _storage_path(storage_key: str) -> Path:
    if re.fullmatch(r"[a-f0-9]{32}", storage_key) is None:
        raise ValueError("Ungültige Storage-ID")
    root = _storage_root()
    path = (root / storage_key).resolve()
    if path.parent != root:
        raise ValueError("Storage-Pfad liegt außerhalb des privaten Dokumentenspeichers")
    return path


def store_file(storage_key: str, content: bytes) -> None:
    path = _storage_path(storage_key)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
    except OSError:
        path.unlink(missing_ok=True)
        raise


def remove_file(storage_key: str) -> None:
    _storage_path(storage_key).unlink(missing_ok=True)


def read_file(storage_key: str) -> bytes:
    path = _storage_path(storage_key)
    file_stat = path.lstat()
    if not stat.S_ISREG(file_stat.st_mode):
        raise OSError("Der private Dokumentenspeicher enthält keine reguläre Datei.")
    return path.read_bytes()
