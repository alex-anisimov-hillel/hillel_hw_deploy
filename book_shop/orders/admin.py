from django.contrib import admin

from orders.models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.StackedInline):
    model = OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]


# admin.site.register(Order)
# admin.site.register(OrderItem)
