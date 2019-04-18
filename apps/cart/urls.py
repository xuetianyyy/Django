from django.contrib import admin
from django.urls import path, re_path, include
from cart.views import CartViews, CartAddViews, CartUpdateViews, CartDelViews
from django.contrib.auth.decorators import login_required

app_name = 'cart'  # 指定应用名
urlpatterns = [
    # 购物车页面
    path('cart', CartViews.as_view(), name="cart"),
    # 购物车添加视图
    path('cart_add', CartAddViews.as_view(), name='cart_add'),
    # 购物车记录更新
    path('cart_update', CartUpdateViews.as_view(), name='update'),
    # 删除购物车记录
    path('cart_del', CartDelViews.as_view(), name='cart_del'),
]
