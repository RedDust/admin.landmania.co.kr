import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from Lib.Crypto import two_way_encryption as encrypt_function
from www.Lib.Crypto.encryption import security
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def log_list(request):
    page = request.GET.get('page', 1)
    limit = 15
    offset = (int(page) - 1) * limit

    with connection.cursor() as cursor:
        # 1. 전체 로그 개수 조회
        cursor.execute("SELECT COUNT(*) FROM lm_login_logs")
        total_count = (cursor.fetchone() or (0,))[0]

        # 2. Raw SQL 실행 (JOIN을 통해 사용자 닉네임과 이메일 함께 가져오기)
        query = """
            SELECT 
                l.*, 
                u.nickname, 
                u.d_email as user_email,
                u.provider
            FROM lm_login_logs l
            LEFT JOIN lm_users u ON l.user_seq = u.seq
            ORDER BY l.seq DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, [limit, offset])
        logs = dictfetchall(cursor)

    # 3. 데이터 후처리 (IP 복호화 및 이메일 복호화)
    for log in logs:
        log['dec_ip'] = security.decrypt(log['enc_ip'])
        log['dec_user_email'] = security.decrypt(log['user_email']) if log['user_email'] else "알 수 없음"
        
        # User Agent가 너무 길면 잘라서 보여주기 위해 처리 (선택사항)
        if log['user_agent'] and len(log['user_agent']) > 50:
            log['short_agent'] = log['user_agent'][:50] + "..."
        else:
            log['short_agent'] = log['user_agent']

    # 4. 페이징 객체 생성 (UI 연동용)
    paginator = Paginator(range(total_count), limit)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'logs': logs,
        'page_obj': page_obj,
        'total_count': total_count
    }
    return render(request, 'UserAccount/login_log_list.html', context)