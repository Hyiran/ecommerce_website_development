from django.shortcuts import render, redirect
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
        # print('sku_ids: ', sku_ids)

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


# 未处理订单并发问题
class OrderCommitView1(View):
    """订单创建"""

    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 以,分隔的字符串 3,4

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
        sku_ids = sku_ids.split(',')  # [3,4]

        # 遍历sku_ids，向df_order_goods中添加记录
        for sku_id in sku_ids:
            # 根据id获取商品的信息
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            # 从redis中获取用户要购买的商品的数量
            count = conn.hget(cart_key, sku_id)
            # 模拟订单并发问题
            print('user: %d' % user.id)
            import time
            time.sleep(10)

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
            total_price += sku.price * int(count)

        # todo: 更新订单信息中商品的总数目和总价格
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # todo: 删除购物车中对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})


from django.db import transaction


# 悲观锁处理创建订单
class OrderCommitView2(View):
    """订单创建"""

    @transaction.atomic
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 以,分隔的字符串 3,4

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

        # 设置事务保存点
        sid = transaction.savepoint()

        try:
            # 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_count=total_count,
                total_price=total_price,
                transit_price=transit_price
            )

            # 订单中包含几个商品需要向df_order_goods中添加几条记录
            # 获取redis链接
            conn = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 将sku_ids分割成一个列表
            sku_ids = sku_ids.split(',')  # [3,4]

            # 遍历sku_ids，向df_order_goods中添加记录
            for sku_id in sku_ids:
                # 根据id获取商品的信息
                try:
                    # select * from df_goods_sku where id=<sku_id> for update;
                    # sku = GoodsSKU.objects.get(id=sku_id)
                    print('user: %d try get lock' % user.id)
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                    print('user: %d get locked' % user.id)
                except GoodsSKU.DoesNotExist:
                    # 回滚事务到sid保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

                # 从redis中获取用户要购买的商品的数量
                count = conn.hget(cart_key, sku_id)

                # 判断商品的库存
                if int(count) > sku.stock:
                    # 回滚事务到sid保存点
                    transaction.savepoint_rollback(sid)
                    return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                # 模拟订单并发问题
                # print('user: %d' % user.id)
                import time
                time.sleep(10)

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
                total_price += sku.price * int(count)

            # 更新订单信息中商品的总数目和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 回滚事务到sid保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败1'})
        # 删除购物车中对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})


# 乐观锁处理创建订单
class OrderCommitView(View):
    """订单创建"""

    @transaction.atomic
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 以,分隔的字符串 3,4

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

        # 设置事务保存点
        sid = transaction.savepoint()

        try:
            # 向df_order_info中添加一条记录
            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                addr=addr,
                pay_method=pay_method,
                total_count=total_count,
                total_price=total_price,
                transit_price=transit_price
            )

            # 订单中包含几个商品需要向df_order_goods中添加几条记录
            # 获取redis链接
            conn = get_redis_connection('default')
            # 拼接key
            cart_key = 'cart_%d' % user.id

            # 将sku_ids分割成一个列表
            sku_ids = sku_ids.split(',')  # [3,4]

            # 遍历sku_ids，向df_order_goods中添加记录
            for sku_id in sku_ids:
                for i in range(3):
                    # 根据id获取商品的信息
                    try:
                        # select * from df_goods_sku where id=<sku_id>;
                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        # 回滚事务到sid保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

                    # 从redis中获取用户要购买的商品的数量
                    count = conn.hget(cart_key, sku_id)

                    # 判断商品的库存
                    if int(count) > sku.stock:
                        # 回滚事务到sid保存点
                        transaction.savepoint_rollback(sid)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # 减少商品库存，增加销量
                    orgin_stock = sku.stock
                    new_stock = orgin_stock - int(count)
                    new_sales = sku.sales + int(count)

                    # print('user:%d times:%d stock:%d' % (user.id, i, orgin_stock))
                    # import time
                    # time.sleep(10)

                    # update from df_goods_sku
                    # set stock=<new_stock>, sales=<new_sales>
                    # where id=<sku_id> and stock=<orgin_stock>
                    # update方法返回数字，代表更新的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=orgin_stock).update(stock=new_stock, sales=new_sales)

                    if res == 0:
                        if i == 2:
                            # 回滚事务到sid保存点
                            transaction.savepoint_rollback(sid)
                            # 连续尝试了3次，仍然下单失败，下单失败
                            return JsonResponse({'res': 7, 'errmsg': '下单失败2'})
                        # 更新失败，重新进行尝试
                        continue

                    # 向df_order_goods中添加一条记录
                    OrderGoods.objects.create(
                        order=order,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )

                    # 累加计算订单中商品的总数目和总价格
                    total_count += int(count)
                    total_price += sku.price * int(count)

                    # 更新成功，跳出循环
                    break

            # 更新订单信息中商品的总数目和总价格
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            # 回滚事务到sid保存点
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '下单失败1'})

            # 删除购物车中对应的记录
        # hdel(key, *args)
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'errmsg': '订单创建成功'})


from django.conf import settings
from django.http import HttpResponse
from alipay import AliPay

# 订单支付
# 采用ajax post请求
# 前端需要传递的参数: order_id(订单id)
# /order/pay


class OrderPayView(View):
    """订单支付"""
    def post(self, request):
        # 登录验证
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '缺少参数'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1, # 待支付
                                          pay_method=3, # 支付宝支付
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '无效订单id'})

        # 业务处理: 调用支付宝python SDK中的api_alipay_trade_page_pay函数
        # 初始化
        ali_pay = AliPay(
            appid=settings.ALIPAY_APP_ID,  # 应用APPID
            app_notify_url=settings.ALIPAY_APP_NOTIFY_URL,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,  # 应用私钥文件路径
            # 支付宝的公钥文件，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False，False代表线上环境，True代表沙箱环境
        )

        # 调用支付宝pythonSDK中的api_alipay_trade_page_pay函数
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price # Decimal
        order_string = ali_pay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单id
            total_amount=str(total_pay), # 订单实付款
            subject='天天生鲜%s' % order_id, # 订单标题
            return_url='http://127.0.0.1:8000/order/check',
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        pay_url = settings.ALIPAY_GATEWAY_URL + order_string
        # print(pay_url)
        return JsonResponse({'res': 3, 'pay_url': pay_url, 'errmsg': 'OK'})


# /order/check
class OrderCheckView(LoginRequiredMixin, View):
    """订单支付结果查询"""

    def get(self, request):
        # 获取登录用户
        user = request.user

        # 获取用户订单id
        order_id = request.GET.get('out_trade_no')

        # 参数校验
        if not all([order_id]):
            return JsonResponse({'res': 1, 'errmsg': '缺少参数'})

        # 校验订单id
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          order_status=1,  # 待支付
                                          pay_method=3,  # 支付宝支付
                                          )
        except OrderInfo.DoesNotExist:
            return HttpResponse('订单信息错误')

        # 业务处理: 调用Python SDK中的交易查询的接口
        # 初始化
        ali_pay = AliPay(
            appid=settings.ALIPAY_APP_ID,  # 应用APPID
            app_notify_url=settings.ALIPAY_APP_NOTIFY_URL,  # 默认回调url
            app_private_key_path=settings.APP_PRIVATE_KEY_PATH,  # 应用私钥文件路径
            # 支付宝的公钥文件，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=settings.ALIPAY_PUBLIC_KEY_PATH,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False，False代表线上环境，True代表沙箱环境
        )

        # 调用Python SDK 中api_alipay_trade_query参数说明：

        # {
        #     "trade_no": "2017032121001004070200176844", # 支付宝交易号
        #     "code": "10000", # 网关返回码
        #     "invoice_amount": "20.00",
        #     "open_id": "20880072506750308812798160715407",
        #     "fund_bill_list": [
        #         {
        #             "amount": "20.00",
        #             "fund_channel": "ALIPAYACCOUNT"
        #         }
        #     ],
        #     "buyer_logon_id": "csq***@sandbox.com",
        #     "send_pay_date": "2017-03-21 13:29:17",
        #     "receipt_amount": "20.00",
        #     "out_trade_no": "out_trade_no15",
        #     "buyer_pay_amount": "20.00",
        #     "buyer_user_id": "2088102169481075",
        #     "msg": "Success",
        #     "point_amount": "0.00",
        #     "trade_status": "TRADE_SUCCESS", # 支付状态
        #     "total_amount": "20.00"
        # }

        # 调用Python SDK 中api_alipay_trade_query 查询交易结果
        response = ali_pay.api_alipay_trade_query(out_trade_no=order_id)
        # 获取支付宝网关的返回码
        res_code = response.get('code')

        if res_code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
            # 支付成功 10000
            # 更新订单的支付状态和支付宝交易号
            order.order_status = 4  # 待评价
            order.trade_no = response.get('trade_no')
            order.save()

            # 返回结果
            return render(request, 'pay_result.html', {'pay_result': '支付成功'})
        else:
            # 支付失败
            return render(request, 'pay_result.html', {'pay_result': '支付失败'})


# /order/comment/订单id
class CommentView(LoginRequiredMixin, View):
    """订单评论"""
    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order', kwargs={"page": 1}))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order", kwargs={"page": 1}))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count*order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order', kwargs={"page": 1}))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order", kwargs={"page": 1}))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容 1-total_count
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i) # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '') # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5 # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
