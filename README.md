# ecommerce_website_development
本项目基于Django1.8.2和django-bootstrap3等来开发一个电商平台，可实现注册、登录、浏览、购买、支付等全部常用功能。



## 20180309

- web项目开发的一般流程。

  ```
  项目立项->需求分析->原型设计
  后端：架构设计->数据库设计->模块代码实现和单元测试
  前端: UI设计->前端设计
  代码整合->集成测试->网站发布(项目上线)
  ```

- 天天生鲜项目的需求和架构设计。

  ```
  四大模块:
  1）用户模块: 注册、激活、登录、退出、用户中心
  2）商品模块: 首页、详情页、列表页、商品搜索
  3）购物车模块: 购物车记录的增、删、改、查
  4）订单模块: 订单创建、订单显示、订单支付
  ```

- 天天生鲜项目数据库的设计和分析。

  ```
  数据库设计:
  1）用户模块
    用户表(df_user)
    地址表(df_address)

  2）商品模块
    商品种类表(df_goods_type)
    商品SPU表(df_goods)
    商品SKU表(df_goods_sku)
    商品图片表(df_goods_image)
    首页轮播商品表(df_index_banner)
    首页促销活动表(df_index_promotion)
    首页分类商品展示表(df_index_type_goods)

  3) 购物车模块
    redis实现

  4）订单模块
    订单信息表(df_order_info)
    订单商品表(df_order_goods)

  数据库设计注意点:
  1）对于一对多的关系，应该设计两张表，并且多表中存放外键。
  2）数据库设计时，有些时候需要以空间换取时间。
  ```

- 天天生鲜项目相关模型类的设计。

  ```
  choices: 限定字段的取值范围。

  富文本编辑器的使用:
  1）安装包
    pip install django-tinymce==2.6.0

  2）注册应用并配置
    INSTALLED_APPS = (
      # ...
      'tinymce', # 富文本编辑器
      # ...
    )

    TINYMCE_DEFAULT_CONFIG = {
      'theme': 'advanced',
      'width': 600,
      'height': 400,
    }

  3）项目的urls中添加url配置项。
    urlpatterns = [
      # ...
      url(r'^tinymce/$', include('tinymce.urls')), # 富文本编辑器
      # ...
    ]

  使用富文本类型:
  1）导入类型
    from tinymce.models import HTMLField

  2）创建模型类
    class Goods(models.Model):
      """商品模型类"""
      detail = HTMLField(verbose_name='商品详情')
  ```

- 天天生鲜项目框架的搭建过程。

  ```
  项目框架搭建流程:
  1）创建Django项目
  2）根据项目功能模块划分创建应用
  3）进行基本配置(注册应用，模板文件目录，静态文件目录，数据库配置)
  4）模型类的设计
  5）迁移生成数据表

  注意点:
  1）项目中存储用户信息时需要覆盖Django默认的认证系统用户模型类，所以生成迁移文件之前需要在
  settings.py配置文件中进行如下设置:
    AUTH_USER_MODEL = 'user.User'
  ```

## 20180310

- 类视图来填充views.py。

  ```
  类视图:
    访问url时采用不同的请求方式(get、post)，就会调用类视图中对应的方法。

  使用:
  1) views.py中定义类视图
  class RegisterView(View):
    def get(self, request):
      """注册页面显示"""
      pass

    def post(self, request):
      """注册处理"""
      pass

  2) 在urls.py中进行配置
  from someapp.views import RegisterView
  urlpatterns = [
    # ...
    url(r'^register$', RegisterView.as_view(), name='register')
    # ...
  ]
  ```

- django中常见认证相关函数的使用。

  ```
  导入:
    from django.contrib.auth import create_user, authenticate, login, logout

  create_user: 添加用户。
  authenticate: 认证用户。
  login: 记住用户登录状态。
  logout: 清除用户登录状态。
  ```

- django中邮件的发送。

  ```
  1）配置文件中进行邮件相关配置。
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.163.com'
    EMAIL_PORT = 25
    #发送邮件的邮箱
    EMAIL_HOST_USER = 'itcast88@163.com'
    #在邮箱中设置的客户端授权密码
    EMAIL_HOST_PASSWORD = 'python808'
    #收件人看到的发件人
    EMAIL_FROM = 'python<itcast88@163.com>'
  2）使用send_mail函数发送邮件。
    from django.core.mail import send_mail
    send_mail(
      subject='邮件主题',
      message='邮件正文',
      from_email='发件人',
      recipient_list='收件人列表',
      html_message='包含html的邮件内容')
  ```

- 4.itsdangerous包加密解密的简单使用。

  ```
  安装:
    pip install itsdangerous

  使用:
    from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
    from itsdangerous import SignatureExpired

    # 创建Serializer类对象
    serializer = Serializer('加解密密钥', '解密有效时间')
    info = {'confirm': 1}
    # 调用dumps方法实现加密，返回值类型为bytes
    token = serializer.dumps(info)
    # 调用loads方法实现解密
    try:
      res = serializer.loads(token)
    except SignatureExpired as e:
      # 超过解密有效时间，抛出异常
      pass
  ```

- 5.celery异步任务队列的使用，将发送邮件等耗时操作由其操作，以便提升前端用户体验。

  ```
  celery(异步任务队列):
  1) 任务发出者: 发出任务。
  2) 任务处理者: 处理任务。
  3）中间人(broker): 又叫任务队列，用于任务发出者和处理者之间信息的交换。

  注意点:
  1）celery中，任务发出者、中间人和任务处理者可以在不同的电脑上，但前提是
  发出者和处理者必须都能连接到中间人。
  2）在celery中，任务就是函数，处理者就是工作的进程。
  3）celery发出任务时，只是发出的要执行的任务函数的名字和所需的参数。

  使用:
  1）安装
    pip install celery
  2) 无论是发出任务还是启动工作的进程，都需要一个Celery类的对象。
    from celery import Celery
    app = Celery('demo', broker='中间人地址')
  3）定义任务函数tasks.py
    @app.task
    def task_func(a, b):
      print('任务函数...')
  4）启动工作进程
  celery -A 任务函数所在文件的路径 worker -l info
  5）发送任务
  task_func.delay(2, 3)
  ```

- 6.用户注册的处理流程。

  ```
  # /user/register
  class RegisterView(View):
      def post(self, request):
        """注册处理"""
        # 获取参数

        # 参数校验(参数完整性校验，邮箱格式校验)

        # 业务处理: 注册处理
          # 校验用户名是否已被注册
          # 添加注册用户的信息(调用create_user方法)
          user = User.objects.create_user('用户名', '邮箱', '密码')
          # 生成激活token信息
          # 使用celery发出发送邮件任务
          # 跳转到首页
  ```

- 7.用户激活的处理流程。

  ```
  # /user/active/激活token信息
  class ActiveView(View):
      def get(self, request, token):
        """激活"""
        # 创建Serializer对象
        try:
          # 解密
          # 获取待激活用户的id
          # 查找用户并设置激活标记
          # 跳转到登录页
        except SignatureExpired as e:
          # 激活链接已失效
          pass
  ```

- 8.用户登录和退出的处理流程。

  ```
  # /user/login
  class LoginView(View):
    def post(self, request):
      """登录处理"""
      # 获取参数

      # 参数校验(完整性校验)

      # 业务处理: 登录验证
      # 验证用户名和密码的正确性(调用authenticate方法)
      user = authenticate(username='用户名', password='密码')
      if user is not None:
        # 用户名密码正确
        if user.is_active:
          # 用户已激活
          # 记录用户的登录状态(调用login方法)
          login(request, user)

          # 判断是否需要记住用户名

          # 跳转到首页，跳转传递参数：1、session设置；2、cookies设置；
          # 3、内置的user.is_authenticated
        else:
          # 用户未激活
      else:
        # 用户名或密码错误

  # /user/logout
  class LogoutView(View):
    def get(self, request):
      """退出"""
      # 清除用户的登录状态(调用logout方法)
      logout(request)

      # 跳转到登录页面
  ```

- 9.request对象的user属性。

  ```
  每个请求到达Django框架后，request对象都会有一个user属性。
  1）如果用户已登录，request.user是一个认证系统用户模型类(User)的对象，包含登录用户的信息。
  2）如果用户未登录，request.user是一个匿名用户类(AnonymousUser)的对象。

  User类和AnonymousUser类对象都有一个方法is_authenticated方法。
  User类这个方法返回的是True, AnonymousUser类这个方法返回的是False。
  通过reqeust.user.is_authenticated()可以判断用户是否登录。

  注意:
  1) 在模板文件中可以直接使用一个模板变量user，其实就是request.user。

  ```

- 10.使用django-redis配置缓存和存储session信息。

  ```
  1) 安装
  pip install django-redis

  2) 配置
  # Django框架中缓存配置
  CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # 设置缓存信息存储到redis中
        "LOCATION": "redis://redis主机ip:redis主机port/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
  }
  # Django框架中的session存储配置
  # 设置session存储到缓存中
  SESSION_ENGINE = "django.contrib.sessions.backends.cache"
  # session存储到CACHES配置项中default对应的redis数据库中
  SESSION_CACHE_ALIAS = "default"
  ```