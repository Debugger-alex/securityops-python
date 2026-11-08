import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status

from app.config import get_settings

TOTP_PERIOD_SECONDS = 30
TOTP_DIGITS = 6
RECOVERY_CODE_COUNT = 10


def _fernet() -> Fernet:
    key = get_settings().mfa_encryption_key
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MFA ist nicht verfügbar: Der Verschlüsselungsschlüssel ist nicht konfiguriert.",
        )
    try:
        return Fernet(key.get_secret_value().encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MFA ist nicht verfügbar: Der Verschlüsselungsschlüssel ist ungültig.",
        ) from exc


def encrypt_secret(secret: str) -> str:
    return _fernet().encrypt(secret.encode("ascii")).decode("ascii")


def decrypt_secret(encrypted_secret: str) -> str:
    try:
        return _fernet().decrypt(encrypted_secret.encode("ascii")).decode("ascii")
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Das gespeicherte MFA-Geheimnis kann nicht entschlüsselt werden.",
        ) from exc


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def provisioning_uri(secret: str, username: str, issuer: str = "SecurityOps") -> str:
    label = quote(f"{issuer}:{username}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_PERIOD_SECONDS}"
    )


def totp_counter_at(now: float | None = None) -> int:
    return int((time.time() if now is None else now) // TOTP_PERIOD_SECONDS)


def totp_code(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10**TOTP_DIGITS)).zfill(TOTP_DIGITS)


def verify_totp(secret: str, code: str, *, last_counter: int | None = None) -> int | None:
    current_counter = totp_counter_at()
    matching = [
        counter
        for counter in range(max(0, current_counter - 1), current_counter + 2)
        if (last_counter is None or counter > last_counter)
        and hmac.compare_digest(totp_code(secret, counter), code)
    ]
    return max(matching, default=None)


def new_recovery_codes() -> list[str]:
    return [secrets.token_hex(16).upper() for _ in range(RECOVERY_CODE_COUNT)]


def recovery_code_hash(code: str) -> str:
    normalized = code.replace("-", "").strip().upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
