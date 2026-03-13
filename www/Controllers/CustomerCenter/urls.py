import sys
import os
from django.urls import path, re_path, include
from www.Controllers.CustomerCenter import qna

app_name = 'CustomerCenter'  # namespace 설정

urlpatterns = [

    path('qna_list', qna.list, name='qna_list' ),
    path('qna_detail/<int:seq>/', qna.detail, name='qna_detail'),
    
]
