from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class Customer(models.Model):
    # 電話番号のバリデーター
    phone_regex = RegexValidator(
        regex=r'^0\d{1,4}-?\d{1,4}-?\d{3,4}$',
        message="正しい電話番号形式で入力してください。（例: 090-1234-5678、03-1234-5678、0120-123-456）"
    )
    
    name = models.CharField(max_length=100, verbose_name="顧客名")
    phone_number = models.CharField(
        max_length=20, 
        verbose_name="電話番号",
        validators=[phone_regex]
    )
    email = models.EmailField(unique=True, verbose_name="メールアドレス")  # 追加
    memo = models.TextField(blank=True, verbose_name="メモ")
    last_visit_date = models.DateField(null=True, blank=True, verbose_name="最終来店日")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "顧客"
        verbose_name_plural = "顧客"
        
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', '予約中'),
        ('completed', '完了'),
        ('cancelled', 'キャンセル'),
    ]
    
    user = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="顧客")
    reservation_date = models.DateField(verbose_name="予約日")
    reservation_time = models.TimeField(verbose_name="予約時間")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="ステータス")
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="ゲスト名")
    guest_email = models.EmailField(blank=True, verbose_name="ゲストメール")
    notes = models.TextField(blank=True, verbose_name="備考")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    def __str__(self):
        if self.user:
            return f"{self.user.name} - {self.reservation_date}"
        return f"{self.guest_name} - {self.reservation_date}"

    class Meta:
        verbose_name = "予約"
        verbose_name_plural = "予約"