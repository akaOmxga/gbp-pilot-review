from app.security.encryption import decrypt, encrypt


def test_encrypt_decrypt_roundtrip() -> None:
    plaintext = "ya29.fake-google-access-token"
    cipher = encrypt(plaintext)
    assert isinstance(cipher, bytes)
    assert plaintext.encode() not in cipher
    assert decrypt(cipher) == plaintext
