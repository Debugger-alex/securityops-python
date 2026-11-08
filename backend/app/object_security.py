import base64
import json
import secrets
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status

from app.config import get_settings


class ObjectDataEncryptionError(Exception):
    pass


def _encryption_key() -> bytes:
    secret = get_settings().object_data_encryption_key
    if secret is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Der Schlüssel für sensible Objektdaten ist nicht konfiguriert.",
        )
    try:
        key = base64.b64decode(secret.get_secret_value(), altchars=b"-_", validate=True)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Der Schlüssel für sensible Objektdaten ist ungültig konfiguriert.",
        ) from exc
    if len(key) != 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Der Schlüssel für sensible Objektdaten muss 32 Byte lang sein.",
        )
    return key


def encrypt_object_data(object_id: UUID, payload: dict[str, str | None]) -> str:
    nonce = secrets.token_bytes(12)
    plaintext = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    ciphertext = AESGCM(_encryption_key()).encrypt(nonce, plaintext, object_id.bytes)
    return "v1:" + base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_object_data(object_id: UUID, stored_value: str) -> dict[str, str | None]:
    if not stored_value.startswith("v1:"):
        raise ObjectDataEncryptionError("Unbekannte Version verschlüsselter Objektdaten.")
    try:
        encrypted = base64.b64decode(
            stored_value[3:].encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
        if len(encrypted) < 12 + 16:
            raise ValueError("Verschlüsselte Daten sind unvollständig.")
        nonce, ciphertext = encrypted[:12], encrypted[12:]
        plaintext = AESGCM(_encryption_key()).decrypt(nonce, ciphertext, object_id.bytes)
        payload = json.loads(plaintext)
    except InvalidTag as exc:
        raise ObjectDataEncryptionError(
            "Verschlüsselte Objektdaten können mit dem konfigurierten Schlüssel nicht geprüft werden."
        ) from exc
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise ObjectDataEncryptionError("Verschlüsselte Objektdaten sind ungültig.") from exc
    if not isinstance(payload, dict) or any(
        not isinstance(value, str) and value is not None for value in payload.values()
    ):
        raise ObjectDataEncryptionError("Verschlüsselte Objektdaten haben ein ungültiges Format.")
    return payload
