import re
import random
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from register.models import User


def register_view(request):
    """用户注册页面 - 处理 GET 和 POST"""
    context = {}

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        verification_code = request.POST.get('verification_code', '').strip()

        errors = []

        # --- 校验用户名 ---
        if not username:
            errors.append('请输入用户名')
        elif len(username) < 2 or len(username) > 20:
            errors.append('用户名长度应为2-20个字符')
        elif not re.match(r'^[a-zA-Z0-9_一-鿿]+$', username):
            errors.append('用户名只能包含字母、数字、下划线和中文')
        elif User.objects.filter(username=username).exists():
            errors.append('该用户名已被注册')

        # --- 校验邮箱 ---
        if not email:
            errors.append('请输入邮箱')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('请输入有效的邮箱地址')
        elif User.objects.filter(email=email).exists():
            errors.append('该邮箱已被注册')

        # --- 校验密码 ---
        if not password:
            errors.append('请输入密码')
        elif len(password) < 6 or len(password) > 18:
            errors.append('密码长度应为6-18个字符')
        elif not re.match(r'^[a-zA-Z0-9_]+$', password):
            errors.append('密码只能由字母、数字和下划线组成')

        # --- 校验确认密码 ---
        if password != confirm_password:
            errors.append('两次输入的密码不一致')

        # --- 校验验证码 ---
        saved_code = request.session.get('register_verification_code', '')
        if not verification_code:
            errors.append('请输入验证码')
        elif verification_code.upper() != saved_code.upper():
            errors.append('验证码错误')

        # --- 处理结果 ---
        if errors:
            context['errors'] = errors
            # 保留已填写的用户名和邮箱（密码和验证码需重新输入）
            context['form_data'] = {
                'username': username,
                'email': email,
            }
        else:
            # 创建用户，密码哈希存储
            user = User(
                username=username,
                email=email,
                password=make_password(password),
            )
            user.save()

            # 清除 session 中的验证码
            request.session.pop('register_verification_code', None)

            context['success'] = True

    return render(request, 'register.html', context)


def send_verification_code(request):
    """发送邮箱验证码 — AJAX 接口，通过QQ邮箱发送6位验证码"""
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
    request.session['register_verification_code'] = code

    # 通过QQ邮箱发送验证码
    try:
        send_mail(
            subject='【Travel memories】邮箱验证码',
            message=f'您的验证码为：{code}，请在10分钟内完成注册。如非本人操作，请忽略此邮件。',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': '验证码已发送至您的邮箱，请注意查收'})
    except Exception as e:
        # 邮件发送失败时清除验证码，返回错误信息
        request.session.pop('register_verification_code', None)
        return JsonResponse({'success': False, 'message': '验证码发送失败，请稍后重试'})
