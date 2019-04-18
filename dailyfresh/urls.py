"""dailyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 富文本编辑器路由
    re_path(r'^tinymce/', include('tinymce.urls')),  # 以tinymce/开头的所有路径
    # 应用路由, namespace指定反向解析匹配名称
    re_path(r'^user/', include('user.urls', namespace='user')),
    re_path(r'^cart/', include('cart.urls', namespace='cart')),
    re_path(r'^order/', include('order.urls', namespace='order')),
    # 此路由包含首页, 所以只匹配开头, 放在最后, 是防止它匹配到其它模块的路由
    re_path(r'^', include('commod.urls', namespace='commod')),
    # 搜索引擎提交的路由, 全文检索框架
    path('search', include('haystack.urls')),
]
