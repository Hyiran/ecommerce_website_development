from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.

# http://127.0.0.1:8000
# /
def index(request):
    """首页"""
    # if request.session.get('is_login'):
    #     username = request.session['is_login']
    #     print(username)
    #     del request.session['is_login']
    #     content = {'username': username}
    #     return render(request, 'index.html', content)

    #  if 'is_login' in request.COOKIES:
    #     username = request.COOKIES['is_login']
    #     print(username)
    #     content = {'username': username}
    #     response = render(request, 'index.html', content)
    #     response.delete_cookie('is_login')
    #     return response

    # username = 0
    # print('**********')
    # return render(request, 'index.html', {'username': username})
    return render(request, 'index.html')



