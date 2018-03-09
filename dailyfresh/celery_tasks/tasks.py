from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
# 导入Celery类
# from celery import Celery

# 这两行代码在启动worker进行的一端打开
# 设置django配置依赖的环境变量
import os
import sys
sys.path.insert(0, './')
# import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
# django.setup()

# from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# 创建一个Celery类的对象
# app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/11')
from celery_tasks.celery import app as app


# 定义任务函数
@app.task
def send_register_active_email(to_email, username, token):
    """发送激活邮件"""
    # 组织邮件内容
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = """
                        <h1>%s, 欢迎您成为天天生鲜注册会员</h1>
                        请点击以下链接激活您的账户(7个小时内有效)<br/>
                        <a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>
                    """ % (username, token, token)

    # 发送激活邮件
    # send_mail(subject=邮件标题, message=邮件正文,from_email=发件人, recipient_list=收件人列表)
    # import time
    # time.sleep(5)
    send_mail(subject, message, sender, receiver, html_message=html_message)









