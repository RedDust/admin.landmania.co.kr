from django.conf import settings


print("settings" , type(settings) , settings)

virtual_hosts = {
    "admin.landmania.co.kr": "www.urls",
}



# print("settings.LandMania_DOMAIN" , type(settings.LandMania_DOMAIN) , settings.LandMania_DOMAIN)

# for setting in settings:
#     print("setting=> ", type(setting), setting)


class DomainMappingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        # temp_virtual_hosts = {
        #     settings.LandMania_DOMAIN: 'LandMania.urls',
        #     settings.StockFriends_DOMAIN: 'StockFriends.urls',
        # }



        host = request.get_host()
        request.urlconf = virtual_hosts.get(host)

        response = self.get_response(request)
        return response