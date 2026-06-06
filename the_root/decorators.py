from functools import wraps
from django.shortcuts import redirect
from django.conf import settings
from register.models import User


def login_required(view_func):
    """Session-based login-required decorator.

    Checks that request.session['user_id'] exists and that the
    corresponding User row is still in the database. On failure,
    flushes the session and redirects to settings.LOGIN_URL.

    Attaches the resolved User object to request.user_obj for
    convenience in downstream views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect(settings.LOGIN_URL)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.flush()
            return redirect(settings.LOGIN_URL)
        request.user_obj = user
        return view_func(request, *args, **kwargs)
    return wrapper
