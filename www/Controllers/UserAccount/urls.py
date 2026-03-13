import sys
import os
from django.urls import path, re_path, include
from www.Controllers.UserAccount import user_list, login_log, user_modify

app_name = 'UserAccount'  # namespace 설정

urlpatterns = [

    path('user_list/', user_list.userList, name='user_list' ),
    path('login_log/', login_log.log_list, name='login_log'),
    path('logout/', user_list.userList, name='logout'),


    # 회원 관리 관련
    path('users/detail/<int:seq>/', user_modify.userDetail, name='userDetail'), # 회원 상세
    
    # 기능 처리 (POST 전용)
    path('users/update-point/', user_modify.updatePoint, name='updatePoint'), # 포인트 변경

    # 기능 처리 (POST 전용)
    path('users/update-state/', user_modify.updateState, name='updateState'), # 회원상태변경




    path('users/withdraw/form/<int:seq>/', user_modify.userWithdrawForm, name='userWithdrawForm'), # 탈퇴 폼
    path('users/withdraw/delete_user', user_modify.doWithdraw, name='doWithdraw'), # 탈퇴 처리

    
    # path('_xhr_contect_submit', index._xhr_contect_submit, name="_xhr_contect_submit"),


    # path('_test', index.test, name="main_test"),
    # re_path(r"^admin/", include('index.urls'), name='index_url'),
    # re_path(r"^admin/", include('intro.Controllers.admin.urls'), name='admin_url'),

]
