import os
import sys
import traceback
import logging

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.core.validators import validate_email
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from Lib.Crypto import two_way_encryption as encrypt_function
from www.Lib.Crypto.encryption import security
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.urls import reverse
from www.Apps.lm_user_config import UsersStatus
from www.Apps.lm_table_names import TableNames
from django.db import connection
from django.core.paginator import Paginator
from www.Apps.lm_user_config import UsersStatus

logger = logging.getLogger('Landmania')


def dictfetchall(cursor):
    """커서의 결과를 Dict 형태로 변환"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def userList(request):
    
    search_type = request.GET.get('search_type', 'all')
    keyword = request.GET.get('keyword', '').strip()
    page = request.GET.get('page', '1')

    status_dict = dict(UsersStatus.choices)

    limit = 20
    offset = (int(page) - 1) * limit

    with connection.cursor() as cursor:


        # 2. 검색 조건(WHERE) 동적 구성
        where_clause = "WHERE 1=1"
        params = []


        if keyword:
            if search_type == 'name':
                where_clause += " AND (nickname LIKE %s OR d_name LIKE %s)"
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            elif search_type == 'email':
                where_clause += " AND email_hash LIKE %s"
                validate_email(keyword)
                target_email_hash = security.make_search_hash(keyword)
                params.append(f'%{target_email_hash}%')
            elif search_type == 'provider':
                where_clause += " AND provider LIKE %s"
                params.append(f'%{keyword}%')
            elif search_type == 'phone':
                where_clause += " AND phone_hash LIKE %s"
                target_phone_hash = security.make_search_hash(keyword)
                params.append(f'%{target_phone_hash}%')                
            elif search_type == 'ip':
                where_clause += " AND hash_last_login_ip LIKE %s"
                target_login_ip_hash = security.make_search_hash(keyword)
                params.append(f'%{target_login_ip_hash}%')
            else: # 전체 검색 (all)
                where_clause += """ AND (nickname LIKE %s OR d_name LIKE %s 
                                    OR email_hash LIKE %s OR phone_hash LIKE %s 
                                    OR hash_last_login_ip LIKE %s) """
                params.extend([
                               f'%{keyword}%',
                               f'%{keyword}%',
                               security.make_search_hash(keyword),
                               security.make_search_hash(keyword),
                               security.make_search_hash(keyword)
                               ] )



        # 1. 전체 데이터 개수 조회 (페이징용)
        count_query = f"SELECT COUNT(*) FROM {TableNames.Users} {where_clause}"
        cursor.execute(count_query, params)
        total_count = (cursor.fetchone() or (0,))[0]



        # 2. Raw SQL 실행 (LIMIT, OFFSET 사용)
        query = f"""
            SELECT * FROM {TableNames.Users} 
            {where_clause}
            ORDER BY seq DESC 
            LIMIT %s OFFSET %s
        """

        print("query ==> " , query)
        print("params ==> " , params)

        cursor.execute(query, params +[limit, offset])
        rows = dictfetchall(cursor)

    # 3. 데이터 후처리 (양방향 데이터 복호화)
    for row in rows:
        # 양방향 필드 복호화 security.decrypt(DBuser_email)
        row['dec_email'] = security.decrypt(row['d_email'])
        row['nickname'] = row['nickname']
        row['dec_name'] = security.decrypt(row['d_name'])
        row['dec_phone'] = security.decrypt(row['d_phone'])
        row['dec_ip'] = security.decrypt(row['d_last_login_ip'])
        row['provider'] = row['provider']
        
        # 단방향 및 해시는 원본 그대로 유지 (s_password, email_hash)
        logger.info(security.decrypt(row['d_email']))
        logger.info(len( security.decrypt(row['d_email'])))

    # 4. Django Paginator를 수동으로 연동 (UI 편의성)
    # 실제 DB 조회를 20개만 했으므로, 가짜 리스트를 만들어 Paginator 객체 생성
    dummy_list = range(total_count) 
    paginator = Paginator(dummy_list, limit)
    
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'users': rows,
        'page_obj': page_obj,
        'total_count': total_count,
        'status_dict': status_dict, # 템플릿에 전달
        'search_type': search_type, # 검색 상태 유지용
        'keyword': keyword,         # 검색어 유지용        
    }
    
    return render(request, 'UserAccount/user_list.html', context)

