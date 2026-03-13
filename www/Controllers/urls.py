import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from django.urls import path, re_path, include




urlpatterns = [

    path('admin_account/', include('www.Controllers.AdminAccount.urls')),
    path('user_account/', include('www.Controllers.UserAccount.urls')),
    path('customer_center/', include('www.Controllers.CustomerCenter.urls')),
    path('api_manage/', include('www.Controllers.ApiManage.urls')),
    path('guest_center/', include('www.Controllers.GuestCenter.urls')),

    path('', include('www.Controllers.Index.urls' )),
    path('/', include('www.Controllers.Index.urls')),

]