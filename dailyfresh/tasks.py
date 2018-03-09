"""please input file function"""
'''
@Time    : 2018/3/9 下午4:06
@Author  : scrappy_zhang
@File    : tasks.py
'''


from celery import Celery

# 我们这里案例使用redis作为broker
app = Celery('demo',
             backend='redis://127.0.0.1:6379/1',
             broker='redis://127.0.0.1:6379/2')

# 创建任务函数
@app.task
def my_task(a, b):
    print("任务函数正在执行....")
    return a + b