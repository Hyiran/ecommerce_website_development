from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.core.urlresolvers import reverse


from apps.user.models import Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods


from django_redis import get_redis_connection
# Create your views here.


# 提交订单页面视图
# /order/place
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面"""
    def post(self, request):
        # 获取用户
        user = request.user

        # 获取提交时被选中的商品id
        sku_ids = request.POST.getlist('sku_ids')
        print('sku_ids: ',sku_ids)

        # 若没有商品，则直接跳回首页
        if len(sku_ids) == 0:
            return redirect(reverse('goods:index'))

        # 获取收货地址

        addrs = Address.objects.filter(user=user)

        # 拼接key
        cart_key = 'cart_%d' % user.id

        # 连接redis
        conn = get_redis_connection('default')
        # 遍历sku_ids获取用户所要购买的商品的信息
        skus = []
        total_count = 0
        total_amount = 0
        for sku_id in sku_ids:
            # 根据id查找商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)

            # 从redis中获取用户所要购买的商品的数量
            count = conn.hget(cart_key, sku_id)

            # 计算商品的小计
            amount = sku.price * int(count)

            # 给sku对象增加属性count和amount
            # 分别保存用户要购买的商品的数目和小计
            sku.count = count
            sku.amount = amount

            # 追加商品的信息
            skus.append(sku)

            # 累加计算用户要购买的商品的总件数和总金额
            total_count += int(count)
            total_amount += amount

        # 运费: 运费表: 100-200  假设为10
        transit_price = 10

        # 实付款
        total_pay = total_amount + transit_price

        # 组织模板上下文
        context = {
            'addrs': addrs,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'sku_ids': ','.join(sku_ids)
        }

        # 使用模板
        return render(request, 'place_order.html', context)

# 订单创建
# 采用ajax post请求
# /order/commit
# 前端传递的参数: 收货地址id(addr_id) 支付方式(pay_method) 用户所要购买的全部商品的id(sku_ids)
'''订单创建的流程
    1) 接收参数
    2）参数校验
    3) 组织订单信息
    4）todo: 向df_order_info中添加一条记录
    5）todo: 订单中包含几个商品需要向df_order_goods中添加几条记录
        5.1 将sku_ids分割成一个列表
        5.2 遍历sku_ids，向df_order_goods中添加记录
            5.2.1 根据id获取商品的信息
            5.2.2 从redis中获取用户要购买的商品的数量
            5.2.3 向df_order_goods中添加一条记录
            5.2.4 减少商品库存，增加销量
            5.2.5 累加计算订单中商品的总数目和总价格
    6) 更新订单信息中商品的总数目和总价格
    7）删除购物车中对应的记录
'''

# 订单事务
class OrderCommitView(View):

    """订单创建"""
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids') # 以,分隔的字符串 3,4

        # 参数校验
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})

        # 校验地址id
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 3, 'errmsg': '非法的支付方式'})

        # 组织订单信息
        # 组织订单id: 20180316115930+用户id
        from datetime import datetime
        order_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(user.id)

        # 运费
        transit_price = 10

        # 总数目和总价格
        total_count = 0
        total_price = 0

        # todo: 向df_order_info中添加一条记录
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            addr=addr,
            pay_method=pay_method,
            total_count=total_count,
            total_price=total_price,
            transit_price=transit_price
        )

        # todo: 订单中包含几个商品需要向df_order_goods中添加几条记录
        # 获取redis链接
        conn = get_redis_connection('default')
        # 拼接key
        cart_key = 'cart_%d' % user.id

        # 将sku_ids分割成一个列表
        sku_ids = sku_ids.split(',') # [3,4]

        # 遍历sku_ids，向df_order_goods中添加记录
        for sku_id in sku_ids:
            # 根据id获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            # 从redis中获取用户要购买的商品的数量
            count = conn.hget(cart_key, sku_id)

            # 向df_order_goods中添加一条记录
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=count,
                price=sku.price
            )

            # 减少商品库存，增加销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 累加计算订单中商品的总数目和总价格
            total_count += int(count)
            total_price += sku.price*int(count)

        # todo: 更新订单信息中商品的总数目和总价格
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # todo: 删除购物车中对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})



