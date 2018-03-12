from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic import View
from django_redis import get_redis_connection
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner


# Create your views here.

# http://127.0.0.1:8000
# /
# def index(request):
#     """首页"""
    # if request.session.get('is_login'):
    #     username = request.session['is_login']
    #     print(username)
    #     del request.session['is_login']
    #     content = {'username': username}
    #     return render(request, 'index.html', content)

    #  if 'is_login' in request.COOKIES:
    #     username = request.COOKIES['is_login']
    #     print(username)
    #     content = {'username': username}
    #     response = render(request, 'index.html', content)
    #     response.delete_cookie('is_login')
    #     return response

    # username = 0
    # print('**********')
    # return render(request, 'index.html', {'username': username})
    # return render(request, 'index.html')


# http://127.0.0.1:8000
# /
class IndexView(View):
    """首页"""
    def get(self, request):
        """显示"""
        # 获取商品的分类信息
        types = GoodsType.objects.all()

        # 获取首页的轮播商品的信息
        index_banner = IndexGoodsBanner.objects.all().order_by('index')

        # 获取首页的促销活动的信息
        promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

        # 获取首页分类商品的展示信息
        for category in types:
            # 获取type种类在首页展示的图片商品的信息和文字商品的信息
            image_banner = IndexTypeGoodsBanner.objects.filter(category=category, display_type=1)
            title_banner = IndexTypeGoodsBanner.objects.filter(category=category, display_type=0)

            # 给category对象增加属性title_banner,image_banner
            # 分别保存category种类在首页展示的文字商品和图片商品的信息
            category.title_banner = title_banner
            category.image_banner = image_banner

        # 判断用户用户是否已登录
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')

            print(request.user.id)
            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key)-> 返回属性的数目
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {
            'types': types,
            'index_banner': index_banner,
            'promotion_banner': promotion_banner,
            'cart_count': cart_count,
        }

        # 使用模板
        return render(request, 'index.html', context)
