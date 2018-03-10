from django.conf.urls import url
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, User_center_infoView, User_center_siteView

urlpatterns = [
    url(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', LoginView.as_view(), name='login'),  # 登录
    url(r'^logout$', LogoutView.as_view(), name='logout'),  # 退出
    url(r'^user_center_info$', User_center_infoView.as_view(), name='user_center_info'),  # 用户中心
    url(r'^user_center_site$', User_center_siteView.as_view(), name='user_center_site'),  # 收货地址
]
