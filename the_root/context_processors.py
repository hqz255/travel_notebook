"""
模板上下文处理器 — 为所有模板自动注入用户相关信息，避免每个视图重复传参。

按约定，上下文字段名以下划线分隔（snake_case），与现有模板变量保持一致。
"""

from register.models import User


def user_info(request):
    """将当前登录用户的 avatar_url、username、email 注入所有模板上下文。

    该处理器在所有使用 navbar_authenticated.html 的页面中自动提供用户信息，
    无需每个视图手动传递。对于未登录用户，返回空值，模板中按需判断。

    Returns:
        dict: 包含 avatar_url, username, email 的字典（未登录时均为空字符串）。
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return {
            'avatar_url': '',
            'username': '',
            'email': '',
        }

    try:
        user = User.objects.only('avatar', 'username', 'email').get(id=user_id)
    except User.DoesNotExist:
        # session 中的 user_id 对应不到数据库记录（用户被删除等）
        request.session.flush()
        return {
            'avatar_url': '',
            'username': '',
            'email': '',
        }

    return {
        'avatar_url': user.avatar.url if user.avatar else '',
        'username': user.username,
        'email': user.email,
    }
