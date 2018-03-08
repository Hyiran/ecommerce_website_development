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