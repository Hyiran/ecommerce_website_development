import re
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
# from django.core.mail import send_mail
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
# django内置的认证系统函数
from django.contrib.auth import authenticate, login, logout

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from apps.user.models import User
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
        remember = request.POST.get('remember') # None
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


                # 跳转到首页
                response = redirect(reverse('goods:index'))  # HttpResponseRedirect
                # 将用户名赋值给index
                # 方式1：直接在session里面记录该值，并传递给重定向
                request.session['is_login'] = username
                # 方式2： 设置cookie，不安全
                # response.set_cookie('is_login', username)
                # 方式3：由于采用django自带的authenticate，因此，可以在模板中使用user.is_authenticated
                #

                # 判断是否需要记住用户名
                if remember == 'on':
                    # 设置cookie username
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    # 删除cookie username
                    response.delete_cookie('username')

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
        # 清除用户登录状态
        logout(request)

        # 跳转到登录
        return redirect(reverse('user:login'))



