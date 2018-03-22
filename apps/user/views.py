import re
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
# from django.core.mail import send_mail
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
# django内置的认证系统函数
from django.contrib.auth import authenticate, login, logout
# django认证中的用户登入检测
from django.contrib.auth.decorators import login_required

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from apps.user.models import User, Address
from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from celery_tasks import tasks


# from apps.user import tasks

# Create your views here.


# /user/register
class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示"""
        # print('get----')
        return render(request, 'register.html')

    def post(self, request):
        """注册处理"""
        # print('post----')
        # 1.接收参数
        username = request.POST.get('user_name')  # None
        password = request.POST.get('pwd')
        email = request.POST.get('email')

        # 2.参数校验(后端校验)
        # 校验数据的完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 校验邮箱格式
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 校验用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is not None:
            return render(request, 'register.html', {'errmsg': '用户名已注册'})

        # 校验邮箱是否被注册...

        # 3.业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 注册之后，需要给用户的注册邮箱发送激活邮件，在激活邮件中需要包含激活链接
        # 激活链接: /user/active/用户id
        # 存在问题: 其他用户恶意请求网站进行用户激活操作
        # 解决问题: 对用户的信息进行加密，把加密后的信息放在激活链接中，激活的时候在进行解密
        # /user/active/加密后token信息

        # 对用户的身份信息进行加密，生成激活token信息
        serializer = Serializer(settings.SECRET_KEY, 3600 * 7)
        info = {'confirm': user.id}
        # 返回bytes类型
        token = serializer.dumps(info)
        # str
        token = token.decode()

        # 组织邮件信息
        # subject = '天天生鲜欢迎信息'
        # message = ''
        # sender = settings.EMAIL_FROM
        # receiver = [email]
        # html_message = """
        #             <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
        #             请点击一下链接激活您的账号(7小时之内有效)<br/>
        #             <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
        #         """ % (username, token, token)
        #
        # # 发送激活邮件
        # # send_mail(subject='邮件标题',
        # #           message='邮件正文',
        # #           from_email='发件人',
        # #           recipient_list='收件人列表')
        # send_mail(subject, message, sender, receiver, html_message=html_message)
        tasks.send_register_active_email.delay(email, username, token)

        # 4.返回应答: 跳转到首页
        return redirect(reverse('goods:index'))


# /user/active/加密token
class ActiveView(View):
    """激活"""

    def get(self, request, token):
        """激活"""
        # print('---active---')
        serializer = Serializer(settings.SECRET_KEY, 3600 * 7)
        try:
            # 解密
            info = serializer.loads(token)
            # 获取待激活用户id
            user_id = info['confirm']
            # 激活用户
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已失效
            # 实际开发: 返回页面，让你点击链接再发激活邮件
            return HttpResponse('激活链接已失效')


# /user/login
class LoginView(View):
    """登录"""

    def get(self, request):
        """显示"""
        # 判断用户是否记住用户名
        username = request.COOKIES.get('username')

        checked = 'checked'
        if username is None:
            # 没有记住用户名
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')  # None
        # 调试查看
        # print('username:', username)
        # print('password:', password)
        # print('remember:', remember)

        # 2.参数校验(后端校验)
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '参数不完整'})

        # 3.业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活
                # 记住用户的登录状态
                login(request, user)

                # 获取用户登录之前访问的url地址，默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))  # None
                # print(next_url)

                # 跳转到next_url
                response = redirect(next_url)  # HttpResponseRedirect

                # 跳转到首页
                # response = redirect(reverse('goods:index'))  # HttpResponseRedirect
                # 将用户名赋值给index
                # 方式1：直接在session里面记录该值，并传递给重定向
                # request.session['is_login'] = username
                # 方式2： 设置cookie，不安全
                # response.set_cookie('is_login', username)
                # 方式3：由于采用django自带的authenticate，因此，可以在模板中使用user.is_authenticated
                #

                # 判断是否需要记住用户名
                if remember == 'on':
                    # 设置cookie username
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    # 删除cookie username
                    response.delete_cookie('username')
                # response.set_cookie('name', username)
                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# request对象有一个属性user, request.user
# 如果用户已登录，request.user是一个认证用户模型类(User)的对象，包含登录用户的信息
# 如果用户未登录，request.user是一个匿名用户类(AnonymousUser)的对象

# is_authenticated
# User类这个方法永远返回的是True
# AnonymousUser类这个方法永远返回的是False

# 在模板文件中可以直接使用一个模板变量user，实际上就是request.user

# /user/logout
class LogoutView(View):
    """退出"""

    def get(self, request):
        """退出"""
        # 清除用户登录状态,内置的logout函数会自动清除当前session
        logout(request)

        # 跳转到登录
        return redirect(reverse('user:login'))


# login_required

from django.contrib.auth.decorators import login_required
from utils.mixin import LoginRequiredView, LoginRequiredMixin
from django_redis import get_redis_connection


# /user/
# class UserInfoView(View):
# class UserInfoView(LoginRequiredView):
class UserInfoView(LoginRequiredMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        """显示"""
        # 获取登录用户
        user = request.user

        # 获取用户的默认收货地址
        address = Address.objects.get_default_address(user)

        # 获取用户的最近浏览商品的信息
        # 若采用redis第三包交互时
        # from redis import StrictRedis
        # conn = StrictRedis(host='172.16.179.142', port=6379, db=5)

        # 返回StrictRedis类的对象
        # 若采用django-redis包时
        conn = get_redis_connection('default')
        # 拼接key
        history_key = 'history_%d' % user.id

        # lrange(key, start, stop) 返回是列表
        # 获取用户最新浏览的5个商品的id
        sku_ids = conn.lrange(history_key, 0, 4) # [1, 3, 5, 2]

        skus = []
        for sku_id in sku_ids:
            # 根据商品的id查询商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 追加到skus列表中
            skus.append(sku)

        # 组织模板上下文
        context = {
            'address': address,
            'skus': skus,
            'page': 'user'
        }

        # 使用模板
        return render(request, 'user_center_info.html', context)


# /user/order
# class UserOrderView(View):
# class UserOrderView(LoginRequiredView):
class UserOrderView(LoginRequiredMixin, View):
    """用户中心-订单页"""

    def get(self, request, page):
        """显示"""
        # 获取登录用户
        user = request.user
        # 查询所有订单
        info_msg = 1   # 若有订单则为1
        try:
            order_infos = OrderInfo.objects.filter(user=user).order_by('-create_time')
        except OrderInfo.DoesNotExist :
            info_msg = 0

        if len(order_infos) == 0:
            info_msg = 0
        context = {
            'page': 'order',
            'info_msg': info_msg,
        }
        if info_msg == 1:

            for order_info in order_infos:
                order_goods = OrderGoods.objects.filter(order=order_info)
                for order_good in order_goods:
                    # 商品小计
                    amount = order_good.price * order_good.count
                    order_good.amount = amount
                order_info.order_goods = order_goods
                order_info.status_title = OrderInfo.ORDER_STATUS[order_info.order_status]
                # order_info.status = order_info.ORDER_STATUS_CHOICES[order_info.order_status-1][1]

            # 分页操作
            from django.core.paginator import Paginator
            paginator = Paginator(order_infos, 3)

            # 处理页码
            page = int(page)

            if page > paginator.num_pages:
                # 默认获取第1页的内容
                page = 1

            # 获取第page页内容, 返回Page类的实例对象
            order_infos_page = paginator.page(page)

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

            context = {
                'page': 'order',
                'order_infos': order_infos,
                'info_msg': info_msg,
                'pages' : pages,
                'order_infos_page': order_infos_page
            }
        return render(request, 'user_center_order.html', context)


# /user/address
# class AddressView(View):
# class AddressView(LoginRequiredView):
class AddressView(LoginRequiredMixin, View):
    """用户中心-地址页"""
    def get(self, request):
        """显示"""
        # 获取登录用户user
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        default_address = Address.objects.get_default_address(user)

        all_address = Address.objects.get_all_address(user)

        # 组织模板上下文
        context = {
            'address': default_address,
            'have_address': all_address,
            'page': 'address'
        }

        # 使用模板
        return render(request, 'user_center_site.html', context)

    def post(self, request):
        """地址添加"""
        # 接收参数
        receiver = request.POST.get('receiver')
        addr = request.POST.get('direction')
        zip_code = request.POST.get('mail_code')
        phone = request.POST.get('phone_number')

        # 参数校验
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号

        # 业务处理：添加收货地址
        # 如果用户已经有默认地址，新添加的地址作为非默认地址，否则作为默认地址
        # 获取登录用户user
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)

        is_default = True
        if address is not None:
            is_default = False

        # 添加收货地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答，刷新地址页面
        return redirect(reverse('user:address'))

