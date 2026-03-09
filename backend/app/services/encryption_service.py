from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.AES_ENCRYPTION_KEY
        if not key:
            raise RuntimeError(
                "AES_ENCRYPTION_KEY is not configured. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_data(plaintext: str) -> str:
    """Encrypt a plaintext string and return the ciphertext as a UTF-8 string."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_data(ciphertext: str) -> str:
    """Decrypt a ciphertext string and return the original plaintext."""
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        raise ValueError("Decryption failed — invalid token or wrong key")
