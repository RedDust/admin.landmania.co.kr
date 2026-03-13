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

def index(request):

    try:
        
        rstData = {
            'TITLE' : 'Home',
        }

        if request.user.is_authenticated:
            # 로그인 된 사용자는 대시보드로 이동
            return render(request, 'Index/dashboard.html') # 아까 만든 대시보드 파일명
        else:
            # 비로그인 사용자는 랜딩 페이지로 이동
            # return render(request, 'admin_base.html') # 아까 만든 대시보드 파일명
            return render(request, 'Index/index.html')

        # return HttpResponse('ddd')
        return render(request, 'Index/dashboard.html' ,rstData)
        # return render(request, 'Temp/index.html' ,rstData)
        # return render(request, 'index.html' ,rstData)

    except Exception as e:
        print(e)
        print(type(e))
        err_msg = str(traceback.format_exc())
        print(err_msg)
        return JsonResponse({'result': 'FAILURE'})
    