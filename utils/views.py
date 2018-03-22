"""用户登录要求视图基类"""
'''
@Time    : 2018/3/11 下午8:46
@Author  : scrappy_zhang
@File    : views.py
'''


from django.contrib.auth.decorators import login_required


# class LoginRequiredMixin(object):
#     '''提交要求用户登录的功能'''
#     @classmethod
#     def as_view(cls, **initkwargs):
#         # 调用父类的as_view
#         view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
#         return login_required(view)

class LoginRequiredMixin(object):
    """提供要求用户登录功能"""
    @classmethod
    def as_view(cls, *args, **kwargs):
        view = super(LoginRequiredMixin, cls).as_view(*args, **kwargs)
        return login_required(view)
