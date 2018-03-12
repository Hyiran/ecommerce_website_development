from django.conf.urls import url
from apps.goods.views import IndexView

urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),  # 首页
]
