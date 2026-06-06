import os
import uuid
from django.shortcuts import render
from django.conf import settings
from register.models import User
from record_memories.models import Article, ArticleCategory
from the_root.decorators import login_required

# ---------------------------------------------------------------------------
# 图片上传安全配置
# ---------------------------------------------------------------------------

# 允许的图片文件扩展名（白名单）
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

# 单张图片最大体积：10 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# 尝试导入 PIL/Pillow（可选依赖，用于深度图片验证）
try:
    from PIL import Image as PILImage
    _PIL_AVAILABLE = True
except ImportError:
    PILImage = None
    _PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# 图片文件头魔数映射表
# 用于检测文件真实类型，不依赖浏览器提供的 content_type / MIME
# ---------------------------------------------------------------------------

# 每种格式对应的魔数字节前缀
_IMAGE_MAGIC_SIGNATURES = [
    (b'\xff\xd8\xff', '.jpg'),           # JPEG: FF D8 FF
    (b'\x89PNG\r\n\x1a\n', '.png'),      # PNG
    (b'RIFF', '.webp'),                  # WebP (需额外校验 WEBP 标记)
    (b'GIF87a', '.gif'),                 # GIF87a
    (b'GIF89a', '.gif'),                 # GIF89a
    (b'BM', '.bmp'),                     # BMP
    (b'\x00\x00\x01\x00', '.ico'),       # ICO (仅用于检测，不在白名单内)
]


def _detect_extension_by_magic(header: bytes) -> str | None:
    """通过文件头魔数检测图片真实类型，返回扩展名（如 '.jpg'）或 None。"""
    for magic, ext in _IMAGE_MAGIC_SIGNATURES:
        if header[:len(magic)] == magic:
            # WebP 特殊处理：RIFF 容器内需要确认 WEBP 标识
            if ext == '.webp' and header[8:12] != b'WEBP':
                continue
            return ext
    return None


def _is_valid_image(uploaded_file):
    """验证上传文件是否为真实有效的图片（多层纵深校验）。

    返回 (is_valid: bool, error_message: str)

    校验流程（按顺序，任一失败立即拒绝）：
    1. 文件大小检查 — 防止上传超大文件耗尽磁盘
    2. 扩展名白名单检查 — 第一道过滤
    3. 文件头魔数检测 — 判断文件真实类型，不信任浏览器 MIME
    4. PIL/Pillow 内容完整性验证 — 确认图片可正常解码
    """
    # ---------- 1. 文件大小检查 ----------
    if uploaded_file.size > MAX_IMAGE_SIZE:
        size_mb = uploaded_file.size / (1024 * 1024)
        max_mb = MAX_IMAGE_SIZE / (1024 * 1024)
        return False, f"图片「{uploaded_file.name}」大小为 {size_mb:.1f} MB，超过限制（最大 {max_mb:.0f} MB）"

    if uploaded_file.size == 0:
        return False, f"图片「{uploaded_file.name}」是空文件"

    # ---------- 2. 扩展名白名单检查 ----------
    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"不支持的文件格式「{ext}」，请上传 JPG / PNG / WEBP / GIF / BMP 格式的图片"

    # ---------- 3. 文件头魔数检测 ----------
    uploaded_file.seek(0)
    header = uploaded_file.read(16)  # 读取前 16 字节足够覆盖所有常见格式
    uploaded_file.seek(0)

    detected_ext = _detect_extension_by_magic(header)
    if detected_ext is None:
        return False, f"「{uploaded_file.name}」的文件内容不是有效的图片格式（无法识别文件头）"

    if detected_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"「{uploaded_file.name}」真实类型为 {detected_ext}，不在允许的格式列表中"

    # ---------- 4. PIL/Pillow 内容完整性验证 ----------
    if _PIL_AVAILABLE:
        try:
            uploaded_file.seek(0)
            img = PILImage.open(uploaded_file)
            img.verify()  # 校验图片数据结构完整性
            uploaded_file.seek(0)
        except Exception:
            uploaded_file.seek(0)
            return False, f"「{uploaded_file.name}」图片文件已损坏或内容无效"
    # PIL 未安装时跳过深度验证（魔数检测已提供基本保障）

    return True, ""


def _get_active_categories():
    """获取当前启用的分类列表，以字典列表形式返回，方便模板使用。"""
    return list(
        ArticleCategory.objects.filter(is_active=True)
        .values('id', 'name', 'slug')
        .order_by('display_order', 'id')
    )


@login_required
def wmmr(request):
    """我的每日 — 发布页面

    GET:  渲染发布表单
    POST: 处理文章发布/保存草稿
    """
    user = request.user_obj

    # 获取所有启用的分类供模板渲染
    active_categories = _get_active_categories()

    context = {
        'username': user.username,
        'email': user.email,
        'categories': active_categories,
        'error': '',
        'success': '',
        'form_data': {},  # 保留已填写的表单数据
    }

    # 处理 POST 发布请求
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_ids_raw = request.POST.get('category_ids', '').strip()
        content = request.POST.get('content', '').strip()
        action = request.POST.get('action', 'publish').strip()
        uploaded_images = request.FILES.getlist('images')

        # 解析多选分类 ID
        selected_category_ids = []
        if category_ids_raw:
            try:
                selected_category_ids = [
                    int(cid.strip())
                    for cid in category_ids_raw.split(',')
                    if cid.strip()
                ]
            except ValueError:
                context['error'] = '无效的文章分类'
                return render(request, 'wmmr.html', context)

        # 校验分类 ID 是否合法（必须存在于数据库且为启用状态）
        if selected_category_ids:
            valid_category_ids = set(
                ArticleCategory.objects.filter(
                    id__in=selected_category_ids,
                    is_active=True,
                ).values_list('id', flat=True)
            )
            invalid_ids = set(selected_category_ids) - valid_category_ids
            if invalid_ids:
                context['error'] = f'包含无效的文章分类'
                return render(request, 'wmmr.html', context)
        else:
            context['error'] = '请至少选择一个文章分类'
            return render(request, 'wmmr.html', context)

        # 保存表单数据以便出错时回填
        context['form_data'] = {
            'title': title,
            'category_ids': category_ids_raw,
            'content': content,
        }

        # 标题和内容必填校验
        if not title:
            context['error'] = '请输入文章标题'
            return render(request, 'wmmr.html', context)
        if not content:
            context['error'] = '请输入文章内容'
            return render(request, 'wmmr.html', context)

        # 图片数量上限校验
        MAX_IMAGES = 9
        if len(uploaded_images) > MAX_IMAGES:
            context['error'] = f'最多只能上传 {MAX_IMAGES} 张图片，你选择了 {len(uploaded_images)} 张'
            return render(request, 'wmmr.html', context)

        # 逐张图片校验并保存
        saved_image_paths = []
        if uploaded_images:
            upload_dir = settings.MEDIA_ROOT / 'uploads'
            upload_dir.mkdir(parents=True, exist_ok=True)

            for img_file in uploaded_images:
                is_valid, err_msg = _is_valid_image(img_file)
                if not is_valid:
                    context['error'] = err_msg  # _is_valid_image 已包含文件名
                    return render(request, 'wmmr.html', context)

                # 生成唯一文件名并保存
                _, ext = os.path.splitext(img_file.name)
                unique_name = f"{uuid.uuid4().hex}{ext.lower()}"
                file_path = upload_dir / unique_name

                with open(file_path, 'wb+') as dest:
                    for chunk in img_file.chunks():
                        dest.write(chunk)

                saved_image_paths.append(f"uploads/{unique_name}")

        # 保存文章到数据库
        is_draft = (action == 'draft')
        status = 'draft' if is_draft else 'published'

        article = Article.objects.create(
            title=title,
            content=content,
            author=user,
            status=status,
            images=saved_image_paths,
        )
        # 关联分类
        article.categories.set(selected_category_ids)

        # 构建成功消息
        image_count = len(saved_image_paths)
        if is_draft:
            context['success'] = (
                f'📝 草稿保存成功！'
                + (f' 共保存 {image_count} 张图片' if image_count else '')
                + ' 可在「我的回忆」中继续编辑。'
            )
        else:
            context['success'] = (
                f'🎉 文章发布成功！'
                + (f' 共上传 {image_count} 张图片' if image_count else '')
            )

        context['form_data'] = {}  # 清空表单
        return render(request, 'wmmr.html', context)

    return render(request, 'wmmr.html', context)
