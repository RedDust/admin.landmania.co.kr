import sys
import os
from django.urls import path, re_path, include
from www.Controllers.GuestCenter.Board import open_board

app_name = 'Board'  # namespace 설정

urlpatterns = [

    path('guest_board_list', open_board.BoardList, name="GuestBoardList"),
    path('guest_qna_detail/<int:seq>/', open_board.BoardDetail, name="GuestBoardDetail"),

    path('guest_qna_answer_save/', open_board.SaveAnswer, name="GuestBoardAnswerSave"),
    path('guest_qna_delete/<int:seq>/', open_board.DeleteBoard, name="GuestDeleteBoard"),

    
]
