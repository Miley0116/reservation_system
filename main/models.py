from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re

def validate_phone_number(value):
    """電話番号のバリデーション"""
    # 許可されるパターン
    patterns = [
        r'^\d{2}-\d{4}-\d{4}$',      # 00-0000-0000 (例: 03-1234-5678)
        r'^\d{3}-\d{4}-\d{4}$',      # 000-0000-0000 (例: 090-1234-5678)
        r'^\d{4}-\d{2}-\d{4}$',      # 0000-00-0000 (例: 0123-45-6789)
        r'^0120-\d{3}-\d{3}$',       # 0120-000-000 (例: 0120-123-456)
    ]
    
    for pattern in patterns:
        if re.match(pattern, value):
            return
    
    raise ValidationError('電話番号は「00-0000-0000」「000-0000-0000」「0000-00-0000」「0120-000-000」のいずれかの形式で入力してください')

def validate_image_extension(value):
    """画像ファイルの拡張子をチェック"""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    if ext not in valid_extensions:
        raise ValidationError('画像ファイルはJPG、PNG、PDF形式のみアップロード可能です')
    
def validate_image_size(value):
    """画像ファイルのサイズをチェック（10MB以下）"""
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB
        raise ValidationError('画像ファイルは10MB以下にしてください')

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
    phone_number = models.CharField(max_length=20, unique=True, validators=[validate_phone_number], verbose_name='電話番号')
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
        
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', '予約中'),
        ('completed', '完了'),
        ('cancelled', 'キャンセル'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name='顧客')
    reservation_date = models.DateField(verbose_name='予約日')
    reservation_time = models.TimeField(verbose_name='予約時間')
    service = models.CharField(max_length=200, verbose_name='サービス内容')
    duration = models.IntegerField(default=60, verbose_name='所要時間（分）')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='ステータス')
    memo = models.TextField(blank=True, verbose_name='備考')
    reference_image = models.ImageField(upload_to='reference_images/', blank=True, null=True, validators=[validate_image_extension, validate_image_size], verbose_name='参考画像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        ordering = ['-reservation_date', '-reservation_time']
        verbose_name = '予約'
        verbose_name_plural = '予約'
    
    def __str__(self):
        return f"{self.customer.name} - {self.reservation_date} {self.reservation_time}"
    
# ユーザー権限管理
class UserProfile(models.Model):
    user = models.OneToOneField(Administrator, on_delete=models.CASCADE, related_name='profile')
    
    # 顧客管理権限
    can_edit_customer = models.BooleanField(default=False, verbose_name='顧客編集権限')
    can_delete_customer = models.BooleanField(default=False, verbose_name='顧客削除権限')

    # 予約管理権限
    can_edit_reservation = models.BooleanField(default=False, verbose_name='予約編集権限')
    can_delete_reservation = models.BooleanField(default=False, verbose_name='予約削除権限')
    
    
    class Meta:
        verbose_name = 'ユーザー権限'
        verbose_name_plural = 'ユーザー権限'
    
    def __str__(self):
        return f'{self.user.user.username}の権限'