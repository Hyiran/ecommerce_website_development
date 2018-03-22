"""celery配置"""
'''
@Time    : 2018/3/9 下午4:28
@Author  : scrappy_zhang
@File    : celeryconfig.py
'''

from kombu import Exchange, Queue

BROKER_URL = 'redis://127.0.0.1:6379/1'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/2'
