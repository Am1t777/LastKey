# base64 is used to encode raw bytes into printable ASCII strings for database storage
import base64
# os.urandom generates cryptographically secure random bytes for keys and nonces
import os

# Argon2id low-level API — used for password-based key derivation (not for auth hashing)
from argon2.low_level import Type, hash_secret_raw
# hashes and serialization support RSA key operations
from cryptography.hazmat.primitives import hashes, serialization
# padding and rsa provide the RSA key generation and OAEP encryption/decryption
from cryptography.hazmat.primitives.asymmetric import padding, rsa
# AESGCM implements AES-256 in Galois/Counter Mode (authenticated encryption)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# AES-256 uses a 256-bit (32-byte) key
AES_KEY_SIZE = 32   # bytes
# GCM standard recommends a 96-bit (12-byte) nonce for best performance and security
GCM_NONCE_SIZE = 12  # bytes (96-bit nonce, standard for GCM)

# RSA key size — 2048 bits is the minimum recommended by NIST for new applications
RSA_KEY_SIZE = 2048
# 65537 is the standard public exponent (F4) — chosen for efficiency and security
RSA_PUBLIC_EXPONENT = 65537

# Argon2id tuning parameters following OWASP recommendations:
ARGON2_TIME_COST = 3        # Number of iterations (higher = slower = harder to brute-force)
ARGON2_MEMORY_COST = 65536  # Memory usage in KiB — 64 MB makes GPU attacks expensive
ARGON2_PARALLELISM = 4      # Number of parallel threads used during hashing
ARGON2_HASH_LEN = 32        # Output length in bytes — 256 bits, matching AES-256 key size


# generate_aes_key creates a fresh random 256-bit AES key for encrypting one secret
def generate_aes_key() -> bytes:
    """Generate a random 256-bit AES key."""
    # os.urandom uses the OS CSPRNG — safe for cryptographic use
    return os.urandom(AES_KEY_SIZE)


# encrypt_content encrypts a plaintext string with AES-256-GCM using the provided key
def encrypt_content(plaintext: str, key: bytes) -> tuple[str, str, str]:
    """Encrypt plaintext with AES-256-GCM.

    Returns (ciphertext_b64, iv_b64, tag_b64) — all base64 encoded.
    The AESGCM primitive appends the 16-byte auth tag to the ciphertext,
    so we split it off for separate storage.
    """
    # Generate a fresh random nonce for this encryption operation (never reuse a nonce with the same key)
    iv = os.urandom(GCM_NONCE_SIZE)
    # Create an AESGCM cipher instance bound to this 256-bit key
    aesgcm = AESGCM(key)
    # AESGCM.encrypt() returns ciphertext concatenated with the 16-byte GCM authentication tag
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    # Split off the last 16 bytes as the authentication tag, leaving only the ciphertext
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    # Base64-encode each component for safe storage as text in the database
    return (
        base64.b64encode(ciphertext).decode("utf-8"),  # ciphertext
        base64.b64encode(iv).decode("utf-8"),          # nonce / initialisation vector
        base64.b64encode(tag).decode("utf-8"),          # authentication tag
    )


# decrypt_content reverses encrypt_content — reassembles the ciphertext+tag and decrypts
def decrypt_content(ciphertext_b64: str, key: bytes, iv_b64: str, tag_b64: str) -> str:
    """Decrypt AES-256-GCM ciphertext back to plaintext string."""
    # Decode each base64-encoded component back to raw bytes
    ciphertext = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    tag = base64.b64decode(tag_b64)
    # Recreate the AESGCM cipher with the same key
    aesgcm = AESGCM(key)
    # AESGCM.decrypt() expects ciphertext+tag concatenated; it verifies the tag before decrypting
    # If the tag doesn't match (tampered data) it raises InvalidTag, which we let propagate
    plaintext_bytes = aesgcm.decrypt(iv, ciphertext + tag, None)
    # Decode the raw bytes back to a UTF-8 string
    return plaintext_bytes.decode("utf-8")


# generate_rsa_keypair creates a new 2048-bit RSA key pair for a beneficiary
def generate_rsa_keypair() -> tuple[str, str]:
    """Generate an RSA-2048 keypair.

    Returns (public_key_pem, private_key_pem) as PEM strings.
    The public key is stored server-side (in beneficiaries table).
    The private key is given to the beneficiary and never stored on the server.
    """
    # Generate the private key using the standard public exponent 65537
    private_key = rsa.generate_private_key(
        public_exponent=RSA_PUBLIC_EXPONENT,
        key_size=RSA_KEY_SIZE,
    )
    # Derive the public key from the private key
    public_key = private_key.public_key()

    # Serialize the public key as PEM-encoded SubjectPublicKeyInfo (standard format)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # Serialize the private key as unencrypted PKCS#8 PEM — shown to the user once, never stored
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        # No server-side passphrase — the beneficiary is responsible for protecting it
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    return public_pem, private_pem


# encrypt_key_for_beneficiary wraps an AES key with a beneficiary's RSA public key
def encrypt_key_for_beneficiary(aes_key: bytes, public_key_pem: str) -> str:
    """Encrypt an AES key with a beneficiary's RSA public key (OAEP+SHA-256).

    Returns base64-encoded ciphertext stored in secret_assignments.encrypted_key.
    """
    # Load the PEM public key into a cryptography library key object
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
    # Encrypt using OAEP padding with SHA-256 — the secure standard for RSA encryption
    encrypted = public_key.encrypt(
        aes_key,
        padding.OAEP(
            # MGF1 mask generation function using SHA-256
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            # Hash algorithm for the OAEP label
            algorithm=hashes.SHA256(),
            # No custom label — use the default empty label
            label=None,
        ),
    )
    # Return the ciphertext as a base64 string for storage in the database
    return base64.b64encode(encrypted).decode("utf-8")


# decrypt_key_as_beneficiary recovers the AES key using the beneficiary's RSA private key
def decrypt_key_as_beneficiary(encrypted_key_b64: str, private_key_pem: str) -> bytes:
    """Decrypt an AES key using a beneficiary's RSA private key (OAEP+SHA-256).

    Returns the raw AES key bytes.
    """
    # Load the PEM private key — password=None because we store unencrypted private keys
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )
    # Decode the base64-encoded ciphertext back to raw bytes
    encrypted = base64.b64decode(encrypted_key_b64)
    # Decrypt using the same OAEP+SHA-256 parameters used during encryption
    return private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


# derive_key turns a user's password into a 256-bit AES key using Argon2id
def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password using Argon2id.

    Parameters follow OWASP recommendations:
      time_cost=3, memory_cost=64MB, parallelism=4
    Used for user-side key derivation (not for server-side bcrypt auth).
    """
    # hash_secret_raw returns raw bytes (not the encoded $argon2id$... string)
    return hash_secret_raw(
        # Encode the password as UTF-8 bytes before hashing
        secret=password.encode("utf-8"),
        # Random salt prevents rainbow table attacks (a different salt per secret)
        salt=salt,
        # CPU/memory cost parameters — must match the frontend Argon2id call exactly
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        # Output 32 bytes — the correct size for an AES-256 key
        hash_len=ARGON2_HASH_LEN,
        # Type.ID selects Argon2id variant (hybrid of Argon2i and Argon2d)
        type=Type.ID,
    )
