import sys
import os
from django.urls import path, re_path, include
from www.Controllers.Index import index

app_name = 'Index'  # namespace 설정

urlpatterns = [

    path('', index.index, name='index_url' ),
    # path('_xhr_contect_submit', index._xhr_contect_submit, name="_xhr_contect_submit"),
    # path('_test', index.test, name="main_test"),
    # re_path(r"^admin/", include('index.urls'), name='index_url'),
    # re_path(r"^admin/", include('intro.Controllers.admin.urls'), name='admin_url'),

]
