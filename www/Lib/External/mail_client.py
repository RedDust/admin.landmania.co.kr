import os
import sys
import traceback
import base64

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from cryptography.fernet import Fernet
from django.conf import settings
from Lib.Crypto import two_way_encryption as encrypt_function
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime


# 1. 권한 범위 (메일 발송만 가능하도록 설정)
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_service():
    creds = None
    # 이전에 인증받은 토큰이 있다면 가져옴
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 인증 토큰이 없거나 만료된 경우 새로 인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Google Cloud에서 다운로드한 credentials.json 파일이 있어야 합니다.
            credential_path = os.path.join(settings.BASE_DIR, 'credentials.json')

            flow = InstalledAppFlow.from_client_secrets_file(credential_path, SCOPES)

            # 서버 환경인 경우 로컬 서버를 띄워 인증 (브라우저가 열려야 함)
            # creds = flow.run_local_server(port=0)
            creds = flow.run_local_server(port=0, open_browser=False)
        # 다음 실행을 위해 토큰 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


#인증 메일 발송
def ajx_send_auth(mailTo,strAuthCode):

    service = get_service()
    

    # 메일 내용 구성
    message = EmailMessage()
    message['To'] = f"{mailTo}".strip()
    message['From'] = 'landmania@landmania.co.kr' # 인증된 본인 계정 주소로 자동 지정됨
    message['Subject'] = f'[랜드매니아] 회원가입을 위한 인증번호({strAuthCode}) 안내'

    #2. 일반 텍스트 버전 (HTML 미지원 환경 대비)
    text_content = f"""
    안녕하세요. 대한민국 최고의 부동산 경매 데이터 허브, 랜드매니아입니다.
    
    요청하신 인증번호는 [{strAuthCode}] 입니다.
    해당 번호를 인증 창에 입력하여 회원가입을 완료해 주세요.
    인증번호는 발송 후 3분간 유효합니다.
    
    본인이 요청하지 않은 경우 이 메일을 무시해 주세요.
    감사합니다.
    """
    message.set_content(text_content)

    # 3. HTML 버전 (고급 디자인 적용)
    html_content = f"""
    <div style="max-width: 500px; margin: 0 auto; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; border: 1px solid #eef0f2; border-radius: 12px; overflow: hidden;">
        <div style="background-color: #2487ce; padding: 25px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -1px;">LandMania</h1>
        </div>
        
        <div style="padding: 40px 25px; background-color: #ffffff; text-align: center;">
            <h2 style="color: #333; font-size: 18px; margin-bottom: 15px; font-weight: 700;">이메일 인증을 진행해 주세요</h2>
            <p style="color: #666; font-size: 14px; line-height: 1.6; margin-bottom: 30px;">
                안녕하세요. 랜드매니아에 방문해 주셔서 감사합니다.<br>
                회원가입 완료를 위해 아래 인증번호를 입력창에 입력해 주세요.
            </p>
            
            <div style="background-color: #f4f7f9; padding: 25px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 30px;">
                <span style="font-size: 32px; font-weight: 800; color: #2487ce; letter-spacing: 5px;">{strAuthCode}</span>
            </div>
            
            <p style="color: #999; font-size: 12px; line-height: 1.5;">
                * 인증번호는 발송 후 <strong>3분간</strong> 유효합니다.<br>
                * 본인이 요청한 것이 아니라면 고객센터로 문의해 주세요.
            </p>
        </div>
        
        <div style="padding: 20px; background-color: #f8f9fa; text-align: center; font-size: 11px; color: #aaa; border-top: 1px solid #eee;">
            <p style="margin: 0;">본 메일은 발신전용입니다. 관련 문의는 고객센터를 이용해 주세요.</p>
            <p style="margin: 5px 0 0 0;">© 2026 LandMania. All Rights Reserved.</p>
        </div>
    </div>
    """
    message.add_alternative(html_content, subtype='html')

    # 4. API 전송을 위한 Base64 인코딩
    try:
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}

        send_result = service.users().messages().send(userId="me", body=create_message).execute()
        return JsonResponse({'result': 'success', 'message_id': send_result['id']})

    except Exception as error:
        return JsonResponse({'result': 'error', 'details': str(error)}, status=500)



#가입 완료 메일 발송
def send_welcome_email(user_email, nickname):
    """
    회원가입 완료 축하 이메일을 발송합니다 (Gmail API 사용)
    """
    service = get_service()
    if not service:
        return False

    # 1. 메일 객체 생성
    message = EmailMessage()
    message['Subject'] = f'[랜드매니아] {nickname}님, 회원가입을 진심으로 축하드립니다!'
    message['From'] = 'landmania@landmania.co.kr' # 인증된 본인 계정 주소로 자동 지정됨
    message['To'] = f"{user_email}".strip()

    # 현재 시간 및 기본 정보 설정
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    user_grade = "일반회원" # 가입 시 기본 등급

    # 2. 텍스트 버전 내용 (변수 치환)
    text_content = f"""
    안녕하세요, {nickname}님!
    랜드매니아(LandMania)의 회원이 되신 것을 진심으로 환영합니다.

    [가입 정보 확인]
    - 닉네임: {nickname}
    - 아이디: {user_email}
    - 가입일시: {current_date}
    - 회원등급: {user_grade}

    지금 바로 랜드매니아에 접속하여 전국 법원 경매 및 공매 실시간 정보를 확인해 보세요.
    서비스 바로가기: https://www.landmania.co.kr/

    감사합니다.
    랜드매니아 팀 드림
    """
    message.set_content(text_content)

    # 3. HTML 버전 (Information Table 포함)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background-color: #f4f7f9;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
            <tr>
                <td align="center" style="padding: 40px 0; background-color: #2487ce;">
                    <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800; letter-spacing: -1px;">LandMania</h1>
                </td>
            </tr>
            
            <tr>
                <td style="padding: 40px 35px;">
                    <h2 style="margin: 0 0 20px 0; color: #333; font-size: 22px; font-weight: 700; text-align: center;">Welcome! 가입을 축하드립니다.</h2>
                    <p style="margin: 0 0 30px 0; color: #666; font-size: 15px; line-height: 1.7; text-align: center;">
                        <strong>{nickname}</strong>님, 대한민국 최고의 부동산 경매 허브<br>
                        랜드매니아의 가족이 되신 것을 진심으로 환영합니다.
                    </p>
                    
                    <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 12px; padding: 25px; margin-bottom: 35px;">
                        <h4 style="margin: 0 0 15px 0; color: #2487ce; font-size: 14px; border-bottom: 1px solid #eef0f2; padding-bottom: 10px;">[ 나의 가입 정보 ]</h4>
                        <table width="100%" style="font-size: 14px; color: #555; border-collapse: collapse;">
                            <tr>
                                <td width="100" style="padding: 8px 0; font-weight: bold; color: #333;">닉네임</td>
                                <td style="padding: 8px 0;">{nickname}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #333;">아이디(ID)</td>
                                <td style="padding: 8px 0;">{user_email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #333;">가입일시</td>
                                <td style="padding: 8px 0;">{current_date}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #333;">회원등급</td>
                                <td style="padding: 8px 0;"><span style="color: #2487ce; font-weight: 600;">{user_grade}</span></td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://www.landmania.co.kr/" style="display: inline-block; padding: 16px 50px; background-color: #2487ce; color: #ffffff; text-decoration: none; border-radius: 50px; font-weight: 700; font-size: 16px; box-shadow: 0 4px 12px rgba(36, 135, 206, 0.3);">랜드매니아 시작하기</a>
                    </div>
                </td>
            </tr>
            
            <tr>
                <td style="padding: 30px; background-color: #fcfcfc; border-top: 1px solid #f1f1f1; text-align: center; font-size: 12px; color: #aaa;">
                    <p style="margin: 0 0 8px 0;">본 메일은 발신 전용으로 회신되지 않습니다.</p>
                    <p style="margin: 0;">© 2026 LandMania. All Rights Reserved.</p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    message.add_alternative(html_content, subtype='html')

    # 4. Gmail API 전송 형식으로 인코딩
    try:
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        
        # 실제 발송 실행
        service.users().messages().send(userId="me", body=create_message).execute()
        return True
    except Exception as e:
        print(f"Welcome Email 발송 오류: {e}")
        return False
    



def ajx_send_password_reset(user_email, reset_url):
    """
    비밀번호 재설정 링크를 이메일로 발송합니다 (Gmail API 사용)
    """
    service = get_service()
    if not service:
        return False

    # 1. 메일 객체 생성
    message = EmailMessage()
    message['Subject'] = '[랜드매니아] 비밀번호 재설정 안내입니다.'
    message['From'] = 'landmania@landmania.co.kr'
    message['To'] = f"{user_email}".strip()

    # 현재 시간 (안내 문구용)
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 2. 텍스트 버전 내용 (HTML 미지원 클라이언트 대비)
    text_content = f"""
안녕하세요, 랜드매니아입니다.

비밀번호 재설정을 위한 요청이 접수되었습니다.
아래 링크를 클릭하여 새로운 비밀번호를 설정해 주세요.

비밀번호 재설정 링크:
{reset_url}

※ 본 링크는 보안을 위해 한 번만 사용 가능하며, 일정 시간이 지나면 만료됩니다.
본인이 요청하지 않은 경우 이 메일을 무시하셔도 됩니다.

감사합니다.
랜드매니아 드림
    """
    message.set_content(text_content)

    # 3. HTML 버전 (깔끔한 디자인 패키징)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background-color: #f4f7f9;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #007bff; padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">비밀번호 재설정 안내</h1>
            </div>
            
            <div style="padding: 40px 30px; line-height: 1.6; color: #333333;">
                <p style="font-size: 16px; margin-bottom: 20px;">
                    안녕하세요, <strong>랜드매니아</strong>입니다.<br>
                    회원님의 계정에 대한 비밀번호 재설정 요청이 접수되어 안내해 드립니다.
                </p>
                
                <p style="font-size: 15px; color: #666666; margin-bottom: 30px;">
                    아래의 <strong>'비밀번호 재설정하기'</strong> 버튼을 클릭하여 새로운 비밀번호를 설정하실 수 있습니다.
                </p>

                <div style="text-align: center; margin: 40px 0;">
                    <a href="{reset_url}" style="background-color: #007bff; color: #ffffff; padding: 15px 35px; text-decoration: none; font-weight: bold; border-radius: 5px; font-size: 16px; display: inline-block;">비밀번호 재설정하기</a>
                </div>

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; font-size: 13px; color: #777777;">
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>보안을 위해 이 링크는 <strong>단 한 번만</strong> 사용 가능합니다.</li>
                        <li>본인이 요청하지 않은 경우, 누군가 이메일 주소를 잘못 입력했을 수 있으니 이 메일을 무시해 주세요.</li>
                        <li>비밀번호는 타인에게 노출되지 않도록 주의해 주시기 바랍니다.</li>
                    </ul>
                </div>
            </div>

            <div style="background-color: #eeeeee; padding: 20px; text-align: center; font-size: 12px; color: #999999;">
                <p style="margin: 5px 0;">본 메일은 발신 전용입니다. 문의사항은 고객센터를 이용해 주세요.</p>
                <p style="margin: 5px 0;">© LandMania. All rights reserved.</p>
                <p style="margin: 5px 0;">발송 시각: {current_time}</p>
            </div>
        </div>
    </body>
    </html>
    """
    message.add_alternative(html_content, subtype='html')

    # 4. Gmail API 전송 실행
    try:
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        service.users().messages().send(userId="me", body=create_message).execute()
        return True
    except Exception as e:
        print(f"Password Reset Email 발송 오류: {e}")
        return False    