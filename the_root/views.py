from django.shortcuts import render, redirect
from django.conf import settings
from register.models import User
from the_root.decorators import login_required


def index(request):
    """首页 — 已登录用户（含"记住我"）自动跳转到产品主页"""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            User.objects.get(id=user_id)
            return redirect('product_homepage')
        except User.DoesNotExist:
            request.session.flush()
    return render(request, 'index.html')


@login_required
def product_homepage(request):
    """产品主页 — 登录成功后跳转到此页面"""
    user = request.user_obj
    context = {
        'username': user.username,
        'email': user.email,
    }
    return render(request, 'Product_homepage.html', context)


def logout_view(request):
    """退出登录 — 清除 session 并跳转到首页"""
    request.session.flush()
    return redirect('index')
