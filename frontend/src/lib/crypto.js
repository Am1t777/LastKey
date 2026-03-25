import { argon2id } from '@noble/hashes/argon2.js'

function base64ToBytes(b64) {
  const bin = atob(b64)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return bytes
}

function concat(a, b) {
  const result = new Uint8Array(a.length + b.length)
  result.set(a, 0)
  result.set(b, a.length)
  return result
}

function pemToBuffer(pem) {
  const lines = pem.replace(/\r/g, '').split('\n').filter(l => l && !l.startsWith('-----'))
  return base64ToBytes(lines.join(''))
}

export async function decryptSecretAsOwner(password, ownerEncryptedKey, encContent, encIv, encTag) {
  const [salt_b64, ct_b64, iv_b64, tag_b64] = ownerEncryptedKey.split(':', 4)
  // Argon2id params match backend encryption_service.py: t=3, m=65536, p=4, dkLen=32
  const hash = argon2id(new TextEncoder().encode(password), base64ToBytes(salt_b64), {
    t: 3, m: 65536, p: 4, dkLen: 32,
  })
  const ownerKey = await crypto.subtle.importKey('raw', hash, 'AES-GCM', false, ['decrypt'])
  const aesKeyB64Bytes = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(iv_b64) },
    ownerKey,
    concat(base64ToBytes(ct_b64), base64ToBytes(tag_b64)),
  )
  const aesKeyBytes = base64ToBytes(new TextDecoder().decode(aesKeyB64Bytes))
  const contentKey = await crypto.subtle.importKey('raw', aesKeyBytes, 'AES-GCM', false, ['decrypt'])
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(encIv) },
    contentKey,
    concat(base64ToBytes(encContent), base64ToBytes(encTag)),
  )
  return new TextDecoder().decode(plaintext)
}

export async function decryptSecretAsBeneficiary(privatePem, encKeyB64, encContent, encIv, encTag) {
  const privateKey = await crypto.subtle.importKey(
    'pkcs8', pemToBuffer(privatePem),
    { name: 'RSA-OAEP', hash: 'SHA-256' }, false, ['decrypt'],
  )
  const aesKeyBytes = await crypto.subtle.decrypt({ name: 'RSA-OAEP' }, privateKey, base64ToBytes(encKeyB64))
  const contentKey = await crypto.subtle.importKey('raw', aesKeyBytes, 'AES-GCM', false, ['decrypt'])
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: base64ToBytes(encIv) },
    contentKey,
    concat(base64ToBytes(encContent), base64ToBytes(encTag)),
  )
  return new TextDecoder().decode(plaintext)
}
