
import os
import sys
import traceback
import logging

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
from www.Lib.Crypto.encryption import security
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.urls import reverse
from www.Apps.lm_user_config import UsersStatus
from www.Apps.lm_table_names import TableNames
from www.Lib.External import mail_client
from www.Lib.External import login_naver_client
from www.Lib.External import login_kakao_client
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def userDetail(request, seq):
    try:

        status_list = UsersStatus.choices
        # 탈퇴 및 삭제를 제외한 리스트만 템플릿으로 전달
        filtered_choices = [(v, l) for v, l in UsersStatus.choices if v not in ['DELETED', 'API_DELETED', 'ADMIN']]

        with connection.cursor() as cursor:
            # 1. 회원 정보 조회
            sql = f"SELECT * FROM {TableNames.Users} WHERE seq = %s"
            cursor.execute(sql, [seq])
            # fetchall 대신 dict 형태로 가져오기 위한 처리 (또는 전용 유틸리티 사용)
            columns = [col[0] for col in (cursor.description or [])]
            row = cursor.fetchone()
            
            if not row:
                return render(request, '404.html', {'msg': '회원을 찾을 수 없습니다.'})
            
            user = dict(zip(columns, row))

            # 2. 복호화 처리 (보안 정책에 따라 필요한 필드만)
            user['dec_email'] = security.decrypt(user['d_email'])
            user['dec_phone'] = security.decrypt(user['d_phone']) if user['d_phone'] else ""
            user['dec_ip'] = security.decrypt(user['d_last_login_ip']) if user['d_last_login_ip'] else ""
            user['dec_name'] = security.decrypt(user['d_name']) if user['d_name'] else ""
            user['profile_image'] = user['profile_image'] if user['profile_image'] else "/static/img/avatar.png"

            print("user" , user)

            # 2. 접속 이력(Login Logs) 조회 (최근 10건)
            log_sql = """
                SELECT * FROM lm_login_logs 
                WHERE user_seq = %s 
                ORDER BY created_at DESC LIMIT 10
            """
            cursor.execute(log_sql, [seq])
            log_columns = [col[0] for col in (cursor.description or [])]
            log_rows = cursor.fetchall()
            
            login_logs = []
            for row in log_rows:
                log_dict = dict(zip(log_columns, row))
                # IP 복호화 처리
                log_dict['dec_ip'] = security.decrypt(log_dict['enc_ip'])
                login_logs.append(log_dict)


        return render(request, 'UserAccount/user_detail.html', {
            'user': user,
            'login_logs': login_logs, # 템플릿으로 전달
            'status_list' : filtered_choices
            })

    except Exception as e:
        # 에러 핸들링 로직...
        return render(request, 'error.html', {'error': str(e)})




def updatePoint(request):
    if request.method != 'POST':
        # [핵심] POST 요청이 아닐 경우 처리 (405 에러 또는 목록으로 리다이렉트)
        # return HttpResponseNotAllowed(['POST']) 
        return HttpResponseRedirect(reverse('UserAccount:user_list'))

    seq = request.POST.get('user_seq')
    point_type = request.POST.get('point_type')
    amount = int(request.POST.get('amount', 0))
    
    # 실제 DB 업데이트 로직 (Raw SQL 예시)
    operator = '+' if point_type == 'plus' else '-'
    sql = f"UPDATE  {TableNames.Users}  SET point = point {operator} %s WHERE seq = %s"

    try:
        with connection.cursor() as cursor:
            with transaction.atomic():
                cursor.execute(sql, [amount, seq])


        return HttpResponseRedirect(reverse('UserAccount:userDetail', args=[seq]))
    
    except Exception as e:
        # 에러 발생 시 여기서 처리
        print(f"트랜잭션 롤백됨: {e}")
        return HttpResponseRedirect(reverse('UserAccount:userList'))      



def updateState(request):
    if request.method != 'POST':
        # [핵심] POST 요청이 아닐 경우 처리 (405 에러 또는 목록으로 리다이렉트)
        # return HttpResponseNotAllowed(['POST']) 
        return HttpResponseRedirect(reverse('UserAccount:user_list'))        

    seq = request.POST.get('user_seq')
    new_state = request.POST.get('new_state')
    strNewStateLabel = UsersStatus(new_state).label

    # 1. 반복문으로 상세히 보기
    print("--- POST Detail ---")
    for key, value in request.POST.items():
        print(f"POST Key: {key} | Value: {value}")
    print("----------------------")


    # 2. 반복문으로 상세히 보기
    print("--- Session Detail ---")
    for key, value in request.session.items():
        print(f"session Key: {key} | Value: {value}")
    print("----------------------")

    sql = f"UPDATE  {TableNames.Users}  SET status = %s WHERE seq = %s"

    try:
        with connection.cursor() as cursor:
            with transaction.atomic():
                cursor.execute(sql, [new_state, seq])

        messages.info(request, f"상태를 {strNewStateLabel}로 변경했습니다.")
        return HttpResponseRedirect(reverse('UserAccount:userDetail', args=[seq]))
    
    except Exception as e:
        # 에러 발생 시 여기서 처리
        print(f"트랜잭션 롤백됨: {e}")
        return HttpResponseRedirect(reverse('UserAccount:userList'))   


    # messages.success(request, "상태 변경이 완료되었습니다.")
    # return HttpResponseRedirect(reverse('UserAccount:userDetail', args=[seq]))



# --- 메인 View 함수 ---
def userWithdrawForm(request, seq):
    
    intAdminSeq = request.session.get('_auth_user_id')
    print("intAdminSeq : " , intAdminSeq)
    """
    회원 강제 탈퇴 처리 폼 및 라우팅 제어
    """
    # 1. 대상 회원 정보 조회 (화면 표시용)
    user_data = None
    try:
        with connection.cursor() as cursor:
            sql = f"""
                SELECT seq, nickname, d_email, status, d_name,level,provider,profile_image,point
                FROM {TableNames.Users} 
                WHERE seq = %s
                """
            cursor.execute(sql, [seq])
            
            # 요청하신 표기법 적용
            log_columns = [col[0] for col in (cursor.description or [])]
            row = cursor.fetchone()
            
            if not row:
                return HttpResponse("해당 회원을 찾을 수 없습니다.", status=404)
            
            user_data = dict(zip(log_columns, row))
            if user_data.get('d_email'):
                user_data['dec_email'] = security.decrypt(user_data['d_email'])

            if user_data.get('d_name'):
                user_data['dec_name'] = security.decrypt(user_data['d_name'])


    except Exception as e:
        print(f"Fetch Error: {e}")
        user_data = {'seq': seq, 'nickname': '회원'}

    # 3. 화면 렌더링
    return render(request, 'UserAccount/user_withdraw_form.html', {
        'user': user_data,
        'target_seq': seq
    })






def doWithdraw(request):
    # IP 정보 추출
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    user_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    user_seq = request.POST.get('user_seq')
    print("user_seq : " , user_seq)

    intAdminSeq = request.session.get('_auth_user_id')
    print("intAdminSeq : " , intAdminSeq)

    strAdminId = request.session.get('u_id')
    print("strAdminId : " , strAdminId)


    # 1. 폼 데이터 수집
    reasons_list = request.POST.getlist('withdraw_reason') # ['service_quality', 'too_many_ads']
    reasons_str = ",".join(reasons_list)         # 문자열로 병합
    reason_detail = request.POST.get('admin_note', '').strip()

    user_pw = request.POST.get('admin_password')

    # Django 내장 인증 함수 (DB와 대조)
    user = authenticate(request, username=strAdminId, password=user_pw)

    print('user ==> ' , type(user) , user)

    if user is None or not isinstance(user, User):

        # 수정 후 (user_seq 변수를 함께 전달)
        messages.error(request, "관리자 정보가 일치 하지 않습니다.")
        return redirect('UserAccount:userWithdrawForm', seq=user_seq)   



    try:
        with connection.cursor() as cursor:

            sqlSelectAdminInfo = f""" 
                SELECT * FROM {TableNames.AdminUser}
                WHERE id = %s
            """
            cursor.execute(sqlSelectAdminInfo, [intAdminSeq])
            row = cursor.fetchone()
            # [해결] 데이터가 없는 경우에 대한 예외 처리 추가
            if not row:
                messages.error(request, "로그아웃 되었습니다.")
                return redirect('AdminAccount:login_form')

            transaction.set_autocommit(False)

            # 2. 본인 확인 (비밀번호 검증)
            cursor.execute(f"SELECT s_password, provider FROM {TableNames.Users} WHERE seq = %s", [user_seq])
            row = cursor.fetchone()

            # [해결] 데이터가 없는 경우에 대한 예외 처리 추가
            if not row:
                raise Exception(f"[{__file__}:{sys._getframe().f_lineno}] 오류가 발생했습니다.")

            db_pw_hash = row[0]
            db_provider = row[1]
            # 3. 트랜잭션 시작: 상태 변경 + 로그 기록

            # A. 회원 상태 변경
            sql_update_user = f"""
                UPDATE {TableNames.Users} SET 
                status = 'DELETED', 
                d_name = '', 
                nickname = null,
                ci = null,
                profile_image = null,
                d_phone = null,
                level = 1,
                point = 0,
                verification='0000'
                WHERE seq = %s"""
            cursor.execute(sql_update_user, [user_seq])


            if db_provider == 'naver':
                #네이버 DROP 처리
                if not login_naver_client.revoke_naver_token(cursor,user_seq):
                    raise Exception(f"[{__file__}:{sys._getframe().f_lineno}] 오류가 발생했습니다.")

                sql_delete_social = f""" 
                        DELETE FROM {TableNames.SocialAccounts} WHERE user_seq= %s LIMIT 1
                """
                cursor.execute(sql_delete_social, [user_seq])

            elif db_provider == 'kakao':
                # #카카오 DROP 처리
                if not login_kakao_client.revoke_kakao_token(cursor,user_seq):
                    raise Exception(f"[{__file__}:{sys._getframe().f_lineno}] 오류가 발생했습니다.")

                sql_delete_social = f""" 
                        DELETE FROM {TableNames.SocialAccounts} WHERE user_seq= %s LIMIT 1
                """
                cursor.execute(sql_delete_social, [user_seq])

            # B. 탈퇴 로그 삽입
            reason_detail += f"- 관리자({intAdminSeq}) 탈퇴"
            sql_insert_log = f"""
                INSERT INTO {TableNames.WithdrawalLogs} 
                (user_seq, reasons, reason_detail, d_ip, ip_hash) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql_insert_log, [
                user_seq, 
                reasons_str, 
                reason_detail, 
                security.encrypt(user_ip), 
                security.make_search_hash(user_ip)
            ])

            transaction.commit()

        messages.success(request, "탈퇴 처리가 완료되었습니다.")
        return redirect('UserAccount:user_list') # 성공 시 반환값 추가
    
    except Exception as e:
        transaction.rollback()
        print(f"Withdrawal Error: {e}")
        messages.error(request, "탈퇴 처리 중 오류가 발생했습니다.")
        return redirect('UserAccount:userWithdrawForm', seq=user_seq)