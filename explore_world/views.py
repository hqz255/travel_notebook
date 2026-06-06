from django.shortcuts import render
from record_memories.models import Article
from the_root.decorators import login_required


@login_required
def explore_world(request):
    """探索世界 — 展示所有已发布的文章"""
    user = request.user_obj

    articles = (
        Article.objects
        .filter(status='published')
        .select_related('author')
        .prefetch_related('categories')
        .order_by('-created_at')
    )

    return render(request, 'explore_world.html', {
        'username': user.username,
        'email': user.email,
        'articles': articles,
    })
