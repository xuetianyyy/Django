from django.contrib import admin
from django.urls import path, re_path, include
from commod.views import *

app_name = 'commod'  # 指定应用名
urlpatterns = [
    # 首页路由
    path('', IndexViews.as_view(), name='index'),
    # 商品列表
    path('commod/detail/<int:sku_id>', DetailViews.as_view(), name='detail'),
    # 商品列表页
    # 查看更多->商品列表页
    path('commod/detail_list/<int:type_id>/<int:page_num>',
         DetailListViews.as_view(), name='detail_list'),
]
