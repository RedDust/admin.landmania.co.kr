import os
import hashlib
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
import string


# .env 파일 로드
load_dotenv()

class SecurityManager:
    def __init__(self):
        # 1. 환경 변수에서 키 로드
        self.encryption_key = os.getenv('FIELD_ENCRYPTION_KEY')
        self.pepper = os.getenv('SECURITY_PEPPER')
        
        if not self.encryption_key or not self.pepper:
            raise ValueError("보안 설정이 누락되었습니다. .env 파일을 확인하세요.")

        # 2. 객체 초기화 (매번 생성하지 않도록 싱글톤처럼 활용)
        self.cipher = Fernet(self.encryption_key.encode())
        self.password_hasher = PasswordHasher()

    # --- [A] 양방향 암호화 (이메일, 이름, 전화번호용) ---
    def encrypt(self, plain_text: str) -> str:
        if not plain_text: return None
        return self.cipher.encrypt(plain_text.encode('utf-8')).decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text: return None
        try:
            return self.cipher.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
        except Exception:
            return "[Decryption Failed]"

    # --- [B] 단방향 해싱 (비밀번호용 - Argon2id) ---
    def hash_password(self, password: str) -> str:
        # 비밀번호에 시스템 페퍼를 섞어서 해싱
        return self.password_hasher.hash(password + self.pepper)

    def verify_password(self, hashed_password: str, input_password: str) -> bool:
        try:
            return self.password_hasher.verify(hashed_password, input_password + self.pepper)
        except VerifyMismatchError:
            return False

    # --- [C] 검색용 결정적 해시 (이메일 검색용 - SHA-256) ---
    def make_search_hash(self, data: str) -> str:
        """암호화된 데이터를 DB 인덱스로 찾기 위한 해시 생성"""
        if not data: return None
        return hashlib.sha256((data + self.pepper).encode('utf-8')).hexdigest()
    
    def generate_verification_code(self,length=6):
        """6자리 숫자 인증번호 생성"""
        # string.digits는 '0123456789' 문자열입니다.
        characters = string.digits 
        # secrets.choice를 사용하여 보안상 강력한 무작위 번호 생성
        code = ''.join(secrets.choice(characters) for _ in range(length))
        return code    


    def mask_email(self, email:str):
        """
        아이디와 도메인을 모두 마스킹 처리하는 함수
        예: reddust9@naver.com -> redd****@na***.com
        예: user@daum.net -> u***@da**.net
        """
        try:
            if "@" not in email:
                return email
                
            local_part, domain_part = email.split("@")
            
            # 1. 아이디(Local Part) 마스킹 로직
            if len(local_part) <= 3:
                masked_local = local_part[0] + "*" * (len(local_part) - 1)
            else:
                masked_local = local_part[:4] + "*" * (len(local_part) - 4)
                
            # 2. 도메인(Domain Part) 마스킹 로직
            if "." in domain_part:
                # naver.com -> sld: naver, tld: .com 분리
                sld, tld = domain_part.split(".", 1)
                
                if len(sld) <= 2:
                    masked_sld = sld[0] + "*" * (len(sld) - 1)
                else:
                    # 도메인 앞 2글자만 노출
                    masked_sld = sld[:2] + "*" * (len(sld) - 2)
                
                masked_domain = f"{masked_sld}.{tld}"
            else:
                # 점(.)이 없는 특수 도메인일 경우
                masked_domain = domain_part[:2] + "*" * (len(domain_part) - 2)
                
            return f"{masked_local}@{masked_domain}"
        except:
            return email

# 전역 인스턴스 생성
security = SecurityManager()