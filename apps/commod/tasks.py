from __future__ import absolute_import, unicode_literals
from celery import shared_task  # celery装饰器
from django_redis import get_redis_connection
from django.template import loader, RequestContext
from django.conf import settings
import os
from .models import CommodType, IndexPromotionBanner, IndexTypeCommodBanner, IndexCommodBanner


@shared_task
def generate_start_index_html():
    """ 产生首页静态页面 """
    # 获取商品的种类信息
    types = CommodType.objects.all()

    # 获取首页轮播商品信息
    commod_banners = IndexCommodBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeCommodBanner.objects.filter(
            type=type, display_type=1).order_by('index')
        # 获取type种类首页分类以商品的文字展示信息
        title_banners = IndexTypeCommodBanner.objects.filter(
            type=type, display_type=1).order_by('index')

        # 动态给type增加属性, 分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 模板数据
    temp_data = {
        'types': types,
        'commod_banners': commod_banners,
        'promotion_banners': promotion_banners,
    }

    # 使用模板
    # 1. 加载模板文件
    # temp = loader.get_template('baseTemp/static_index.html')
    temp = loader.get_template('commod/index.html')
    # # 2. 定义模板上下文
    # context = RequestContext(request, context)
    # 3. 模板渲染
    static_index_html = temp.render(temp_data)

    # 生成首页静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/html/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
