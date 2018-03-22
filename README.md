# ecommerce_website_development
本项目基于Django1.8.2等来开发一个电商平台，可实现注册、登录、浏览、购买、支付等全部常用功能。

## 运行方式：

修改如下文件的名称：去掉.example

- 修改settings.example.py为settings.py并将相关参数设置为本地参数
- 修改alipay_public_key_.pem与app_private_key.pem为自己的
- 修改client.conf为自己的FastDFS系统客户端配置文件
- 修改uwsgi.ini为自己的设置



## 重点内容有：

- Redis实现购物车记录存储
- Redis实现最近浏览记录存储
- 发送注册邮件以Celery异步操作实现
- 网站优化之首页动态页面静态化——以Celery异步操作实现
- 网站优化之首页缓存——Redis存储
- 分布式存储系统FastDFS存储网站商品图片——自定义存储器类
- 商品搜索框架`haystack`
- 订单并发库存问题之悲观锁与乐观锁
- 自定义管理器实现快速查询数据
- 采用Django内置的认证系统进行登录校验——自定义用户类、校验装饰器
- session基于Redis存储
- 支付宝接口









- 用户历史浏览记录存储的分析过程——一般用户最近浏览的均为用户的感兴趣群体数据，有助于推荐更精准的广告或者产品。

  ```
  问题分析:
  1）什么时候需要添加用户历史浏览的记录？
  答:当用户点击某个商品，访问商品的详情页面(详情页视图)的时候，才要添加历史浏览记录。

  2）什么时候需要获取用户历史浏览的记录？
  答: 当用户访问用户中心-信息页(信息页视图)的时候，需要获取用户的历史浏览记录。

  3）保存用户的历史浏览记录需要保存哪些数据？
  答: 保存商品id，添加历史浏览记录时需要保持用户的浏览顺序。

  4）数据需要保存在哪里？
  答: 数据持久化保存: 文件 mysql数据库 redis数据库。对于频繁操作的数据，为了提高处理的效率，
  建议放在redis数据库。

  5）采用redis中哪种数据格式？key-value key是字符串类型，value分为5种类型。
  存储方案1：所有用户的历史浏览记录用一条数据来保存。
    key: history
    值选择hash, 属性(user_用户id), 用hash的属性来区分每一个用户。
    属性(user_用户id)的值来保存用户浏览的商品的id, 属性值保存成以逗号分隔的字符 '2,3,4'

  存储方案2：每个用户的历史浏览记录用一条数据来保存。
    key: history_用户id 用key来区分每一个用户
    value选择list: [3, 1, 2]，最新浏览的商品的id添加到列表最左侧

  存储方案1操作历史浏览记录时需要进行额外的字符串操作，存储方案2的效率更高。
  ```

<font color=blue>一个常见的问题: mySQL里有2000w数据，redis中只存20w的数据，如何保证redis中的数据都是热点数据</font>：

相关知识点：

- redis 内存数据集大小上升到一定大小的时候，就会施行数据淘汰策略。
- redis<font color=red>常见的六种淘汰策略</font>：
  - volatile-lru：从已设置过期时间的数据集（server.db[i].expires）中挑选最近最少使用的数据淘汰；
  - volatile-ttl：从已设置过期时间的数据集（server.db[i].expires）中挑选将要过期的数据淘汰；
  - volatile-random：从已设置过期时间的数据集（server.db[i].expires）中任意选择数据淘汰；
  - allkeys-lru：从数据集（server.db[i].dict）中挑选最近最少使用的数据淘汰；
  - allkeys-random：从数据集（server.db[i].dict）中任意选择数据淘汰；
  - no-enviction（驱逐）：禁止驱逐数据。

<font color=blue>限制用户短时间内登录次数的问题：</font>

```python
"""用列表实现:列表中每个元素代表登陆时间,只要最后的第5次登陆时间和现在时间差不超过1小时就禁止登陆"""
"""
请用Redis和任意语言实现一段恶意登录保护的代码，限制1小时内每用户Id最多只能登录5次
"""
import redis
import sys
import time

r = redis.StrictRedis(host='127.0.0.1', port=6379, db=1)
try:
    id = sys.argv[1]
except:
    print('input argument error')
    sys.exit(0)
# 将每次登陆的时间存入redis的名为login_item列表中，判断列表元素个数是否已达到5并且和第一次登录时间比较是否在一个小时以内。
if r.llen('login_item') >= 5 and (time.time() - float(r.lindex('login_item', 4)) <= 3600):
    print('you are forbidden logining')
else:
    print('you are allowed to login')
    r.lpush('login_item', time.time())
```


