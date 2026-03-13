
import os
import requests
import json
import traceback

from django.db import connection, transaction
from www.Apps.lm_table_names import TableNames
from www.Lib.Crypto.encryption import security

def revoke_naver_token(cursor,user_seq):
    try:

        # 2. 연동 테이블 조회
        sql_check = f"""
            SELECT provider_token FROM {TableNames.SocialAccounts} 
            WHERE user_seq = %s FOR UPDATE
        """
        cursor.execute(sql_check, [user_seq])
        # [설정 반영] 컬럼 정보 추출 (필요 시 로그용으로 활용)
        log_columns = [col[0] for col in (cursor.description or [])]

        # fetchall()을 통해 전체 개수를 확인합니다.
        rows = cursor.fetchall()
        row_count = len(rows)

        # row count가 1 이하(0 또는 1)인 경우 예외 처리
        if row_count < 1:
            raise Exception(f"처리 가능한 연동 정보가 부족합니다. (조회된 행 수: {row_count})")

        # 2개 이상일 때 첫 번째 데이터를 가져옵니다. 
        # rows[0]은 (provider_token,) 형태의 튜플이므로 첫 번째 요소를 추출합니다.
        access_token = rows[0][0]
        
        print("access_token ==> " , access_token)

        """
        네이버 접근 토큰을 폐기(연동 해제)합니다.
        """
        client_id = os.getenv('NAVER_LOGIN_API_CLIENT_ID')
        client_secret = os.getenv('NAVER_LOGIN_API_CLIENT_SECRET')

        # 네이버 토큰 폐기 API URL 구성
        # URL 파라미터로 필수 정보들을 전달합니다.
        revoke_url = "https://nid.naver.com/oauth2.0/token"
        params = {
            'grant_type': 'delete',
            'client_id': client_id,
            'client_secret': client_secret,
            'access_token': access_token,
            'service_provider': 'NAVER'
        }

        # GET 방식으로 요청을 보냅니다.
        response = requests.get(revoke_url, params=params)
        res_data = response.json()

        # 결과 확인 (성공 시 result: "success")
        if res_data.get('result') == 'success':
            print(f"네이버 연동 해제 성공: {res_data}")
            return True
        else:
            print(f"네이버 연동 해제 실패: {res_data.get('error_description')}")
            return False

    except Exception as e:
        print(f"Error: {e}") # 디버깅용
        err_msg = traceback.format_exc()
        print(err_msg)        
        print(f"네이버 API 통신 에러: {e}")
        return False