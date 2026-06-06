from django.shortcuts import render
from the_root.decorators import login_required


@login_required
def interact(request):
    """互动交流"""
    user = request.user_obj
    return render(request, 'interact.html', {
        'username': user.username,
        'email': user.email,
    })
