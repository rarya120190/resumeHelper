"""Tests for the Fernet-based encryption service."""

from __future__ import annotations

import pytest

from app.services.encryption_service import decrypt_data, encrypt_data


class TestEncryptDecrypt:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Hello, this is a secret message!"
        ciphertext = encrypt_data(plaintext)
        assert ciphertext != plaintext
        assert decrypt_data(ciphertext) == plaintext

    def test_different_plaintexts_different_ciphertexts(self):
        ct1 = encrypt_data("message one")
        ct2 = encrypt_data("message two")
        assert ct1 != ct2

    def test_same_plaintext_different_ciphertexts(self):
        """Fernet uses a timestamp + IV, so encrypting the same text twice
        produces different ciphertexts."""
        ct1 = encrypt_data("same text")
        ct2 = encrypt_data("same text")
        assert ct1 != ct2  # Fernet is non-deterministic
        assert decrypt_data(ct1) == decrypt_data(ct2) == "same text"

    def test_empty_string_encryption(self):
        ciphertext = encrypt_data("")
        assert decrypt_data(ciphertext) == ""

    def test_unicode_encryption(self):
        plaintext = "Résumé — Ông Nguyễn 你好 🚀"
        ciphertext = encrypt_data(plaintext)
        assert decrypt_data(ciphertext) == plaintext

    def test_long_text_encryption(self):
        plaintext = "A" * 10_000
        ciphertext = encrypt_data(plaintext)
        assert decrypt_data(ciphertext) == plaintext

    def test_invalid_ciphertext_raises(self):
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data("this-is-not-valid-ciphertext")

    def test_tampered_ciphertext_raises(self):
        ct = encrypt_data("original")
        # Flip a character in the middle of the ciphertext
        tampered = ct[:10] + ("A" if ct[10] != "A" else "B") + ct[11:]
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_data(tampered)
