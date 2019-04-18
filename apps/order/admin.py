from django.contrib import admin
from .models import OrderInfo, OrderCommod

# Register your models here.


class OrderInfoAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'addr',
                    'pay_method', 'total_count', 'total_price', 'transit_price', 'order_status', 'trade_no']


class OrderCommodAdmin(admin.ModelAdmin):
    list_display = ['order', 'sku', 'count', 'price', 'comment']

admin.site.register(OrderInfo, OrderInfoAdmin)
admin.site.register(OrderCommod, OrderCommodAdmin)
