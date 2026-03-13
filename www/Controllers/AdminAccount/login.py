import os
import sys
import traceback

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
import base64
from Lib.Crypto import two_way_encryption as encrypt_function
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

def form(request):

    try:
        
        rstData = {
            'TITLE' : 'Home',
        }


        # return HttpResponse('ddd')
        return render(request, 'AdminAccount/login_form.html' ,rstData)
        # return render(request, 'Temp/index.html' ,rstData)
        # return render(request, 'index.html' ,rstData)

    except Exception as e:
        print(e)
        print(type(e))
        err_msg = str(traceback.format_exc())
        print(err_msg)
        return JsonResponse({'result': 'FAILURE'})
    


def doLogin(request):
    # 1. POST 요청일 때 (로그인 버튼을 눌렀을 때)
    if request.method == 'POST':
        try:
            # HTML의 name="username"과 name="password"에서 데이터를 가져옴
            user_id = request.POST.get('username')
            user_pw = request.POST.get('password')

            # Django 내장 인증 함수 (DB와 대조)
            user = authenticate(request, username=user_id, password=user_pw)

            # print('user ==> ' , type(user) , user)
            # aaa = isinstance(user, User)
            # print('aaa ==> ' , type(aaa) , aaa)                    
            
            if user is not None and isinstance(user, User):
                # 인증 성공: 세션에 로그인 정보 기록
                login(request, user)
               
                # if user.is_active is not 1:
                #     messages.error(request, "사용할 수 없는 관리자 입니다.")                    
                #     return redirect('AdminAccount:login') 

                # 모든 정보를 세션에 저장
                request.session['u_seq'] = user.pk
                request.session['u_id'] = user.username
                request.session['u_name'] = f"{user.first_name}{user.last_name}"
                request.session['u_email'] = user.email
                request.session['u_is_staff'] = user.is_staff
                request.session['u_is_superuser'] = user.is_superuser
                request.session['date_joined'] = user.date_joined.strftime('%Y-%m-%d')

                

                # 로그인 성공 후 이동할 페이지 (예: 대시보드 메인)
                # URL 설정에 따라 'AdminAccount:login' 등으로 변경하세요.
                return redirect('Index:index_url') 
            
            else:
                # 인증 실패: 아이디나 비밀번호가 틀린 경우
                messages.error(request, "아이디 또는 비밀번호가 일치하지 않습니다.")
                return render(request, 'AdminAccount/login_form.html', {'TITLE': 'Login'})

        except Exception as e:
            print(f"Error: {e}")
            err_msg = traceback.format_exc()
            print(err_msg)
            # 심각한 에러 발생 시
            messages.error(request, "로그인 처리 중 서버 오류가 발생했습니다.")
            return render(request, 'AdminAccount/login_form.html', {'TITLE': 'Login Error'})

    # 2. GET 요청일 때 (처음 접속했을 때)
    else:
        # 이미 로그인된 사용자가 로그인 페이지에 접근하면 대시보드로 튕겨냄
        if request.user.is_authenticated:
            return redirect('/')
            
        rstData = {
            'TITLE': 'LandMania Admin Login',
        }
        return render(request, 'AdminAccount/login_form.html', rstData)



# 로그아웃 함수도 함께 준비하세요
def doLogout(request):
            
    logout(request)
    messages.info(request, "로그아웃 되었습니다.")
    return redirect('AdminAccount:login_form')