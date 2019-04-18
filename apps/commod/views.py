from django.shortcuts import render, redirect
from django.views import View
from django.core.cache import cache
from django_redis import get_redis_connection
from django.conf import settings
import os
from .models import *
from order.models import OrderCommod
from django.urls import reverse
from django.core.paginator import Paginator
# Create your views here.


class IndexViews(View):
    """ 首页视图类 """

    def get(self, request):
        """ 显示首页 """
        temp_data = cache.get('index_page_data')  # 尝试读取缓存
        if temp_data is None:
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

            temp_data = {
                'types': types,
                'commod_banners': commod_banners,
                'promotion_banners': promotion_banners,
                'cart_count': 1,
            }

            # 设置缓存
            cache.set('index_page_data', temp_data, 3600)

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已经登录
            conn = get_redis_connection('default')  # 连接redis
            cart_key = 'cart_{}'.format(user.id)    # 凭借hash的键名
            cart_count = conn.hlen(cart_key)        # 获取该键里的数据数目

        # 添加cart_cout数据
        temp_data.update(cart_count=cart_count)
        temp_data['cart_count'] = cart_count
        # print(temp_data['cart_count'])

        return render(request, 'commod/index.html', temp_data)


class DetailViews(View):
    """ 商品详情页视图类 """

    def get(self, request, sku_id):
        """ 返回商品详情页 """
        try:
            sku = CommodSKU.objects.get(id=sku_id)
        except CommodSKU.DoesNotExist:
            # 商品不存在
            return redirect(reverse('commod:index'))

        # 获取商品的分类信息
        types = CommodType.objects.all()

        # 获取商品的评论信息
        sku_orders = OrderCommod.objects.filter(sku=sku).exclude(comment='')

        # print('哈哈', sku_orders[0].comment)
        # print(sku_orders.comment)

        # 获取新品信息
        new_skus = CommodSKU.objects.filter(
            ctype=sku.ctype).order_by('-create_time')[:2]  # 根据创建时间降序排序两条数据

        # 获取同一个SPU的其他规格商品
        same_spu_skus = CommodSKU.objects.filter(
            commod=sku.commod).exclude(id=sku_id)   # 排除默认展示规格的商品信息

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_{}'.format(user.id)
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史记录
            conn = get_redis_connection('default')  # 获取redis连接实例
            history_key = 'history_{}'.format(user.id)
            # 移除列表中的sku_id
            conn.lrem(history_key, 0, sku_id)
            # 把sku_id插入到列表的左侧
            conn.lpush(history_key, sku_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)

        # 组织模板上下文
        temp_data = {
            'sku': sku,         # CommodSKU
            'types': types,     # CommodType
            'sku_orders': sku_orders,  # OrderCommod
            'new_skus': new_skus,  # CommodSKU 最新上架的两个商品
            'same_spu_skus': same_spu_skus,  # CommodSKU
            'cart_count': cart_count,
        }

        # 使用模板
        return render(request, 'commod/detail.html', temp_data)


class DetailListViews(View):
    """ 查看更多-商品列表页 """

    def get(self, request, type_id, page_num):
        # def get(self, request, type_id):
        """
        展示商品列表页面
        :param type_id: 商品种类
        :page_num: 当前的页码
        """
        # print(type_id)
        # print(page_num)
        # type_id = 4
        # page_num = 1
        try:
            # 获取用户请求的商品种类信息
            ctype = CommodType.objects.get(id=type_id)
        except CommodType.DoesNotExist:
            # 如果商品种类不存在, 跳转首页
            return redirect(reverse('commod:index'))
        # 获取商品种类的所有信息
        types = CommodType.objects.all()

        sort = request.GET.get('sort')  # 获取用户请求商品列表排序方式
        # 根据前端用户请求的商品排序方式, 来获取对应分类的商品信息
        if sort == 'price':
            # 如果是按照价格进行排序, 价格升序排列
            skus = CommodSKU.objects.filter(ctype=ctype).order_by('price')
        elif sort == 'sales':
            # 如果按照销量进行排序, 销量从高到底, 降序
            skus = CommodSKU.objects.filter(ctype=ctype).order_by('-sales')
        else:
            # 其它都以默认的排序方式, 按照id进行排序(降序)
            sort = 'default'
            skus = CommodSKU.objects.filter(ctype=ctype).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 1)       # 获取分页的查询集, 并指定每页展示1条数据
        page_num = int(page_num) if page_num != '' else 1
        sku_page = paginator.get_page(page_num)  # 获取当前选中的分页码数据集
        page_len = paginator.num_pages   # 页码总数
        if page_num <= 5:
            page_list = paginator.page_range[0:5]
        elif (page_len - page_num) < 5:
            page_list = paginator.page_range[-5:]
        else:
            page_list = paginator.page_range[page_num - 3:page_num + 2]

        # print(page_list)

        # 获取新品信息
        new_skus = CommodSKU.objects.filter(
            ctype=ctype).order_by('-create_time')[:2]  # 根据创建时间降序排序两条数据

        # 获取用户购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_{}'.format(user.id)
            cart_count = conn.hlen(cart_key)

        # 模板数据
        temp_data = {
            'ctype': ctype,        # 当前的商品种类信息
            'types': types,        # 所有商品种类信息
            'pages': sku_page,         # 当前页码Page对象
            'new_skus': new_skus,  # 最新上架的商品信息
            'cart_count': cart_count,  # 购物车信息
            'sort': sort,          # 用于上下一页, 默认使用使用的sort
            'page_list': page_list,  # 页码列表
        }
        # 使用模板
        return render(request, 'commod/list.html', temp_data)
