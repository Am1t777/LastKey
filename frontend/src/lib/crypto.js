// argon2id is a pure-JS implementation of the Argon2id key derivation function
// It must match the backend encryption_service.py parameters exactly (t=3, m=65536, p=4, dkLen=32)
import { argon2id } from '@noble/hashes/argon2.js'

// base64ToBytes converts a base64-encoded string to a Uint8Array of raw bytes
// This is needed because the Web Crypto API works with ArrayBuffers/Uint8Arrays, not strings
function base64ToBytes(b64) {
  // atob() decodes base64 to a binary string (each character is one byte)
  const bin = atob(b64)
  // Allocate a typed array the same length as the decoded binary string
  const bytes = new Uint8Array(bin.length)
  // Copy each character's char code into the typed array as a byte value
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return bytes
}

// concat joins two Uint8Arrays into one — used to reassemble ciphertext + authentication tag
// The Web Crypto API's AES-GCM decrypt expects them concatenated
function concat(a, b) {
  // Allocate a new array large enough to hold both inputs
  const result = new Uint8Array(a.length + b.length)
  // Copy `a` starting at offset 0
  result.set(a, 0)
  // Copy `b` immediately after `a`
  result.set(b, a.length)
  return result
}

// pemToBuffer strips the PEM header/footer and newlines from a PEM-encoded key
// and returns the raw DER bytes as a Uint8Array — required by Web Crypto's importKey
function pemToBuffer(pem) {
  // Split on newlines, remove carriage returns, and filter out blank lines and "-----" header/footer lines
  const lines = pem.replace(/\r/g, '').split('\n').filter(l => l && !l.startsWith('-----'))
  // Join all content lines and base64-decode the result to get the raw DER bytes
  return base64ToBytes(lines.join(''))
}

// decryptSecretAsOwner decrypts a secret using the owner's password
// This mirrors the server-side _decrypt_aes_key_from_owner + decrypt_content flow
export async function decryptSecretAsOwner(password, ownerEncryptedKey, encContent, encIv, encTag) {
  // Split the owner_encrypted_key packed string into its four base64 components
  // Format: salt_b64:ct_b64:iv_b64:tag_b64 (matches secret_service.py _pack/_unpack)
  const [salt_b64, ct_b64, iv_b64, tag_b64] = ownerEncryptedKey.split(':', 4)

  // Derive the owner's AES key from their password using Argon2id
  // Parameters MUST match backend: time_cost=3, memory_cost=65536 KiB, parallelism=4, output=32 bytes
  const hash = argon2id(new TextEncoder().encode(password), base64ToBytes(salt_b64), {
    t: 3,       // time cost (iterations)
    m: 65536,   // memory cost in KiB (64 MB)
    p: 4,       // parallelism (threads)
    dkLen: 32,  // output key length in bytes (256 bits for AES-256)
  })

  // Import the Argon2id-derived key into the Web Crypto API as an AES-GCM decryption key
  const ownerKey = await crypto.subtle.importKey('raw', hash, 'AES-GCM', false, ['decrypt'])

  // Decrypt the encrypted AES key using the Argon2id-derived key
  // The backend stores ciphertext and tag separately, so we must concatenate them before decrypting
  const aesKeyB64Bytes = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(iv_b64) },  // Use the stored IV/nonce
    ownerKey,
    concat(base64ToBytes(ct_b64), base64ToBytes(tag_b64)), // Rejoin ciphertext + auth tag
  )

  // The decrypted bytes are the UTF-8 string representation of the base64-encoded AES key
  // Decode bytes → UTF-8 string → base64-decode → raw AES key bytes
  const aesKeyBytes = base64ToBytes(new TextDecoder().decode(aesKeyB64Bytes))

  // Import the recovered AES key into the Web Crypto API for content decryption
  const contentKey = await crypto.subtle.importKey('raw', aesKeyBytes, 'AES-GCM', false, ['decrypt'])

  // Use the AES key to decrypt the actual secret content
  // Again concatenate the stored ciphertext and auth tag before passing to decrypt
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(encIv) },  // Use the secret's stored IV
    contentKey,
    concat(base64ToBytes(encContent), base64ToBytes(encTag)), // Rejoin ciphertext + auth tag
  )

  // Convert the decrypted bytes back to a readable UTF-8 string and return it
  return new TextDecoder().decode(plaintext)
}

// decryptSecretAsBeneficiary decrypts a secret using the beneficiary's RSA private key
// This is used on the /release page after the dead man's switch fires
export async function decryptSecretAsBeneficiary(privatePem, encKeyB64, encContent, encIv, encTag) {
  // Import the RSA private key from PEM format into the Web Crypto API
  // 'pkcs8' is the standard format for private keys (matches the backend's PKCS8 serialization)
  const privateKey = await crypto.subtle.importKey(
    'pkcs8', pemToBuffer(privatePem),
    { name: 'RSA-OAEP', hash: 'SHA-256' }, // RSA-OAEP with SHA-256 — matches backend encryption
    false,        // The key is not extractable (more secure)
    ['decrypt'],  // Only allow this key to be used for decryption
  )

  // Decrypt the encrypted AES key using the beneficiary's RSA private key (OAEP padding)
  // The result is the raw 32-byte AES-256 key that was used to encrypt the secret content
  const aesKeyBytes = await crypto.subtle.decrypt({ name: 'RSA-OAEP' }, privateKey, base64ToBytes(encKeyB64))

  // Import the recovered AES key into Web Crypto for content decryption
  const contentKey = await crypto.subtle.importKey('raw', aesKeyBytes, 'AES-GCM', false, ['decrypt'])

  // Decrypt the secret content using the AES key
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(encIv) },  // Use the stored nonce
    contentKey,
    concat(base64ToBytes(encContent), base64ToBytes(encTag)), // Rejoin ciphertext + auth tag
  )

  // Convert the decrypted bytes to a UTF-8 string and return it
  return new TextDecoder().decode(plaintext)
}
