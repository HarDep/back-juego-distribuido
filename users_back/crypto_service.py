from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = base64.b64decode(os.getenv("ENCRYPTION_KEY"))

def encrypt(password:str)-> str:
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(password.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted).decode()

def decrypt(encrypted: str) -> str:
    data = base64.b64decode(encrypted)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode()

def verify_password(plain_password: str, encrypted_password: str) -> bool:
    try:
        decrypted = decrypt(encrypted_password)
        return plain_password == decrypted
    except Exception:
        return False

def is_encrypted(password: str) -> bool:
    try:
        decoded = base64.b64decode(password, validate=True)
        if len(decoded) < 16:
            return False
        iv, encrypted = decoded[:16], decoded[16:]
        cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        unpadder.update(padded_data) + unpadder.finalize()
        return True
    except (ValueError, TypeError):
        return False