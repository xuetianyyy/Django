from django.contrib import admin
from commod.models import *
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    """ 这是一个触发生成静态页面任务的模型管理基类, 用于给其它的模型类继承 """

    def save_model(self, request, obj, form, change):
        """ 当这个模型类表中的数据发生变化时自动触发 """
        # obj.user = request.user
        super().save_model(request, obj, form, change)

        # 发出任务, 让Celery重新生成首页静态页
        from .tasks import generate_start_index_html
        generate_start_index_html.delay()   # 调用celery worker任务

    def delete_model(self, request, obj):
        """ 当这个模型类表中的数据被删除时自动触发 """
        # obj.user = request.user
        super().delete_model(request, obj)

        # 发出任务, 让Celery重新生成首页静态页
        from .tasks import generate_start_index_html
        generate_start_index_html.delay()   # 调用celery worker任务


class CommodTypeAdmin(BaseModelAdmin):
    '''商品类型模型类'''
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    '''首页促销活动模型类'''
    pass


class IndexCommodBannerAdmin(BaseModelAdmin):
    """ 首页轮播商品展示模型类 """
    pass


class IndexTypeCommodBannerAdmin(BaseModelAdmin):
    '''首页分类商品展示模型类'''
    pass


class CommodSKUAdmin(BaseModelAdmin):
    '''首页分类商品展示模型类'''
    pass

# 在后台注册模型类
admin.site.register(CommodType, CommodTypeAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexCommodBanner, IndexCommodBannerAdmin)
admin.site.register(IndexTypeCommodBanner, IndexTypeCommodBannerAdmin)
admin.site.register(CommodSKU, CommodSKUAdmin)
admin.site.register(Commod)
admin.site.register(CommodImage)
