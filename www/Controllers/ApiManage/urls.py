import sys
import os
from django.urls import path, re_path, include
from www.Controllers.ApiManage import send_sms

app_name = 'ApiManage'  # namespace 설정

urlpatterns = [
    path('send_sms_list', send_sms.send_sms_list, name='send_sms_list' ),
]
