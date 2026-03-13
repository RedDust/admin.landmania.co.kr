import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings

# 1. 아예 별도의 키를 .env에서 가져오는 것을 추천합니다.
# 만약 SECRET_KEY를 써야만 한다면 KDF를 거쳐야 합니다.
def get_fernet():
    # 고정된 Salt (이것도 .env에 두는 것이 좋음)
    salt = b'some_fixed_salt_for_db_encryption' 
    
    # PBKDF2를 사용하여 SECRET_KEY로부터 강력한 32바이트 키 추출
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    # settings.DB_ENCRYPTION_KEY가 따로 없다면 SECRET_KEY를 소스로 사용
    key_source = getattr(settings, 'DB_ENCRYPTION_KEY', settings.SECRET_KEY)
    key = base64.urlsafe_b64encode(kdf.derive(key_source.encode()))
    return Fernet(key)

# 객체를 미리 생성해두어 재사용 (성능 최적화)
_FERNET_INSTANCE = None

def get_instance():
    global _FERNET_INSTANCE
    if _FERNET_INSTANCE is None:
        _FERNET_INSTANCE = get_fernet()
    return _FERNET_INSTANCE

def encrypt_data(data):
    if not data: return None
    f = get_instance()
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data: return None
    f = get_instance()
    try:
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return "복호화 실패 (키가 다르거나 데이터가 손상됨)"