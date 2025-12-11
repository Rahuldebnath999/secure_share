from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os

def encrypt_file(file_content: bytes, key: bytes):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded = file_content + b"\0" * (16 - len(file_content) % 16)
    encrypted = encryptor.update(padded) + encryptor.finalize()
    iv_b64 = base64.b64encode(iv).decode()
    encrypted_b64 = base64.b64encode(encrypted).decode()
    return iv_b64, encrypted_b64

def decrypt_file(encrypted_content_b64: str, iv_b64: str, key: bytes) -> bytes:
    iv = base64.b64decode(iv_b64)
    encrypted = base64.b64decode(encrypted_content_b64)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    return padded.rstrip(b"\0")
