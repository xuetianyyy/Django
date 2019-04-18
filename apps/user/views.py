from django.shortcuts import render, redirect
from django.views import View
from user.models import User, Address
from itsdangerous import TimedJSONWebSignatureSerializer as TjSerializer
from django.core.mail import send_mail
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
import re
from django_redis import get_redis_connection       # Django使用redis原声客户端的方法
from commod.models import CommodSKU
# from celery_tasks.tasks import send_register_active_email
from .tasks import send_register_active_email
from order.models import OrderInfo, OrderCommod
from django.core.paginator import Paginator

# Create your views here.


class RegisterViews(View):
    """ 注册视图类 """

    def get(self, request, *args, **kwargs):
        """ 处理get请求 """
        # 显示注册页面
        # request.META["CSRF_COOKIE_USED"] = True
        return render(request, 'user/register.html')

    def post(self, request, *args, **kwargs):
        """ 处理post请求 """
        # 进行注册处理
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.getlist('allow[]')[0]

        # 判断用户是否存在
        try:
            user = User.objects.get(username=username)
            # email = User.objects.get(email=email)
        except User.DoesNotExist:
            # 用户不存在
            user = None

        if user:
            # 如果用户存在, 直接返回信息
            return JsonResponse({'ifuser': True, 'ifemail': False})
        else:
            # 如果用户不存在检查邮箱是否存在
            try:
                user_email = User.objects.get(email=email)
            except User.DoesNotExist:
                # 邮箱不存在
                user_email = None

            if user_email:
                return JsonResponse({'ifuser': False, 'ifemail': True})

        # # 进行业务处理: 进行用户注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # user_id = User.objects.get(username=username)
        # print(user.id, 'haha')

        # 加密签名
        s = TjSerializer(settings.SECRET_KEY, 600)
        # 3. 加密数据
        info = {'user_id': user.id}
        # 加密数据为: data对象, 并对其加盐'xuetian'
        token = s.dumps(info, salt='xuetian').decode()
        # 解密
        # load_data = s.loads(token, salt='xuetian')

        # 发送激活邮件, 包含激活链接:
        send_register_active_email.delay(email, username, token)

        # 返回应答, 跳转到首页
        # return redirect(reverse('commod:index'))
        return JsonResponse({'iflogin': True})


class LoginViews(View):
    """ 登录视图类 """

    def get(self, request, *args, **kwargs):
        """ 显示登录页面 """
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        # 使用模板
        return render(request, 'user/login.html', {'username': username, 'checked': checked})

    def post(self, request, *args, **kwargs):
        """ 登录效验 """
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 效验数据
        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})

        # 业务处理, 登录效验
        user = authenticate(request, username=username, password=password)
        # print(user)
        if user is not None:
            request.session.set_expiry(0)
            # 用户名密码正确, 登录成功
            login(request, user)

            # 获取用户登录后要跳转的地址, 这可能是当用户未登录时访问某个页面, 被阻止的状态, 我么可以通过next参数获取它之前想访问的地址
            # 如果之前没有被阻止过, 而是直接访问的这个页面, 那么next参数是没有值的, 此时就指定首页的默认值
            next_url = request.GET.get('next', reverse('commod:index'))
            # 此时, 如果next中有值, 就会跳转到next参数中的地址中, 如果没有值, 则跳转到上面的默认值到首页
            response = redirect(next_url)

            # 判断是否需要记住用户名
            remember = request.POST.get('remember')

            if remember == 'on':
                # 记住用户名
                response.set_cookie(
                    'username', value=username, max_age=7 * 24 * 3600)
            else:
                response.delete_cookie('username')

            # 跳转到首页
            return response

        else:
            # 登录失败
            return render(request, 'user/login.html', {'errmsg': '用户名或密码错误'})

        #


class LoginOutViews(View):
    """ 退出登录的视图 """

    def get(self, request):
        # 清除用户登录
        logout(request)
        # 跳转到首页
        return redirect(reverse('commod:index'))


class UserCenterInfoViews(LoginRequiredMixin, View):
    """ 用户中心视图 """

    def get(self, request):
        # 获取用户对象
        user = request.user
        # 获取用户默认地址
        address = Address.objects.get_default_addr(user)

        # 获取用户的历史浏览记录
        con = get_redis_connection('default')
        # 设置存储的key, 以history_为前缀的id键名
        history_key = 'history_{}'.format(user.id)
        # 获取用户最近浏览的五条商品信息
        sku_ids = con.lrange(history_key, 0, 4)

        # 从数据库中查询用户浏览的商品具体信息
        commod_li = CommodSKU.objects.filter(
            id__in=sku_ids)  # 这样获取到的数据顺序, 可能与sku_ids中查询的浏览记录顺序不一致

        # 我们需要重新排列顺序
        commod_li = [
            commod for sku in sku_ids for commod in commod_li if commod.id == int(sku.decode())]

        # 传递给模板的数据
        temp_data = {
            'page': 'info',
            'address': address,
            'commod_li': commod_li,
        }

        return render(request, 'user/user_center_info.html', temp_data)


class UserCenterOrderViews(LoginRequiredMixin, View):
    """ 用户订单视图 """

    def get(self, request, page_num):
        user = request.user
        orders = OrderInfo.objects.filter(user=user)

        # 遍历获取订单商品的信息
        for order in orders:
            order_skus = OrderCommod.objects.filter(order_id=order.order_id)
            # 遍历商品列表, 得到订单商品小计, 并动态的添加属性给商品对象
            for order_sku in order_skus:
                order_sku.total_price = order_sku.count * order_sku.price
            # 动态的给order添加属性, 保存订单商品信息
            order.order_skus = order_skus
            # 动态添加一个支付状态属性
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态添加是属性, 订单总价, 订单价格+运费
            order.amount_price = order.total_price + order.transit_price

        # 分页
        paginator = Paginator(orders, 10)
        page_num = int(page_num) if page_num != '' else 1
        order_page = paginator.get_page(page_num)  # 获取当前选中的分页码数据集
        page_len = paginator.num_pages   # 页码总数
        # 只显示5页
        if page_num <= 5:
            page_list = paginator.page_range[0:5]
        elif (page_len - page_num) < 5:
            page_list = paginator.page_range[-5:]
        else:
            page_list = paginator.page_range[page_num - 3:page_num + 2]

        # 模板数据
        temp_data = {
            'order_page': order_page,
            'order_list': page_list,
            'page': 'order',
        }

        return render(request, 'user/user_center_order.html', temp_data)


class UserCenterSiteViews(LoginRequiredMixin, View):
    """ 用户地址详情页视图 """

    def get(self, request):
        user = request.user   # 获取用户查询对象
        # 使用自定义模型管理器判断用户是否存在默认收货地址
        address = Address.objects.get_default_addr(user)
        return render(request, 'user/user_center_site.html', {'page': 'site', 'address': address})

    def post(self, request):
        """ 地址信息的添加 """
        # 1. 接收收据
        receiver = request.POST.get('receiver')     # 收件人
        addr = request.POST.get('addr')             # 收货地址
        zip_code = request.POST.get('zip_code')     # 邮编
        phone = request.POST.get('phone')           # 手机

        # 2. 效验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '数据不完整'})
        # 2.1 效验手机号
        if not re.match(r'^1[3-9][0-9]{9}$', phone):
            return render(request, 'user/user_center_site.html', {'errmsg': '手机号不合法'})

        # 3. 业务处理: 地址添加
        user = request.user   # 获取用户查询对象
        # 使用自定义模型管理器判断用户是否存在默认收货地址
        address = Address.objects.get_default_addr(user)
        if address:
            is_default = False  # 如果用户已存在默认收货地址, 添加的地址将不作为默认收货地址
        else:
            is_default = True   # 否则将作为默认收货地址

        # 3.1 添加地址
        Address.objects.create(
            user=user,
            receiver=receiver,
            addr=addr,
            zip_code=zip_code,
            phone=phone,
            is_default=is_default
        )

        # 4. 返回应答
        return redirect(reverse('user:user_center_site'))
