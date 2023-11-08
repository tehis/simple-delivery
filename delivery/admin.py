from django.contrib import admin
from delivery.models import Agent, Order, Trip, Vendor, DelayQueue, DelayReport


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'created_at', 'delivery_time')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('order', 'status')


@admin.register(DelayQueue)
class DelayAdmin(admin.ModelAdmin):
    list_display = ('report', 'agent', 'status', 'created_at')


@admin.register(DelayReport)
class DelayReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'vendor', 'delay', 'created_at')
    fields = ('order', 'delay', 'created_at')

    @admin.display(ordering='order__vendor', description='Vendor')
    def vendor(self, obj):
        return obj.order.vendor


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

