from django.contrib import admin
from .models import Administrator, Customer, Reservation

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'last_visit_date', 'created_at')
    search_fields = ('name', 'phone_number')
    list_filter = ('last_visit_date', 'created_at')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('get_customer_name', 'reservation_date', 'reservation_time', 'status', 'created_at')
    search_fields = ('user__name', 'guest_name', 'guest_email')
    list_filter = ('status', 'reservation_date', 'created_at')
    
    def get_customer_name(self, obj):
        if obj.user:
            return obj.user.name
        return obj.guest_name
    get_customer_name.short_description = '顧客名'

@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')