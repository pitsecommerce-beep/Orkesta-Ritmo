import os
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_data_key() -> bytes:
    return secrets.token_bytes(32)


def encrypt_with_master_key(data_key: bytes, master_key_hex: str) -> bytes:
    master_key = bytes.fromhex(master_key_hex)
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data_key, None)
    return nonce + ciphertext


def decrypt_with_master_key(encrypted: bytes, master_key_hex: str) -> bytes:
    master_key = bytes.fromhex(master_key_hex)
    aesgcm = AESGCM(master_key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_file(content: bytes, data_key: bytes) -> bytes:
    aesgcm = AESGCM(data_key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, content, None)
    return nonce + ciphertext


def decrypt_file(encrypted: bytes, data_key: bytes) -> bytes:
    aesgcm = AESGCM(data_key)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)


def destroy_data_key(encrypted_data_key: bytes) -> bytes:
    return b'\x00' * len(encrypted_data_key)
