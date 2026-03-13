
import os
import requests
import json
import traceback

from django.db import connection, transaction
from www.Apps.lm_table_names import TableNames
from www.Lib.Crypto.encryption import security

def revoke_kakao_token(cursor,user_seq):
    try:


        # 2. 연동 테이블 조회
        sql_check = f"""
            SELECT provider_uid FROM {TableNames.SocialAccounts} 
            WHERE user_seq = %s FOR UPDATE
        """
        cursor.execute(sql_check, [user_seq])
        # [설정 반영] 컬럼 정보 추출 (필요 시 로그용으로 활용)
        log_columns = [col[0] for col in (cursor.description or [])]

        # fetchall()을 통해 전체 개수를 확인합니다.
        rows = cursor.fetchall()
        row_count = len(rows)

        print("user_seq =>" , user_seq)
        print("rows =>" , rows)        

        # row count가 1 이하(0 또는 1)인 경우 예외 처리
        if row_count < 1:
            raise Exception(f"처리 가능한 연동 정보가 부족합니다. (조회된 행 수: {row_count})")

        # 2개 이상일 때 첫 번째 데이터를 가져옵니다. 
        # rows[0]은 (provider_token,) 형태의 튜플이므로 첫 번째 요소를 추출합니다.
        user_id = rows[0][0]
        print("accuser_idss_token ==> " , user_id)


        # 카카오 디벨로퍼스 > 내 애플리케이션 > 앱 설정 > 요약 정보에서 확인
        ADMIN_KEY = os.getenv('KAKAO_ADMIN_KEY')
        
        url = "https://kapi.kakao.com/v1/user/unlink"
        headers = {
            "Authorization": f"KakaoAK {ADMIN_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "target_id_type": "user_id",
            "target_id": user_id  # 가입 시 저장해둔 카카오 고유 ID (profile_json.get('id'))
        }

        response = requests.post(url, headers=headers, data=params)
        
        if response.status_code == 200:
            print(f"Successfully unlinked user: {response.json().get('id')}")
            return True
        else:
            print(f"Failed to unlink: {response.status_code}, {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}") # 디버깅용
        err_msg = traceback.format_exc()
        print(err_msg)        
        print(f"카카ㅇ API 통신 에러: {e}")
        return False