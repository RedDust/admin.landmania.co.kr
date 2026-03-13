import sys
import os
from django.urls import path, re_path, include
from www.Controllers.CustomerCenter import qna

app_name = 'GuestCenter'  # namespace 설정

urlpatterns = [

    path('board/', include('www.Controllers.GuestCenter.Board.urls')),
    
]
