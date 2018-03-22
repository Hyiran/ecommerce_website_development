from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse

from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

from apps.goods.models import GoodsSKU


from django.views.generic import detail

# Create your views here.


# 前端传递的参数: 商品id(sku_id) 商品数量(count)
# ajax post 请求
# /cart/add
class CartAddView(View):
    """购物车记录添加"""

    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 获取参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')  # 数字

        # 参数校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验商品id requests urllib
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品信息错误'})

        # 校验商品数量count
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 3, 'errmsg': '商品数量必须为有效数字'})

        # 业务处理: 购物车记录添加
        # 获取redis链接
        conn = get_redis_connection('default')
        # 拼接key
        cart_key = 'cart_%d' % user.id
        # cart_1 : {'1':'3', '2':'5'}
        # hget(key, field)
        cart_count = conn.hget(cart_key, sku_id)

        if cart_count:
            # 如果用户的购物车中已经添加过sku_id商品, 购物车中对应商品的数目需要进行累加
            count += int(cart_count)

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 设置用户购物车中sku_id商品的数量
        # hset(key, field, value)   存在就是修改，不存在就是新增
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车中商品的条目数
        cart_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'cart_count': cart_count, 'errmsg': '添加购物车记录成功'})


# 购物车页面显示
# get /cart/
class CartInfoView(LoginRequiredMixin, View):
    """购物车页面显示"""

    def get(self, request):
        # 获取登录用户
        user = request.user

        # 从redis中获取用户的购物车记录信息
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d' % user.id

        # cart_1 : {'1':'2', '3':'1', '5':'2'}
        # hgetall(key) -> 返回是一个字典，字典键是商品id, 键对应值是添加的数目
        cart_dict = conn.hgetall(cart_key)

        total_count = 0
        total_amount = 0
        # 遍历获取购物车中商品的详细信息
        skus = []
        for sku_id, count in cart_dict.items():
            # 根据sku_id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 计算商品的小计
            amount = sku.price * int(count)

            # 给sku对象增加属性amout和count, 分别保存用户购物车中商品的小计和数量
            sku.count = count
            sku.amount = amount

            # 追加商品的信息
            skus.append(sku)

            # 累加计算用户购物车中商品的总数目和总价格
            total_count += int(count)
            total_amount += amount

        # 组织模板上下文
        context = {
            'total_count': total_count,
            'total_amount': total_amount,
            'skus': skus
        }

        # 使用模板
        return render(request, 'cart.html', context)


# 购物车记录更新
# 前端传递的参数: 商品id(sku_id) 更新数量(count)
# ajax post请求
# /cart/update
class CartUpdateView(View):
    """购物车记录更新"""

    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 参数校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验商品id requests urllib
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品信息错误'})

        # 校验商品数量count
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 3, 'errmsg': '商品数量必须为有效数字'})

        # 业务处理: 购物车记录更新
        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d' % user.id

        # 校验商品的库存量
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新用户购物车中商品数量
        # hset(key, field, value)
        conn.hset(cart_key, sku_id, count)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '更新购物车记录成功'})


# 购物车记录删除
# 前端传递的参数: 商品id(sku_id)
# /cart/delete
# ajax post请求
class CartDeleteView(View):
    """购物车记录删除"""

    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 参数校验
        if not all([sku_id]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验商品id requests urllib
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品信息错误'})

        # 业务处理: 删除用户的购物车记录
        # 获取链接
        conn = get_redis_connection('default')

        # 拼接key
        cart_key = 'cart_%d' % user.id

        # 删除记录
        # hdel(key, *fields)
        conn.hdel(cart_key, sku_id)

        # 返回应答
        return JsonResponse({'res': 3, 'errmsg': '删除购物车记录成功'})
