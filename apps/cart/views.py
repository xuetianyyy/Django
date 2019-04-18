from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from commod.models import CommodSKU
from django_redis import get_redis_connection
import json

# Create your views here.


class CartViews(LoginRequiredMixin, View):
    """ 购物车视图类 """

    def get(self, request):
        """" 购物车内容页显示 """
        user = request.user
        # 获取用户购物车记录
        conn = get_redis_connection("default")
        cart_key = 'cart_{}'.format(user.id)
        cart_all = conn.hgetall(cart_key)

        skus = []  # 返回最终的sku查询列表
        sku_total = 0  # 默认的总计商品价格
        sku_nums = 0   # 统计默认商品总件数
        sku_ids = []  # 前端使用
        for sku_id, car_count in cart_all.items():
            sku = CommodSKU.objects.get(id=int(sku_id))  # 商品信息
            # 动态的添加属性
            sku.amount = sku.price * int(car_count)  # 商品价格*数量, 小计
            sku.count = int(car_count)
            skus.append(sku)
            sku_total += sku.amount     # 商品总价格
            sku_nums += int(car_count)  # 商品总件数
            sku_ids.append(str(sku.id))

        temp_data = {
            'skus': skus,  # 商品信息
            'sku_total': sku_total,
            'sku_nums': sku_nums,
            'sku_ids': json.dumps(sku_ids, ensure_ascii=False),
            # 'sku_ids': sku_ids,
        }

        return render(request, 'cart/cart.html', temp_data)


class CartAddViews(View):
    """ 购物车添加视图类 """

    def post(self, request):
        """ 购物车记录添加 """
        # 接收数据
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据效验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 效验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '添加的商品数目无效'})

        # 效验商品是否存在
        try:
            sku = CommodSKU.objects.get(id=sku_id)
        except CommodSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理: 添加购物车记录
        conn = get_redis_connection("default")
        cart_key = 'cart_{}'.format(user.id)

        # 获取sku_id的值
        cart_count = conn.hget(cart_key, sku_id)
        # 如果该值存在
        if cart_count:
            # 累加购物车中的商品数目
            count += int(cart_count)

        # 效验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足, 请重新选择数量'})

        # 设置hash中对应的值
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车中的商品条目数
        total_count = conn.hlen(cart_key)
        # print(total_count)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


class CartUpdateViews(View):
    """ 购物车记录更新 """

    def post(self, request):
        """ 购物车记录更新 """
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('sku_count')

        # 数据效验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 效验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '添加的商品数目无效'})

        # 效验商品是否存在
        try:
            sku = CommodSKU.objects.get(id=sku_id)
        except CommodSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理: 更新购物车记录
        conn = get_redis_connection("default")
        cart_key = 'cart_{}'.format(user.id)

        # 效验商品库存是否足够
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 设置购物车记录 如果存在则更新, 如果不存在则添加
        conn.hset(cart_key, sku_id, count)

        # 返回应答
        return JsonResponse({'res': 5, 'msg': '操作成功'})


class CartDelViews(View):
    """ 删除购物车商品 """

    def post(self, request):
        """ 删除购物车商品 """
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')

        # 业务处理: 更新购物车记录
        conn = get_redis_connection("default")
        cart_key = 'cart_{}'.format(user.id)

        # 删除记录
        conn.hdel(cart_key, sku_id)

        # 返回应答
        return JsonResponse({'res': 2, 'msg': '删除成功'})
