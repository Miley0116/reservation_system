from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('admin-register/', views.register_view, name='register'),
    path('admin-login/', views.login_view, name='login'),
    path('admin-logout/', views.logout_view, name='logout'),
    path('admin-home/', views.home, name='admin-home'),
    
    # 顧客管理
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    
    # 予約管理
    path('reservation/', views.reservation_list, name='reservation_list'),
    path('reservation/add/', views.reservation_add, name='reservation_add'),
    path('reservation/edit/<int:pk>/', views.reservation_edit, name='reservation_edit'),
    path('reservation/delete/<int:pk>/', views.reservation_delete, name='reservation_delete'),
    
    # カレンダー（ここに追加）
    path('reservation/calendar/', views.reservation_calendar, name='reservation_calendar'),
    path('reservation/calendar/data/', views.reservation_calendar_data, name='reservation_calendar_data'),
]