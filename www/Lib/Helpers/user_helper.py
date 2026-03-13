
from www.Apps.lm_table_names import TableNames

def _log_user_access(cursor, user_seq,enc_ip, hash_ip, agent, provider, status="SUCCESS", reason=None):
        
    sql = f"INSERT INTO {TableNames.LoginLogs} (user_seq, enc_ip, hash_ip, user_agent, provider, status, fail_reason) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, [user_seq, enc_ip, hash_ip, agent, provider, status, reason])


def set_user_session(request, user_data):
    """
    사용자 정보를 세션에 저장하는 공통 함수.
    필수 데이터가 하나라도 누락되면 ValueError를 발생시킵니다.
    """
    # 1. 필수 키 리스트 정의
    required_keys = [
        'user_seq', 'user_email', 'provider', 'user_nickname', 
        'level', 'point'
    ]
    
    # 2. 누락된 키 확인 (List Comprehension 활용)
    missing_keys = [key for key in required_keys if key not in user_data or user_data.get(key) is None]
    
    if missing_keys:
        # 어떤 키가 빠졌는지 에러 메시지에 포함
        raise ValueError(f"세션 생성 실패: 필수 데이터 누락 ({', '.join(missing_keys)})")

    # 3. 모든 데이터가 있을 때만 세션 저장
    request.session['user_seq'] = user_data['user_seq']
    request.session['user_email'] = user_data['user_email']
    request.session['provider'] = user_data['provider']
    request.session['user_nickname'] = user_data['user_nickname']
    request.session['last_login'] = user_data.get('last_login')
    request.session['level'] = user_data['level']
    request.session['point'] = user_data['point']
    request.session['status'] = user_data['status']
    request.session['profile_image'] = user_data.get('profile_image') if user_data.get('profile_image') else '/static/images/Mypage/avatar.png'

