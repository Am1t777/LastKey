import pytest
from app.services.encryption_service import (
    encrypt_content,
    decrypt_content,
    generate_rsa_keypair,
    encrypt_key_for_beneficiary,
    decrypt_key_as_beneficiary,
    derive_key,
    generate_aes_key,
)


def test_aes_round_trip():
    key = generate_aes_key()
    content = "my secret content"
    ct, iv, tag = encrypt_content(content, key)
    decrypted = decrypt_content(ct, key, iv, tag)
    assert decrypted == content


def test_aes_wrong_key_raises():
    key = generate_aes_key()
    wrong_key = generate_aes_key()
    content = "my secret"
    ct, iv, tag = encrypt_content(content, key)
    with pytest.raises(Exception):
        decrypt_content(ct, wrong_key, iv, tag)


def test_rsa_key_generation():
    public_pem, private_pem = generate_rsa_keypair()
    assert "BEGIN PUBLIC KEY" in public_pem
    assert "BEGIN PRIVATE KEY" in private_pem


def test_rsa_round_trip():
    public_pem, private_pem = generate_rsa_keypair()
    aes_key = generate_aes_key()
    encrypted = encrypt_key_for_beneficiary(aes_key, public_pem)
    decrypted = decrypt_key_as_beneficiary(encrypted, private_pem)
    assert decrypted == aes_key


def test_argon2_deterministic():
    password = "testpass"
    salt = b"saltsaltsalt1234"
    key1 = derive_key(password, salt)
    key2 = derive_key(password, salt)
    assert key1 == key2
    assert len(key1) == 32


def test_unicode_content():
    key = generate_aes_key()
    content = "שלום עולם — secret"
    ct, iv, tag = encrypt_content(content, key)
    decrypted = decrypt_content(ct, key, iv, tag)
    assert decrypted == content


def test_encrypt_content_returns_three_strings():
    key = generate_aes_key()
    result = encrypt_content("hello", key)
    assert len(result) == 3
    ct, iv, tag = result
    assert isinstance(ct, str)
    assert isinstance(iv, str)
    assert isinstance(tag, str)
