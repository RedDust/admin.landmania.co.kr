from django.http import HttpResponseForbidden

class IPMiddleware:
    # 접근을 허용할 IP 리스트
    ALLOWED_IPS = ['127.0.0.1', '222.109.253.24'] 

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 클라이언트의 IP 주소 가져오기
        ip = request.META.get('REMOTE_ADDR')
        
        # 프록시(Nginx 등)를 사용하는 경우 실제 IP 확인
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]


        print("ip => " , ip)

        if ip not in self.ALLOWED_IPS:
            return HttpResponseForbidden("접근 권한이 없습니다.")

        return self.get_response(request)