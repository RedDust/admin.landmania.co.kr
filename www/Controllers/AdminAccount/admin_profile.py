import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from Lib.Crypto import two_way_encryption as encrypt_function
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse  # 이 줄을 추가하세요!
from www.Lib.Crypto.encryption import security
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def detail_from(request):
    print("detail_from => " , detail_from)

    # 2. 반복문으로 상세히 보기
    print("--- Session Detail ---")
    for key, value in request.session.items():
        print(f"session Key: {key} | Value: {value}")
    print("----------------------")

    AdminSeq = request.session.get('u_seq')


    with connection.cursor() as cursor:
        # auth_user 테이블에서 관리자 데이터 조회
        sql = "SELECT * FROM auth_user WHERE id = %s"
        cursor.execute(sql, [AdminSeq])
        
        # [Rule] 안전한 컬럼 추출 표기법 적용
        columns = [col[0] for col in (cursor.description or [])]
        row = cursor.fetchone()
        
        if not row:
            return render(request, 'error.html', {'error': '관리자 정보를 찾을 수 없습니다.'})
            
        admin_data = dict(zip(columns, row))

    return render(request, 'AdminAccount/admin_detail.html', {
        'admin': admin_data
    })
            


def DoUpdateAdmin(request):

    if request.method == 'POST':
        # 1. 폼 데이터 수집
        # admin_id는 URL에서 받거나 폼의 hidden input으로 전달받는다고 가정합니다.
        admin_seq = request.session.get('u_seq') 
        email = request.POST.get('email')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        username =  request.session.get('u_id')


        # 체크박스(스위치)는 체크되지 않으면 데이터가 전송되지 않으므로 존재 여부로 판단합니다.
        is_active = 1 if request.POST.get('is_active') == 'on' else 0
        is_staff = 1 if request.POST.get('is_staff') == 'on' else 0

        print("admin_seq ==> " , admin_seq)
        print("email ==> " , email)
        print("last_name ==> " , last_name)
        print("first_name ==> " , first_name)
        print("username ==> " , username)        

        print("is_active ==> " , is_active)
        print("is_staff ==> " , is_staff)

        try:
            # 2. 데이터베이스 업데이트 (원자성 보장)
            with transaction.atomic():
                with connection.cursor() as cursor:
                    sql = """
                        UPDATE auth_user 
                        SET email = %s, 
                            last_name = %s, 
                            first_name = %s, 
                            is_active = %s, 
                            is_staff = %s 
                        WHERE id = %s
                    """
                    params = [email, last_name, first_name, is_active, is_staff, admin_seq]
                    cursor.execute(sql, params)
                    
                    print("params : " , params)


                # 모든 정보를 세션에 저장

                request.session['u_name'] = f"{first_name}{last_name}"
                request.session['u_email'] = email
                request.session['u_is_staff'] = is_staff
                request.session['u_is_superuser'] = is_active

                # # [Rule] 약속된 description 표기법 (필요 시 로그 기록용)
                # log_columns = [col[0] for col in (cursor.description or [])]

            # 3. 성공 메시지 및 리다이렉트
            messages.success(request, f"관리자({username})의 설정이 성공적으로 저장되었습니다.")
            return redirect(reverse('AdminAccount:adminDetailFrom'))

        except Exception as e:
            # 에러 발생 시 처리
            messages.error(request, f"업데이트 중 오류가 발생했습니다: {str(e)}")
            return redirect(reverse('AdminAccount:adminDetailFrom'))

    # POST가 아닐 경우 목록으로 튕겨내기
    messages.error(request, f"업데이트 중 오류가 발생했습니다")
    return redirect('AdminAccount:adminDetailFrom')


