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
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404


def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def list(request):
    # 1. 검색 및 필터 파라미터 받기
    status_filter = request.GET.get('status', '')  # 'WAITING', 'COMPLETED' 등
    page = request.GET.get('page', 1)
    limit = 15
    offset = (int(page) - 1) * limit

    # 2. 동적 WHERE 절 구성
    where_clause = "WHERE i.is_deleted = 'N'"
    params = []

    if status_filter:
        where_clause += " AND i.status = %s"
        params.append(status_filter)

    with connection.cursor() as cursor:
        # 3. 필터가 적용된 전체 개수 조회 (페이징용)
        count_query = f"SELECT COUNT(*) FROM lm_inquiries i {where_clause}"
        cursor.execute(count_query, params)
        total_count = (cursor.fetchone() or (0,))[0]

        # 4. 필터가 적용된 리스트 조회 (Raw SQL)
        query = f"""
            SELECT 
                i.*, 
                u.nickname as user_nickname,
                u.d_name as user_name,
                u.d_email as user_email
            FROM lm_inquiries i
            LEFT JOIN lm_users u ON i.user_seq = u.seq
            {where_clause}
            ORDER BY i.seq DESC
            LIMIT %s OFFSET %s
        """
        # 필터 파라미터와 페이징 파라미터 병합
        list_params = params + [limit, offset]
        cursor.execute(query, list_params)
        inquiries = dictfetchall(cursor)

    # 5. 데이터 후처리 (복호화 및 제목 길이 조절)
    for item in inquiries:
        # security.decrypt 적용
        item['dec_user_name'] = security.decrypt(item['user_name']) if item['user_name'] else ""
        item['dec_user_email'] = security.decrypt(item['user_email']) if item['user_email'] else ""
        
        if len(item['title']) > 30:
            item['display_title'] = item['title'][:30] + "..."
        else:
            item['display_title'] = item['title']

    # 6. 페이징 객체 생성
    paginator = Paginator(range(total_count), limit)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'inquiries': inquiries,
        'page_obj': page_obj,
        'total_count': total_count,
        'status_filter': status_filter, # 템플릿에서 버튼 활성화 상태 체크용
    }
    return render(request, 'CustomerCenter/qna_list.html', context)


def detail(request, seq):
    # 1. GET/POST 공통: 상세 데이터 조회
    with connection.cursor() as cursor:
        query = """
            SELECT i.*, u.nickname, u.d_name, u.d_email 
            FROM lm_inquiries i
            LEFT JOIN lm_users u ON i.user_seq = u.seq
            WHERE i.seq = %s AND i.is_deleted = 'N'
        """
        cursor.execute(query, [seq])
        rows = dictfetchall(cursor) # NoneType 에러 방지
        
        if not rows:
            raise Http404("문의 내역을 찾을 수 없습니다.")
        
        item = rows[0]

    # 2. 복호화 적용 (새로운 security.decrypt 방식)
    item['dec_user_name'] = security.decrypt(item['d_name']) if item['d_name'] else ""
    item['dec_user_email'] = security.decrypt(item['d_email']) if item['d_email'] else ""

    # 3. 답변 등록 처리 (POST)
    if request.method == "POST":
        # 'answer' 변수를 명확하게 정의합니다.
        answer_text = request.POST.get('answer_content', '').strip()
        admin_seq = 1 # 실제 운영 시 세션에서 관리자 PK를 가져오세요.
        
        if answer_text: # 내용이 있을 때만 업데이트
            with connection.cursor() as cursor:
                update_query = """
                    UPDATE lm_inquiries 
                    SET answer_content = %s, 
                        status = 'COMPLETED', 
                        admin_seq = %s, 
                        answered_at = CURRENT_TIMESTAMP 
                    WHERE seq = %s
                """
                # 정의한 변수명(answer_text)을 리스트에 정확히 전달합니다.
                cursor.execute(update_query, [answer_text, admin_seq, seq])
            
            return redirect('CustomerCenter:qna_detail', seq=seq)

    return render(request, 'CustomerCenter/qna_detail.html', {'item': item})