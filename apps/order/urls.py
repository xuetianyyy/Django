from django.contrib import admin
from django.urls import path, re_path, include
from .views import *

app_name = 'order'  # 指定应用名
urlpatterns = [
    # 订单支付页面显示
    path('order_place', OrderPlaceViews.as_view(), name='order_place'),
    # 订单支付提交
    path('commit', OrderCommitViews.as_view(), name='commit'),
    # 支付接口视图
    path('order_pay', OrderPayViews.as_view(), name='pay'),
    # 支付状态查询
    path('pay_query', OrderPayQueryViews.as_view(), name="pay_query"),
    # 订单评论
    path('order_comment/<int:order_id>',
         OrderCommentViews.as_view(), name='comment'),
]
