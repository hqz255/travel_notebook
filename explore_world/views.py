from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from record_memories.models import Article, ArticleCategory, Comment
from the_root.decorators import login_required


@login_required
def explore_world(request):
    """探索世界 — 展示所有已发布的文章"""
    user = request.user_obj

    articles = (
        Article.objects
        .select_related('author')
        .prefetch_related('categories')
        .annotate(comment_count=Count('comments'))
        .order_by('-created_at')
    )

    return render(request, 'explore_world.html', {
        'username': user.username,
        'email': user.email,
        'articles': articles,
    })


@login_required
def article_detail(request, article_id):
    """文章详情页"""
    user = request.user_obj

    article = get_object_or_404(
        Article.objects
        .select_related('author')
        .prefetch_related('categories'),
        id=article_id,
    )


    # 非作者访问时增加浏览量
    if article.author_id != user.id:
        article.views_count += 1
        article.save(update_fields=['views_count'])

    # 获取顶级评论及其回复
    comments = (
        Comment.objects
        .filter(article=article, parent__isnull=True)
        .select_related('author')
        .prefetch_related('replies__author')
        .order_by('-created_at')
    )

    return render(request, 'article_details.html', {
        'username': user.username,
        'email': user.email,
        'current_user_id': user.id,
        'is_superuser': user.superuser,
        'article': article,
        'comments': comments,
    })


@login_required
@require_http_methods(['POST'])
def post_comment(request, article_id):
    """提交评论或回复（AJAX）"""
    user = request.user_obj

    article = get_object_or_404(Article, id=article_id)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': '评论内容不能为空。'})

    if len(content) > 2000:
        return JsonResponse({'success': False, 'error': '评论内容不能超过2000字。'})

    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id:
        parent = get_object_or_404(Comment.objects.filter(article=article), id=parent_id)

    comment = Comment.objects.create(
        article=article,
        author=user,
        content=content,
        parent=parent,
    )

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'author': comment.author.username,
            'author_initial': comment.author.username[0].upper(),
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            'parent_id': parent.id if parent else None,
            'parent_author': parent.author.username if parent else None,
        },
    })


@login_required
def get_comments(request, article_id):
    """获取文章评论列表（AJAX）"""
    user = request.user_obj

    article = get_object_or_404(Article, id=article_id)

    comments = (
        Comment.objects
        .filter(article=article, parent__isnull=True)
        .select_related('author')
        .prefetch_related('replies__author')
        .order_by('-created_at')
    )

    def serialize_comment(c):
        return {
            'id': c.id,
            'author': c.author.username,
            'author_id': c.author_id,
            'author_initial': c.author.username[0].upper(),
            'content': c.content,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
            'replies': [serialize_comment(r) for r in c.replies.all()],
        }

    return JsonResponse({
        'success': True,
        'comments': [serialize_comment(c) for c in comments],
    })


@login_required
@require_http_methods(['POST'])
def delete_comment(request, comment_id):
    """删除评论或回复（AJAX）—— 作者本人或超级用户可删除"""
    user = request.user_obj

    comment = get_object_or_404(Comment, id=comment_id)

    # 校验：评论作者本人或超级用户可以删除
    if comment.author_id != user.id and not user.superuser:
        return JsonResponse({'success': False, 'error': '你只能删除自己的评论。'}, status=403)

    # 获取所属文章 ID，用于后续校验（可选）
    article_id = comment.article_id

    comment.delete()

    return JsonResponse({
        'success': True,
        'article_id': article_id,
    })


@login_required
def search_articles(request):
    """搜索文章 — 按标题、内容、分类检索"""
    user = request.user_obj
    query = request.GET.get('q', '').strip()

    results = []
    if query:
        results = (
            Article.objects
            .select_related('author')
            .prefetch_related('categories')
            .annotate(comment_count=Count('comments'))
            .filter(
                Q(title__icontains=query)
                | Q(content__icontains=query)
                | Q(categories__name__icontains=query)
            )
            .distinct()
            .order_by('-created_at')
        )

    return render(request, 'search_results.html', {
        'username': user.username,
        'email': user.email,
        'search_query': query,
        'articles': results,
        'results_count': len(results),
    })
