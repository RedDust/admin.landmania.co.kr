from django.db import models

class UsersStatus(models.TextChoices):
    ASSOCIATE = 'ASSOCIATE', '준회원'
    GENERAL = 'GENERAL', '일반회원'
    VERIFICATION = 'VERIFICATION', '실명인증회원'
    PAID = 'PAID', '유료회원'
    INACTIVE = 'INACTIVE', '비활성'
    LOGIN_LOCKED = 'LOGIN_LOCKED', '로그인금지'
    LOCKED = 'LOCKED', '이용금지'
    DELETED = 'DELETED', '탈퇴'
    API_DELETED = "API_DELETED", "연동삭제"
    ADMIN = 'ADMIN', '관리자'


    @property
    def badge_class(self):
        # 상태별 CSS 클래스를 매핑
        mapping = {
            # 강조(Primary/Indigo)
            UsersStatus.VERIFICATION: "bg-primary",
            UsersStatus.PAID: "bg-indigo shadow-sm",
            
            # 긍정/일반(Success/Info)
            UsersStatus.GENERAL: "bg-success",
            UsersStatus.ASSOCIATE: "bg-info-subtle text-info border border-info-subtle",
            
            # 주의/경고(Warning/Orange)
            UsersStatus.LOGIN_LOCKED: "bg-warning text-dark",
            UsersStatus.LOCKED: "bg-orange text-white", # 주황색 (AdminLTE 전용)
            
            # 위험/관리(Danger)
            UsersStatus.ADMIN: "bg-danger fw-bold",
            
            # 무채색/비활성(Secondary/Light)
            UsersStatus.INACTIVE: "bg-secondary",
            UsersStatus.DELETED: "bg-light text-muted border",
            UsersStatus.API_DELETED: "bg-dark-subtle text-decoration-line-through",
        }
        return mapping.get(self, "bg-secondary")