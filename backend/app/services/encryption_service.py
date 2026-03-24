import base64
import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# AES-256-GCM constants
AES_KEY_SIZE = 32   # bytes
GCM_NONCE_SIZE = 12  # bytes (96-bit nonce, standard for GCM)

# RSA constants
RSA_KEY_SIZE = 2048
RSA_PUBLIC_EXPONENT = 65537

# Argon2id parameters
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32


def generate_aes_key() -> bytes:
    """Generate a random 256-bit AES key."""
    return os.urandom(AES_KEY_SIZE)


def encrypt_content(plaintext: str, key: bytes) -> tuple[str, str, str]:
    """Encrypt plaintext with AES-256-GCM.

    Returns (ciphertext_b64, iv_b64, tag_b64) — all base64 encoded.
    The AESGCM primitive appends the 16-byte auth tag to the ciphertext,
    so we split it off for separate storage.
    """
    iv = os.urandom(GCM_NONCE_SIZE)
    aesgcm = AESGCM(key)
    # AESGCM.encrypt() returns ciphertext + 16-byte tag concatenated
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return (
        base64.b64encode(ciphertext).decode("utf-8"),
        base64.b64encode(iv).decode("utf-8"),
        base64.b64encode(tag).decode("utf-8"),
    )


def decrypt_content(ciphertext_b64: str, key: bytes, iv_b64: str, tag_b64: str) -> str:
    """Decrypt AES-256-GCM ciphertext back to plaintext string."""
    ciphertext = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    tag = base64.b64decode(tag_b64)
    aesgcm = AESGCM(key)
    plaintext_bytes = aesgcm.decrypt(iv, ciphertext + tag, None)
    return plaintext_bytes.decode("utf-8")


def generate_rsa_keypair() -> tuple[str, str]:
    """Generate an RSA-2048 keypair.

    Returns (public_key_pem, private_key_pem) as PEM strings.
    The public key is stored server-side (in beneficiaries table).
    The private key is given to the beneficiary and never stored on the server.
    """
    private_key = rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT,
        key_size=RSA_KEY_SIZE,
    )
    public_key = private_key.public_key()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    return public_pem, private_pem


def encrypt_key_for_beneficiary(aes_key: bytes, public_key_pem: str) -> str:
    """Encrypt an AES key with a beneficiary's RSA public key (OAEP+SHA-256).

    Returns base64-encoded ciphertext stored in secret_assignments.encrypted_key.
    """
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    encrypted = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_key_as_beneficiary(encrypted_key_b64: str, private_key_pem: str) -> bytes:
    """Decrypt an AES key using a beneficiary's RSA private key (OAEP+SHA-256).

    Returns the raw AES key bytes.
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )
    encrypted = base64.b64decode(encrypted_key_b64)
    return private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using Argon2id.

    Parameters follow OWASP recommendations:
      time_cost=3, memory_cost=64MB, parallelism=4
    Used for user-side key derivation (not for server-side bcrypt auth).
    """
    return hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
