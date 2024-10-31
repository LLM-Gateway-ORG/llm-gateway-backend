# Encrypting and decrypting helper functions
from cryptography.fernet import Fernet
from django.conf import settings

ENCRYPTION_KEY = settings.ENCRYPTION_KEY

def encrypt_value(value: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(value.encode()).decode()