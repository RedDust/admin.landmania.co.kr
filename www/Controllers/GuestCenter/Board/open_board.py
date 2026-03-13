import os
import sys
import traceback
import base64

import logging
import requests
import urllib.parse
import secrets
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.shortcuts import render , redirect
from django.http import HttpResponse
from django.db import connection
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
from Lib.Crypto import two_way_encryption as encrypt_function
from django.contrib import messages
from django.utils import timezone
from www.Apps.lm_user_config import UsersStatus
from www.Apps.lm_table_names import TableNames
from www.Lib.Crypto.encryption import security
from www.Lib.External import mail_client
from www.Lib.Exception.custom_exception import CustomException
from django.db import connection, transaction
from www.Lib.Helpers import client_helper, user_helper
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.validators import validate_email
from django.urls import reverse

logger = logging.getLogger('Landmania')



def BoardList(request):
    search_type = request.GET.get('search_type', 'all')
    keyword = request.GET.get('keyword', '').strip()
    page = request.GET.get('page', '1')
    delete_status = request.GET.get('delete_status', 'all') # 삭제 여부 필터 추가
    limit = 10
    offset = (int(page) - 1) * limit


    # 1. 동적 WHERE 절 구성 (is_deleted 조건 유연화)
    where_clause = "WHERE 1=1" # 기본 조건
    params = []

    # 삭제 여부에 따른 필터링
    if delete_status == 'N':
        where_clause += " AND is_deleted = 'N'"
    elif delete_status == 'Y':
        where_clause += " AND is_deleted = 'Y'"
    # 'all'인 경우 조건을 추가하지 않아 모두 조회됨



    if keyword:
        if search_type == 'name':
            where_clause += " AND author_name LIKE %s"
            params.append(f'%{keyword}%')
        elif search_type == 'title':
            where_clause += " AND title LIKE %s"
            params.append(f'%{keyword}%')
        elif search_type == 'content':
            where_clause += " AND content LIKE %s"
            params.append(f'%{keyword}%')
        else: # 전체 검색
            where_clause += " AND (author_name LIKE %s OR title LIKE %s OR email LIKE %s)"
            params.extend([f'%{keyword}%'] * 3)

    # 2. 데이터베이스 조회
    with connection.cursor() as cursor:
        # 전체 카운트
        cursor.execute(f"SELECT COUNT(*) FROM lm_guest_qna {where_clause}", params)
        total_count = (cursor.fetchone() or (0,))[0]

        # 리스트 데이터
        query = f"""
            SELECT * FROM lm_guest_qna 
            {where_clause} 
            ORDER BY seq DESC 
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [limit, offset])
        
        # [Rule] 약속된 안전 표기법 적용
        log_columns = [col[0] for col in (cursor.description or [])]
        rows = [dict(zip(log_columns, row)) for row in cursor.fetchall()]

    # 3. 데이터 후처리 (복호화 및 카테고리 매핑)
    category_map = {'ETC': '기타', 'TECH': '기술문의', 'PAY': '결제문의'} # 예시
    
    for row in rows:
        row['dec_email'] = security.decrypt(row['email']) if row['email'] else '-'
        row['dec_phone'] = security.decrypt(row['phone_number']) if row['phone_number'] else '-'
        row['category_label'] = category_map.get(row['category'], row['category'])

    # 4. 페이징 객체 생성 (UI 연동용)
    paginator = Paginator(range(total_count), limit)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)

    rstData = {
        'items': rows,
        'page_obj': page_obj,
        'total_count': total_count,
        'search_type': search_type,
        'delete_status': delete_status, # 템플릿 유지용
        'keyword': keyword,
    }
    return render(request, 'GuestCenter/Board/board_list.html', rstData)



def BoardDetail(request, seq):

    try:
        with connection.cursor() as cursor:
            # 1. 데이터 조회 (삭제되지 않은 글)
            cursor.execute("SELECT * FROM lm_guest_qna WHERE seq = %s ", [seq])
            
            # [Rule] 안전한 컬럼 추출 표기법 적용
            columns = [col[0] for col in (cursor.description or [])]
            row = cursor.fetchone()

            if not row:
                raise Exception(f"[{__file__}:{sys._getframe().f_lineno}] 오류가 발생했습니다.")
                
            item = dict(zip(columns, row))

            # 2. 조회수 증가 (원자성 보장)
            cursor.execute("UPDATE lm_guest_qna SET hit = hit + 1 WHERE seq = %s", [seq])

        # 3. 데이터 복호화 처리
        item['dec_email'] = security.decrypt(item['email']) if item['email'] else '-'
        item['dec_phone'] = security.decrypt(item['phone_number']) if item['phone_number'] else '-'
        item['dec_ip'] = security.decrypt(item['ip_address']) if item['ip_address'] else '-'
        
        # 4. 카테고리 맵 (필요 시)
        category_map = {'ETC': '기타', 'TECH': '기술문의', 'PAY': '결제문의'}
        item['category_label'] = category_map.get(item['category'], item['category'])

        return render(request, 'GuestCenter/Board/board_detail.html', {'item': item})

    except Exception as e:
        transaction.rollback()
        print(f"Withdrawal Error: {e}")
        messages.error(request, "조회중 오류가 발생했습니다.")
        return redirect(reverse('GuestCenter:Board:GuestBoardList'))   
    


def SaveAnswer(request):
    if request.method == 'POST':
        seq = request.POST.get('seq')
        answer_content = request.POST.get('answer_content', '').strip()

        if not answer_content:
            messages.error(request, "답변 내용을 입력해 주세요.")
            return redirect(reverse('GuestCenter:GuestBoardDetail', kwargs={'seq': seq}))

        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # 답변 업데이트 및 상태 변경
                    sql = """
                        UPDATE lm_guest_qna 
                        SET answer_content = %s, 
                            status = 'COMPLETED', 
                            answered_at = CURRENT_TIMESTAMP 
                        WHERE seq = %s
                    """
                    cursor.execute(sql, [answer_content, seq])
                    
                    # [Rule] 약속된 description 안전 표기법 (로그용)
                    log_columns = [col[0] for col in (cursor.description or [])]

            messages.success(request, "답변이 성공적으로 등록되었습니다.")
        except Exception as e:
            messages.error(request, f"저장 중 오류 발생: {str(e)}")
        
        return redirect(reverse('GuestCenter:Board:GuestBoardDetail', kwargs={'seq': seq}))
    
    return redirect(reverse('GuestCenter:Board:GuestBoardList'))    



def DeleteBoard(request, seq):
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # 1. 해당 게시글이 존재하는지 먼저 확인
                cursor.execute("SELECT seq FROM lm_guest_qna WHERE seq = %s AND is_deleted = 'N'", [seq])
                if not cursor.fetchone():
                    messages.error(request, "존재하지 않거나 이미 삭제된 게시글입니다.")
                    return redirect(reverse('GuestCenter:Board:GuestBoardList'))

                # 2. 삭제 상태('Y')로 업데이트
                sql = "UPDATE lm_guest_qna SET is_deleted = 'Y' WHERE seq = %s"
                cursor.execute(sql, [seq])
                
                # [Rule] 약속된 description 안전 표기법 적용
                log_columns = [col[0] for col in (cursor.description or [])]

        messages.success(request, f"#{seq}번 문의글이 성공적으로 삭제되었습니다.")
    except Exception as e:
        messages.error(request, f"삭제 중 오류가 발생했습니다: {str(e)}")
    
    # 삭제 후 목록 페이지로 이동
    return redirect(reverse('GuestCenter:Board:GuestBoardList'))