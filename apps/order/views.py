from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http import JsonResponse
from commod.models import CommodSKU
from django_redis import get_redis_connection
from user.models import Address
from .models import OrderInfo, OrderCommod
from datetime import datetime
from django.db import IntegrityError, transaction
from alipay import AliPay, ISVAliPay  # 支付宝接口
from django.conf import settings
import os
from django.contrib.auth.mixins import LoginRequiredMixin


class OrderPlaceViews(View):
    """ 订单提交页面显示 """

    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return redirect(reverse('cart:cart'))

        # 获取内容
        sku_ids = request.POST.getlist('sku_ids')
        print(request.POST)
        if not sku_ids:
            return redirect(reverse('cart:cart'))

        # 连接redis
        conn = get_redis_connection('default')
        cart_key = 'cart_{}'.format(user.id)
        skus = []          # 存储所有商品信息
        total_count = 0    # 存储购买商品总件数
        total_price = 0    # 存储购买商品总价格
        for sku_id in sku_ids:
            sku = CommodSKU.objects.get(id=sku_id)  # 获取商品信息
            # 动态的为sku添加两个属性
            sku.count = int(conn.hget(cart_key, sku_id))    # 获取商品购买数量
            sku.amount = sku.price * int(sku.count)             # 统计单个商品价格小计
            total_count += sku.count
            total_price += sku.amount
            skus.append(sku)

        transit_price = 10  # 运费
        total_pay = transit_price + total_price         # 实付款
        user_addrs = Address.objects.filter(user=user)   # 用户收货地址
        default_addr = Address.objects.get(user=user, is_default=1)

        temp_data = {
            'skus': skus,                   # 商品信息列表
            'total_count': total_count,     # 商品总件数
            'total_price': total_price,     # 商品总价格
            'transit_price': transit_price,  # 运费
            'total_pay': total_pay,         # 实付款
            'addrs': user_addrs,            # 用户收货地址
            'default_addr': default_addr.id,  # 用户默认收货地址id
        }

        # print(self.temp_data)

        # 返回响应
        return render(request, 'order/place_order.html', temp_data)


class OrderCommitViews(View):
    """ 提交订单视图 """

    def post(self, request):
        """ 创建订单 """
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请您先登录后访问'})

        # 接收数据
        addr_id = request.POST.get('addr_id')
        pay_way = request.POST.get('pay_way')
        sku_ids = request.POST.getlist('sku_ids[]')

        # 效验参数完整性
        if not all([addr_id, pay_way, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '您提交的数据不完整'})

        # 效验支付方式
        if pay_way not in OrderInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '该支付方式不支持'})

        # 效验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '您提交的地址暂未登记'})

        # 组织参数
        # 订单id: 201904160052+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)  # 格式化时间字符串
        # 订单运费
        transit_price = 10
        # 总数目和总金额
        total_count = 0
        total_price = 0

        # 开启mysql事务管理
        try:
            with transaction.atomic():
                sid = transaction.savepoint()  # 设置一个事务回滚点
                # 向df_order_info表添加订单信息数据
                order = OrderInfo.objects.create(order_id=order_id,
                                                 user=user,
                                                 addr=addr,
                                                 pay_method=pay_way,
                                                 total_count=total_count,
                                                 total_price=total_price,
                                                 transit_price=transit_price,
                                                 # order_status='',   # 支付状态
                                                 # trade_no='',        # 订单编号
                                                 )
                # 连接redis
                conn = get_redis_connection('default')
                cart_key = 'cart_{}'.format(user.id)

                # 用户的订单里有多少商品, 就往df_order_commod添加多少记录
                for sku_id in sku_ids:
                    try:
                        sku = CommodSKU.objects.select_for_update().get(id=sku_id)
                    except Address.DoesNotExist:
                        return JsonResponse({'res': 4, 'errmsg': '您提交的商品不存在'})
                    # 从redis获取用户所要购买的商品数量
                    count = conn.hget(cart_key, sku_id)
                    # 判断商品库存是否足够
                    if int(count) > sku.stock:
                        return JsonResponse({'res': 5, 'errmsg': '非常抱歉, 商品库存不足'})
                    # 向df_order_commod表中添加一条记录
                    OrderCommod.objects.create(order=order,
                                               sku=sku,
                                               count=count,
                                               price=sku.price,
                                               )
                    # 更新商品的库存和销量
                    sku.stock -= int(count)     # 更新库存
                    sku.sales += int(count)     # 更新销量
                    sku.save()
                    # 累加计算订单商品的总数量和总价格
                    total_count += int(count)
                    total_price += (sku.price * int(count))

                # 更新订单表中的商品总数量和总价格
                order.total_count = total_count
                order.total_price = total_price
                order.save()
                # 如果到这里没问题, 就提交事务
                transaction.savepoint_commit(sid)
                # 清除用户购物车中的商品记录
                conn.hdel(cart_key, *sku_ids)   # *sku_ids对列表拆包
                return JsonResponse({'res': 6, 'msg': '订单创建成功'})
        except IntegrityError:
            # 如果出错, 回滚事物
            transaction.savepoint_rollback(sid)
            return JsonResponse({'res': 7, 'errmsg': '非常抱歉, 订单创建失败'})


class OrderPayViews(View):
    """ 订单支付视图类 """

    def post(self, request):
        # 判断用户登录状态
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请登录后操作'})

        # 接收参数
        order_id = request.POST.get('order_id')

        # 效验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单号无效'})
        try:
            # 必须是支付宝支付方式, 且支付状态是未支付
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单异常'})

        # 业务处理: 使用python sdk调用支付宝的支付接口
        # print('当前地址', BASE_DIR)
        app_private_key_path = os.path.join(
            settings.BASE_DIR, 'apps/order/app_private_key.pem')
        alipay_public_key_path = os.path.join(
            settings.BASE_DIR, 'apps/order/alipay_public_key.pem')

        # 接口初始化
        alipay = AliPay(
            appid="2016092600598274",                          # 必选, 这个在沙箱或应用中即可看到
            app_notify_url=None,                               # 可选, 默认回调url
            app_private_key_path=app_private_key_path,     # 必选, 指定本地的公钥, 前面有两种方式定义这个变量
            # 必选, 指定支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=alipay_public_key_path,
            # 可选, RSA 或者 RSA2(支付宝推荐)
            sign_type="RSA2",
            # 可选, 默认False(代表实际项目环境), 如果是支付宝沙箱环境需要改为True
            debug=True,
        )

        # 调用支付接口, 电脑网站支付 alipay.trade.page.pay
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        # 如果是沙箱, 需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        total_pay = order.total_price + order.transit_price     # 订单总价, 订单金额+运费
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=str(order_id),             # 订单编号
            total_amount=str(total_pay),            # 订单金额
            subject='测试订单-{}'.format(order_id),  # 订单标题, 如果是python2需要转为utf-8编码
            return_url=None,                        # 同步回调访问地址, 支付宝的结果返回页面, 如若没有就写None
            # 异步回调访问地址, 支付宝的结果默认以这个为准, 可选, 不填则使用默认notify url
            notify_url=None
        )

        # 返回应答, 返回支付链接
        alipay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': alipay_url})


class OrderPayQueryViews(View):
    """ 订单支付查询视图类 """

    def post(self, request):
        """ 支付查询 """
        # 1. 用户验证
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请登录用户'})

        # 2. 接收数据, 并效验
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '订单号无效'})
        # 效验订单状态, 订单号, 用户, 支付方式, 支付状态
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单无效'})

        # 3. 查询支付: 调用接口
        # 接口初始化
        alipay = AliPay(
            appid="2016092600598274",
            app_notify_url=None,
            app_private_key_path=os.path.join(
                settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            alipay_public_key_path=os.path.join(
                settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",
            debug=True,
        )
        # 调用订单查询接口
        while True:
            # 这个接口是订单查询的api
            response = alipay.api_alipay_trade_query(order_id)
            # 这是返回的数据形式, 在支付宝开发文档中也可以看到
            # response = {
            #     "trade_no": "2017032121001004070200176844",  # 支付宝交易号
            #     "code": "10000",  # 接口调用是否成功
            #     "invoice_amount": "20.00",
            #     "open_id": "20880072506750308812798160715407",
            #     "fund_bill_list": [
            #             {
            #                 "amount": "20.00",
            #                 "fund_channel": "ALIPAYACCOUNT"
            #             }
            #     ],
            #     "buyer_logon_id": "csq***@sandbox.com",
            #     "send_pay_date": "2017-03-21 13:29:17",
            #     "receipt_amount": "20.00",
            #     "out_trade_no": "out_trade_no15",
            #     "buyer_pay_amount": "20.00",
            #     "buyer_user_id": "2088102169481075",
            #     "msg": "Success",
            #     "point_amount": "0.00",
            #     "trade_status": "TRADE_SUCCESS",  # 支付结果
            #     "total_amount": "20.00"
            # }
            code = response.get('code')  # 支付宝的接口调用状态码
            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易单号
                trade_no = response.get('trade_no')
                # 更新订单状态
                order.trade_no = trade_no   # 支付单号
                order.order_status = 4      # 支付状态待评价
                order.save()
                # 返回结果
                return JsonResponse({'res': 100, 'msg': '支付成功'})
            elif code == '40004' or (code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                # 等待买家付款
                # 业务处理失败，可能一会就会成功
                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                print('支付出错状态: ', code)
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class OrderCommentViews(LoginRequiredMixin, View):
    """订单评论"""

    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:user_center_order'))

        try:
            order = OrderInfo.objects.get(
                order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:user_center_order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[
            order.order_status]

        # 获取订单商品信息
        order_skus = OrderCommod.objects.filter(
            order_id=order_id)
        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus = order_skus

        # 使用模板
        return render(request, "order/order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(
                order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get(
                "sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            # cotent_1 content_2 content_3
            content = request.POST.get('content_%d' % i, '')
            try:
                order_commod = OrderCommod.objects.get(
                    order=order, sku_id=sku_id)
            except OrderCommod.DoesNotExist:
                continue

            order_commod.comment = content
            order_commod.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:user_center_order", args=(1,)))
