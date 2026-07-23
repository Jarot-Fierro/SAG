import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet() -> Fernet:
    # Generar una clave de 32 bytes basada en SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key_base64 = base64.urlsafe_b64encode(key)
    return Fernet(key_base64)


def encrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return value
    f = get_fernet()
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return ""
