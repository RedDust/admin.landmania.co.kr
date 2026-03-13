import sys
import os
from django.urls import path, re_path, include
from www.Controllers.AdminAccount import login , admin_profile

app_name = 'AdminAccount'  # namespace 설정

urlpatterns = [


    path('login/', login.doLogin, name='doLogin'),
    path('logout/', login.doLogout, name='logout'),    
    path('profile_detail/', admin_profile.detail_from, name="adminDetailFrom"),

    path('update_admin_profile/', admin_profile.DoUpdateAdmin, name="DoUpdateAdmin"),

    path('update_admin_profile/', admin_profile.DoUpdateAdmin, name="resetAdminPassword"),



    path('', login.form, name='login_form' ),

    # path('_test', index.test, name="main_test"),
    # re_path(r"^admin/", include('index.urls'), name='index_url'),
    # re_path(r"^admin/", include('intro.Controllers.admin.urls'), name='admin_url'),

]
