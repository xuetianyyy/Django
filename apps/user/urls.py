from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.auth.decorators import login_required
# from user.views import *
from user import views

app_name = 'user'  # 指定应用名
urlpatterns = [
    # 注册页面
    path('register', views.RegisterViews.as_view(), name='register'),
    # 登录页面
    path('login', views.LoginViews.as_view(), name='login'),
    # 用户中心页
    path('user_center_info', views.UserCenterInfoViews.as_view(),
         name='user_center_info'),
    # 用户订单页,
    path('user_center_order/<int:page_num>', views.UserCenterOrderViews.as_view(),
         name='user_center_order'),
    # 用户地址详情页
    path('user_center_site', views.UserCenterSiteViews.as_view(),
         name='user_center_site'),
    # 用户退出登录视图
    path('logout', views.LoginOutViews.as_view(), name='logout'),
]
