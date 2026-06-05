from django.shortcuts import render, redirect
from django.conf import settings
from register.models import User


def index(request):
    return render(request, 'index.html')


def product_homepage(request):
    """产品主页 — 登录成功后跳转到此页面"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect(settings.LOGIN_URL)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect(settings.LOGIN_URL)

    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, 'Product_homepage.html', context)


def logout_view(request):
    """退出登录 — 清除 session 并跳转到首页"""
    request.session.flush()
    return redirect('index')