import base64
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.encryption_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
