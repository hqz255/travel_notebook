from django.shortcuts import render
from the_root.decorators import login_required


@login_required
def travel_footprint(request):
    """旅行足迹"""
    user = request.user_obj
    return render(request, 'travel_footprint.html', {
        'username': user.username,
        'email': user.email,
    })
