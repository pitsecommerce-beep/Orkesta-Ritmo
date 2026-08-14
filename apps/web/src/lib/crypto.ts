const PBKDF2_ITERATIONS = 310_000;
const SALT_BYTES = 16;
const IV_BYTES = 12;

async function deriveKey(
  secret: string,
  salt: Uint8Array
): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: salt as BufferSource, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    keyMaterial,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"]
  );
}

export async function encryptPassword(
  plaintext: string,
  userId: string
): Promise<{ encryptedPassword: Uint8Array; encryptedDataKey: Uint8Array }> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_BYTES));
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES));

  const dataKey = crypto.getRandomValues(new Uint8Array(32));

  const importedDataKey = await crypto.subtle.importKey(
    "raw",
    dataKey,
    "AES-GCM",
    false,
    ["encrypt"]
  );

  const enc = new TextEncoder();
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    importedDataKey,
    enc.encode(plaintext)
  );

  const encryptedPassword = new Uint8Array(
    SALT_BYTES + IV_BYTES + ciphertext.byteLength
  );
  encryptedPassword.set(salt, 0);
  encryptedPassword.set(iv, SALT_BYTES);
  encryptedPassword.set(new Uint8Array(ciphertext), SALT_BYTES + IV_BYTES);

  const wrapKey = await deriveKey(userId, salt);
  const wrapIv = crypto.getRandomValues(new Uint8Array(IV_BYTES));
  const wrappedKey = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv: wrapIv },
    wrapKey,
    dataKey
  );

  const encryptedDataKey = new Uint8Array(IV_BYTES + wrappedKey.byteLength);
  encryptedDataKey.set(wrapIv, 0);
  encryptedDataKey.set(new Uint8Array(wrappedKey), IV_BYTES);

  return { encryptedPassword, encryptedDataKey };
}

export function toBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
