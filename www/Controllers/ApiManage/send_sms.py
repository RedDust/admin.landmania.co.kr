from django.db import connection
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from www.Lib.Crypto.encryption import security # 확정된 복호화 경로

def dictfetchall(cursor):
    if cursor.description is None: return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def send_sms_list(request):
    # 1. 필터 및 페이징 파라미터
    result_filter = request.GET.get('result', '') # 's': 성공, 'f': 실패
    page = request.GET.get('page', 1)
    limit = 20
    offset = (int(page) - 1) * limit

    # 2. 동적 WHERE 절
    where_clause = "WHERE 1=1"
    params = []

    if result_filter:
        where_clause += " AND r.result = %s"
        params.append(result_filter)

    with connection.cursor() as cursor:
        # 전체 개수 조회
        count_query = f"SELECT COUNT(*) FROM lm_send_sms_record r {where_clause}"
        cursor.execute(count_query, params)
        total_count = (cursor.fetchone() or (0,))[0]

        # 리스트 조회 (사용자 닉네임 JOIN)
        query = f"""
            SELECT 
                r.*, 
                u.nickname as user_nickname
            FROM lm_send_sms_record r
            LEFT JOIN lm_users u ON r.user_seq = u.seq
            {where_clause}
            ORDER BY r.seq DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [limit, offset])
        records = dictfetchall(cursor)

    # 3. 데이터 후처리 (복호화 및 코드 변환)
    for row in records:
        # security.decrypt 적용
        row['dec_phone'] = security.decrypt(row['d_phone']) if row['d_phone'] else ""
        row['dec_ip'] = security.decrypt(row['enc_ip']) if row['enc_ip'] else ""
        
        # 업체명 변환
        row['company_nm'] = '알리고' if row['api_company'] == 'a' else '기타'
        # 발송 타입 변환
        row['type_nm'] = '휴대폰 인증' if row['sms_type'] == 'a' else '기타'

    # 4. 페이징 처리
    paginator = Paginator(range(total_count), limit)
    try:
        page_obj = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    context = {
        'records': records,
        'page_obj': page_obj,
        'total_count': total_count,
        'result_filter': result_filter,
    }
    return render(request, 'ApiManage/sms_list.html', context)