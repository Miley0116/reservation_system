from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('admin-register/', views.register_view, name='register'),
    path('admin-login/', views.login_view, name='login'),
    path('admin-logout/', views.logout_view, name='logout'),
    path('admin-home/', views.home, name='admin-home'),
    
     # 顧客管理
    path('customers/', views.customer_list, name='customer-list'),
    path('customers/add/', views.customer_add, name='customer-add'),
    path('customers/<int:pk>/', views.customer_detail, name='customer-detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer-edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer-delete'),
]