import os
import requests
import json
import traceback

from django.db import connection, transaction
from www.Apps.lm_table_names import TableNames
from www.Lib.Crypto.encryption import security

#1건만 보내는 알리고 모듈
def _ApiAligoSingleSMS(dictSendInfo):

    dictResult = dict()
    dictResult['api_company'] = 'a'
    dictResult['sms_type'] = 'a'
    

    try:

        send_url = 'https://apis.aligo.in/send/'  # 요청을 던지는 URL, 현재는 문자보내기

        sms_data = {'key': os.getenv('ALIGP_SMS_KEY'),  # api key
                    'userid': 'landmania',  # 알리고 사이트 아이디
                    'sender': dictSendInfo['send_number'],  # 발신번호
                    'receiver': dictSendInfo['recv_number'],  # 수신번호 (,활용하여 1000명까지 추가 가능)
                    'msg': dictSendInfo['send_msg'],  # 문자 내용
                    'msg_type': 'SMS',  # 메세지 타입 (SMS, LMS)
                    'title': dictSendInfo['send_title'],  # 메세지 제목 (장문에 적용)
                    'destination': dictSendInfo['destination'],  # %고객명% 치환용 입력
                    # 'rdate' : '예약날짜',
                    # 'rtime' : '예약시간',
                    # 'testmode_yn' : '' #테스트모드 적용 여부 Y/N
                    }
        response = requests.post(send_url, data=sms_data)
        send_response = response.json()

        print("send_response ==> " , send_response)
        print("send_response type ==> " , type(send_response))

        # 수정 후: 문자열을 정수(int)로 바꿔서 비교
        result_code = dictResult.get('result_code', '0') # 값이 없을 경우 '0' 기본값

        if int(result_code) < 1:
            raise Exception(f"SMS 전송 실패: {dictResult.get('message')}")

        #{'result_code': '1', 'message': 'success', 'msg_id': '1270225107', 'success_cnt': 1, 'error_cnt': 0, 'msg_type': 'SMS'}
        
        if send_response.get('success_cnt') > 0:
            dictResult['result'] = True
        else:
            dictResult['result'] = False

        dictResult['msg_id'] = send_response.get('msg_id')
        dictResult['msg_type'] = send_response.get('msg_type')
        dictResult['message'] = dictSendInfo['send_msg']
        return dictResult

    except Exception as e:
        print("_ApiAligoSingleSMS Error Exception")
        print(e)
        print(type(e))
        err_msg = traceback.format_exc()
        print(err_msg)

        dictResult['result'] = False
        dictResult['msg_id'] = '0'
        dictResult['msg_type'] = 'SMS'
        dictResult['message'] = dictSendInfo['send_msg']

        return dictResult




def CommonSMSFilter(dictSendInfo):

    print("dictSendInfo => " , type(dictSendInfo) , dictSendInfo)



def SendSMSDrive(dictSendInfo):
    
    print(f"--- [SMS 발송 시뮬레이션] ---")
    print("dictSendInfo => " , type(dictSendInfo) , dictSendInfo)

    dictSendInfo['send_number'] = '01075910221'
    user_seq = dictSendInfo.get('user_seq')
    recv_number = dictSendInfo.get('recv_number')
    user_ip = dictSendInfo.get('user_ip')
    send_msg = dictSendInfo.get('send_msg')


    # 2. 검색용 phone 해시 생성 (중복 확인 및 인덱스용)
    phone_hash = security.make_search_hash(recv_number)
    d_phone = security.encrypt(recv_number)

    # 2. 검색용 phone 해시 생성 (중복 확인 및 인덱스용)
    hash_ip = security.make_search_hash(user_ip)
    enc_ip = security.encrypt(user_ip)


    if not isinstance(dictSendInfo, dict):
        raise Exception("dictSendInfo is not dict")

    dictSendInfo['destination'] = '01029117586|랜드매니아'
    dictSendInfo['send_number'] = '01075910221'

    try:
        
        #SMS 발송
        dictResult = _ApiAligoSingleSMS(dictSendInfo)

        print("dictResult : " , type(dictResult) , dictResult)

        if not isinstance(dictResult, dict):
            raise Exception('Send SMS Failure: Result is not a dictionary')

        result = dictResult.get('result','f')
        api_company = dictResult.get('api_company')
        api_id = dictResult.get('api_id' , '0')
        sms_type = dictResult.get('sms_type','s')

        with connection.cursor() as cursor:

            sqlInsertSmsRecord = f""" 
                                    INSERT INTO {TableNames.SMS_Record} SET 
                                    user_seq = %s ,
                                    d_phone = %s ,
                                    hash_phone = %s ,
                                    enc_ip = %s ,
                                    hash_ip = %s ,
                                    message = %s ,
                                    api_company = %s ,
                                    api_id = %s ,
                                    sms_type = %s ,
                                    result = %s 
                                """

            cursor.execute(sqlInsertSmsRecord, [
                                user_seq,
                                d_phone,
                                phone_hash,
                                enc_ip,
                                hash_ip,
                                send_msg,
                                api_company,
                                api_id,
                                sms_type,
                                result
                                                ])

        print("sqlInsertSmsRecord" , sqlInsertSmsRecord)
        return True
    
    except Exception as e:
        print("SendSMSDrive Error Exception")
        print(e)
        print(type(e))

        err_msg = traceback.format_exc()
        print(err_msg)

        return False