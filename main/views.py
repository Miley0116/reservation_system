from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Administrator, Customer

def welcome(request):
    """Welcomeページ"""
    return render(request, 'main/welcome.html')

def register_view(request):
    """管理者登録"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # パスワード一致確認
        if password1 != password2:
            messages.error(request, 'パスワードが一致しません')
            return render(request, 'main/register.html')
        
        # ユーザー名の重複確認
        if User.objects.filter(username=username).exists():
            messages.error(request, 'このユーザー名は既に使用されています')
            return render(request, 'main/register.html')
        
        # メールアドレスの重複確認
        if User.objects.filter(email=email).exists():
            messages.error(request, 'このメールアドレスは既に使用されています')
            return render(request, 'main/register.html')
        
        # パスワードポリシーのバリデーション
        try:
            # 仮のユーザーオブジェクトを作成してバリデーション
            temp_user = User(username=username, email=email)
            validate_password(password1, temp_user)
        except ValidationError as e:
            # エラーメッセージを日本語で表示
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'main/register.html')
        
        # ユーザー作成
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # Administrator作成
        Administrator.objects.create(user=user)
        
        messages.success(request, '登録が完了しました。ログインしてください。')
        return redirect('login')
    
    return render(request, 'main/register.html')

def login_view(request):
    """ログイン"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'ようこそ、{username}さん')
            return redirect('admin-home')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません')
    
    return render(request, 'main/login.html')

@login_required(login_url='login')
def home(request):
    """ホーム画面"""
    return render(request, 'main/home.html')

def logout_view(request):
    """ログアウト"""
    logout(request)
    messages.success(request, 'ログアウトしました')
    return redirect('welcome')

# ========== 顧客管理機能 ==========

@login_required(login_url='login')
def customer_list(request):
    """顧客一覧"""
    search_name = request.GET.get('search_name', '')
    search_phone = request.GET.get('search_phone', '')
    search_email = request.GET.get('search_email', '')
    
    customers = Customer.objects.all()
    
    # 顧客名で絞り込み
    if search_name:
        customers = customers.filter(name__icontains=search_name)
    
    # 電話番号で絞り込み
    if search_phone:
        customers = customers.filter(phone_number__icontains=search_phone)
    
    # メールアドレスで絞り込み
    if search_email:
        customers = customers.filter(email__icontains=search_email)
    
    customers = customers.order_by('-created_at')
    
    return render(request, 'main/customer_list.html', {
        'customers': customers,
        'search_name': search_name,
        'search_phone': search_phone,
        'search_email': search_email,
    })

@login_required(login_url='login')
def customer_add(request):
    """顧客新規登録"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        memo = request.POST.get('memo', '')
        last_visit_date = request.POST.get('last_visit_date')
        
        # メールアドレスの重複チェック
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'このメールアドレスは既に登録されています')
            return render(request, 'main/customer_add.html')
        
        try:
            # 顧客作成
            customer = Customer.objects.create(
                name=name,
                phone_number=phone_number,
                email=email,
                memo=memo,
                last_visit_date=last_visit_date if last_visit_date else None
            )
            messages.success(request, f'顧客「{name}」を登録しました')
            return redirect('customer-list')
        except Exception as e:
            messages.error(request, f'登録に失敗しました: {str(e)}')
            return render(request, 'main/customer_add.html')
    
    return render(request, 'main/customer_add.html')

@login_required(login_url='login')
def customer_detail(request, pk):
    """顧客詳細"""
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        messages.error(request, '顧客が見つかりません')
        return redirect('customer-list')
    
    return render(request, 'main/customer_detail.html', {
        'customer': customer,
    })

@login_required(login_url='login')
def customer_edit(request, pk):
    """顧客編集"""
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        messages.error(request, '顧客が見つかりません')
        return redirect('customer-list')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # メールアドレスの重複チェック（自分以外）
        if Customer.objects.filter(email=email).exclude(pk=pk).exists():
            messages.error(request, 'このメールアドレスは既に登録されています')
            return render(request, 'main/customer_edit.html', {'customer': customer})
        
        try:
            customer.name = request.POST.get('name')
            customer.phone_number = request.POST.get('phone_number')
            customer.email = email
            customer.memo = request.POST.get('memo', '')
            last_visit_date = request.POST.get('last_visit_date')
            customer.last_visit_date = last_visit_date if last_visit_date else None
            customer.save()
            
            messages.success(request, f'顧客「{customer.name}」を更新しました')
            return redirect('customer-detail', pk=pk)
        except Exception as e:
            messages.error(request, f'更新に失敗しました: {str(e)}')
            return render(request, 'main/customer_edit.html', {'customer': customer})
    
    return render(request, 'main/customer_edit.html', {'customer': customer})

@login_required(login_url='login')
def customer_delete(request, pk):
    """顧客削除"""
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(pk=pk)
            customer_name = customer.name
            customer.delete()
            messages.success(request, f'顧客「{customer_name}」を削除しました')
        except Customer.DoesNotExist:
            messages.error(request, '顧客が見つかりません')
        
        return redirect('customer-list')
    
    return redirect('customer-list')