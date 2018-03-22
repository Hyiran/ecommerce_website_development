from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.cache import cache
from django.core.urlresolvers import reverse

from django.views.generic import View
from django_redis import get_redis_connection
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner, GoodsSKU
from apps.order.models import OrderGoods


# Create your views here.


# http://127.0.0.1:8000
# /
class IndexView(View):
    """首页"""

    def get(self, request):
        """显示"""
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')  # None pickle

        if context is None:
            # 获取商品的分类信息
            print('设置首页缓存')
            types = GoodsType.objects.all()

            # 获取首页的轮播商品的信息
            index_banner = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页的促销活动的信息
            promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品的展示信息
            for category in types:
                # 获取type种类在首页展示的图片商品的信息和文字商品的信息
                # QuerySet
                image_banner = IndexTypeGoodsBanner.objects.filter(category=category, display_type=1)
                title_banner = IndexTypeGoodsBanner.objects.filter(category=category, display_type=0)

                # 给type对象增加属性title_banner,image_banner
                # 分别保存type种类在首页展示的文字商品和图片商品的信息
                category.title_banner = title_banner
                category.image_banner = image_banner

            # 缓存数据
            context = {
                'types': types,
                'index_banner': index_banner,
                'promotion_banner': promotion_banner,
                'cart_count': 0
            }

            # 设置首页缓存
            # from django.core.cache import cache
            # cache.set('缓存名称', '缓存数据', '缓存有效时间'} pickle
            cache.set('index_page_data', context, 3600)

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
        context.update(cart_count=cart_count)

        # 使用模板
        return render(request, 'index.html', context)  # HttpResponse


# 前端向后端传递数据的三种方式:
# 1) get传参。
# 2) post传参。
# 3）url捕获参数。
#
# 前端传递的参数：商品id(sku_id)
# 商品详情页url地址: '/goods/商品id'

#  /goods/商品id
class DetailView(View):
    def get(self, request, sku_id):
        """显示"""
        # 获取商品的详情信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在，则直接跳回首页
            return redirect(reverse('goods:index'))
        # 获取商品分类信息
        types = GoodsType.objects.all()
        # 获取商品的评论信息
        order_skus = OrderGoods.objects.filter(sku=sku).exclude(comment='').order_by('-update_time')
        # 获取同一SPU的其他规格商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)
        # 获取同种类的新品信息
        new_skus = GoodsSKU.objects.filter(category=sku.category).order_by('-create_time')[:2]
        # 若用户登录，获取购物车中商品的条目数
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key)-> 返回属性的数目
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            # 拼接key
            history_key = 'history_%d' % request.user.id

            # 先尝试从redis对应列表中移除sku_id
            # lrem(key, count, value) 如果存在就移除，如果不存在什么都不做
            # count = 0 移除所有值为 value 的元素。
            conn.lrem(history_key, 0, sku_id)

            # 把sku_id添加到redis对应列表左侧
            # lpush(key, *args)
            conn.lpush(history_key, sku_id)

            # 只保存用户最新浏览的5个商品的id
            # ltrim(key, start, stop)
            conn.ltrim(history_key, 0, 4)

        # 组织模板上下文
        context = {
            'sku': sku,
            'types': types,
            'order_skus': order_skus,
            'same_spu_skus': same_spu_skus,
            'new_skus': new_skus,
            'cart_count': cart_count
        }
        # 使用模板
        return render(request, 'detail.html', context)



# 前端传递的参数：种类id(type_id) 页码(page) 排序方式(sort)
# 商品列表页的url地址: '/list/种类id/页码?sort=排序方式'

class ListView(View):
    def get(self, request, type_id, page):
        """type_id 为种类id， page为页码"""
        # 获取种类id对应的商品种类信息,判断是否合法存在
        try:
            category = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类不存在时，直接跳转首页
            return redirect(reverse('goods:index'))
        # 获取所有种类
        types = GoodsType.objects.all()

        # 获取排序顺序
        # sort=price: 按照商品的价格(price)从低到高排序
        # sort=hot: 按照商品的人气(sales)从高到低排序
        # sort=default: 按照默认排序方式(id)从高到低排序
        sort = request.GET.get('sort')

        # 获取type种类的商品信息并排序
        if sort == 'price':
            skus = GoodsSKU.objects.filter(category=category).order_by('price')
        elif sort == 'hot':
            skus = GoodsSKU.objects.filter(category=category).order_by('-sales')
        else:
            # 按照默认顺序来排序
            sort = 'default'
            skus = GoodsSKU.objects.filter(category=category).order_by('-id')

        # 分页操作
        from django.core.paginator import Paginator
        paginator = Paginator(skus, 5)

        # 处理页码
        page = int(page)

        if page > paginator.num_pages:
            # 默认获取第1页的内容
            page = 1

        # 获取第page页内容, 返回Page类的实例对象
        skus_page = paginator.page(page)

        # 页码处理
        # 如果分页之后页码超过5页，最多在页面上只显示5个页码：当前页前2页，当前页，当前页后2页
        # 1) 分页页码小于5页，显示全部页码
        # 2）当前页属于1-3页，显示1-5页
        # 3) 当前页属于后3页，显示后5页
        # 4) 其他请求，显示当前页前2页，当前页，当前页后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            # 1-num_pages
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            # num_pages-4, num_pages
            pages = range(num_pages - 4, num_pages + 1)
        else:
            # page-2, page+2
            pages = range(page - 2, page + 3)

        # 获取type种类的2个新品信息
        new_skus = GoodsSKU.objects.filter(category=category).order_by('-create_time')[:2]

        # 如果用户登录，获取用户购物车中商品的条目数
        cart_count = 0
        if request.user.is_authenticated():
            # 获取redis链接
            conn = get_redis_connection('default')

            # 拼接key
            cart_key = 'cart_%s' % request.user.id

            # 获取用户购物车中商品的条目数
            # hlen(key)-> 返回属性的数目
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文数据
        context = {
            'type': category,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
            'pages': pages
        }

        # 使用模板
        return render(request, 'list.html', context)



