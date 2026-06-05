import re
import random
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings
from register.models import User


def login_view(request):
    """用户登录页面 - 处理 GET 和 POST"""
    context = {}

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        verification_code = request.POST.get('verification_code', '').strip()

        errors = []

        # --- 校验邮箱 ---
        if not email:
            errors.append('请输入邮箱')

        # --- 校验密码 ---
        if not password:
            errors.append('请输入密码')

        # --- 校验验证码 ---
        saved_code = request.session.get('login_verification_code', '')
        if not verification_code:
            errors.append('请输入验证码')
        elif verification_code.upper() != saved_code.upper():
            errors.append('验证码错误')

        # --- 没有基础错误时进行登录验证 ---
        if not errors:
            try:
                user = User.objects.get(email=email)
                if check_password(password, user.password):
                    # 登录成功，清除验证码
                    request.session.pop('login_verification_code', None)
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username

                    # 支持 next 参数：登录后跳转到目标页面
                    next_url = request.POST.get('next') or request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('product_homepage')
                else:
                    errors.append('邮箱或密码错误')
            except User.DoesNotExist:
                errors.append('邮箱或密码错误')

        if errors:
            context['errors'] = errors
            context['form_data'] = {'email': email}

    return render(request, 'index.html', context)


def send_login_code(request):
    """发送登录验证码 — AJAX 接口，通过QQ邮箱发送6位验证码"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '请求方式错误'}, status=405)

    email = request.POST.get('email', '').strip()

    # 校验邮箱格式
    if not email:
        return JsonResponse({'success': False, 'message': '请输入邮箱地址'})
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return JsonResponse({'success': False, 'message': '邮箱格式不正确'})

    # 生成6位数字验证码
    code = str(random.randint(100000, 999999))
    request.session['login_verification_code'] = code

    # 通过QQ邮箱发送验证码
    try:
        send_mail(
            subject='【Travel memories】登录验证码',
            message=f'您的登录验证码为：{code}，请在10分钟内完成登录。如非本人操作，请忽略此邮件。',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': '验证码已发送至您的邮箱，请注意查收'})
    except Exception as e:
        request.session.pop('login_verification_code', None)
        return JsonResponse({'success': False, 'message': '验证码发送失败，请稍后重试'})
