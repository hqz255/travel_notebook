import os
import re

from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password

from record_memories.models import Article
from register.models import User
from the_root.decorators import login_required


# ---------------------------------------------------------------------------
# 头像上传安全配置（与 record_memories 保持一致的多层校验）
# ---------------------------------------------------------------------------

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 头像最大 5 MB

_IMAGE_MAGIC_SIGNATURES = [
    (b'\xff\xd8\xff', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', '.png'),
    (b'RIFF', '.webp'),
    (b'GIF87a', '.gif'),
    (b'GIF89a', '.gif'),
    (b'BM', '.bmp'),
    (b'\x00\x00\x01\x00', '.ico'),
]


def _detect_extension_by_magic(header: bytes):
    for magic, ext in _IMAGE_MAGIC_SIGNATURES:
        if header[:len(magic)] == magic:
            if ext == '.webp' and header[8:12] != b'WEBP':
                continue
            return ext
    return None


def _validate_avatar(uploaded_file):
    """验证头像文件，返回 (is_valid, error_message)。"""
    if uploaded_file.size > MAX_AVATAR_SIZE:
        return False, f'头像文件过大，最大允许 {MAX_AVATAR_SIZE // (1024*1024)} MB'

    if uploaded_file.size == 0:
        return False, '头像文件为空'

    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f'不支持的文件格式「{ext}」，请上传 JPG / PNG / WEBP / GIF / BMP 格式'

    uploaded_file.seek(0)
    header = uploaded_file.read(16)
    uploaded_file.seek(0)

    detected_ext = _detect_extension_by_magic(header)
    if detected_ext is None:
        return False, '头像文件不是有效的图片格式'
    if detected_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f'头像真实类型为 {detected_ext}，不在允许的格式列表中'

    # PIL 深度验证
    try:
        from PIL import Image as PILImage
        uploaded_file.seek(0)
        img = PILImage.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
    except Exception:
        uploaded_file.seek(0)
        return False, '头像图片文件已损坏或内容无效'

    return True, ''


# ---------------------------------------------------------------------------
# 视图
# ---------------------------------------------------------------------------


@login_required
def user_pub(request):
    """我的回忆 — 展示当前登录用户发布的所有文章"""
    user = request.user_obj

    articles = (
        Article.objects
        .filter(author=user)
        .select_related('author')
        .prefetch_related('categories')
        .annotate(comment_count=Count('comments'))
        .order_by('-created_at')
    )

    # 汇总统计
    total_views = sum(a.views_count for a in articles)
    total_comments = sum(a.comment_count for a in articles)

    return render(request, 'user_pub.html', {
        'username': user.username,
        'email': user.email,
        'articles': articles,
        'total_articles': len(articles),
        'total_views': total_views,
        'total_comments': total_comments,
    })


@login_required
def user_setting(request):
    """账号设置 — 查看和修改个人信息（GET 展示 / POST 处理）"""
    user = request.user_obj

    context = {
        'username': user.username,
        'email': user.email,
        'avatar_url': user.avatar.url if user.avatar else '',
        'errors': [],
        'success': '',
        'form_data': {},
    }

    # =========================================================================
    # GET — 展示当前个人信息
    # =========================================================================
    if request.method == 'GET':
        return render(request, 'user_setting.html', context)

    # =========================================================================
    # POST — 根据 action 参数分发到不同处理逻辑
    # =========================================================================
    action = request.POST.get('action', '').strip()
    uploaded_avatar = request.FILES.get('avatar')

    errors = []

    # ---- 修改个人信息 ----
    if action == 'update_profile':
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()

        context['form_data'] = {'username': new_username, 'email': new_email}

        # 校验用户名
        if not new_username:
            errors.append('请输入用户名')
        elif len(new_username) > 20:
            errors.append('用户名不能超过 20 个字符')
        elif new_username != user.username and User.objects.filter(username=new_username).exists():
            errors.append('该用户名已被使用')

        # 校验邮箱
        if not new_email:
            errors.append('请输入邮箱')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
            errors.append('邮箱格式不正确')
        elif new_email != user.email and User.objects.filter(email=new_email).exists():
            errors.append('该邮箱已被注册')

        if not errors:
            user.username = new_username
            user.email = new_email
            user.save()

            # 同步更新 session 中的 username
            request.session['username'] = new_username

            context['success'] = '个人信息更新成功'
            context['username'] = new_username
            context['email'] = new_email
            context['form_data'] = {}
        else:
            context['errors'] = errors

    # ---- 修改密码 ----
    elif action == 'change_password':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not current_password:
            errors.append('请输入当前密码')
        elif not check_password(current_password, user.password):
            errors.append('当前密码错误')

        if not new_password:
            errors.append('请输入新密码')
        elif len(new_password) < 6:
            errors.append('新密码长度不能少于 6 位')

        if new_password != confirm_password:
            errors.append('两次输入的新密码不一致')

        if not errors:
            user.password = make_password(new_password)
            user.save()
            context['success'] = '密码修改成功，请牢记新密码'
        else:
            context['errors'] = errors

    # ---- 上传头像 ----
    elif action == 'upload_avatar':
        if not uploaded_avatar:
            errors.append('请选择要上传的头像图片')
        else:
            is_valid, err_msg = _validate_avatar(uploaded_avatar)
            if not is_valid:
                errors.append(err_msg)
            else:
                # 删除旧头像文件（如果有）
                if user.avatar:
                    old_avatar_path = user.avatar.path
                    if os.path.isfile(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except OSError:
                            pass

                user.avatar = uploaded_avatar
                user.save()
                context['success'] = '头像上传成功'

        if errors:
            context['errors'] = errors

    else:
        errors.append('无效的操作')

    if errors:
        context['errors'] = errors

    # 刷新头像 URL
    context['avatar_url'] = user.avatar.url if user.avatar else ''

    return render(request, 'user_setting.html', context)
