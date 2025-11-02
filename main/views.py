from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Administrator, Customer, Reservation

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
        
        # 入力値を保持するためのコンテキスト
        context = {
            'name': name,
            'phone_number': phone_number,
            'email': email,
            'memo': memo,
            'last_visit_date': last_visit_date,
        }
        
        # 電話番号の重複チェック
        if Customer.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'この電話番号は既に登録されています')
            return render(request, 'main/customer_add.html', context)
        
        # メールアドレスの重複チェック
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'このメールアドレスは既に登録されています')
            return render(request, 'main/customer_add.html', context)
        
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
            return redirect('customer_list')
        except Exception as e:
            messages.error(request, f'登録に失敗しました: {str(e)}')
            return render(request, 'main/customer_add.html', context)
    
    return render(request, 'main/customer_add.html')

@login_required(login_url='login')
def customer_detail(request, pk):
    """顧客詳細"""
    try:
        customer = Customer.objects.get(pk=pk)
    except Customer.DoesNotExist:
        messages.error(request, '顧客が見つかりません')
        return redirect('customer_list')
    
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
        return redirect('customer_list')
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        
        # 電話番号の重複チェック（自分以外）
        if Customer.objects.filter(phone_number=phone_number).exclude(pk=pk).exists():
            messages.error(request, 'この電話番号は既に登録されています')
            # エラー時に入力値を保持
            customer.name = request.POST.get('name')
            customer.phone_number = phone_number
            customer.email = email
            customer.memo = request.POST.get('memo', '')
            return render(request, 'main/customer_edit.html', {'customer': customer})
        
        # メールアドレスの重複チェック（自分以外）
        if Customer.objects.filter(email=email).exclude(pk=pk).exists():
            messages.error(request, 'このメールアドレスは既に登録されています')
            # エラー時に入力値を保持
            customer.name = request.POST.get('name')
            customer.phone_number = phone_number
            customer.email = email
            customer.memo = request.POST.get('memo', '')
            return render(request, 'main/customer_edit.html', {'customer': customer})
        
        try:
            customer.name = request.POST.get('name')
            customer.phone_number = phone_number
            customer.email = email
            customer.memo = request.POST.get('memo', '')
            last_visit_date = request.POST.get('last_visit_date')
            customer.last_visit_date = last_visit_date if last_visit_date else None
            customer.save()
            
            messages.success(request, f'顧客「{customer.name}」を更新しました')
            return redirect('customer_detail', pk=pk)
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
        
        return redirect('customer_list')
    
    return redirect('customer_list')

# 予約一覧
@login_required
def reservation_list(request):
    reservations = Reservation.objects.all()
    
    # 予約日（from-to）
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        reservations = reservations.filter(reservation_date__gte=date_from)
    if date_to:
        reservations = reservations.filter(reservation_date__lte=date_to)
    
    # 時間（from-to）
    time_from = request.GET.get('time_from', '')
    time_to = request.GET.get('time_to', '')
    if time_from:
        reservations = reservations.filter(reservation_time__gte=time_from)
    if time_to:
        reservations = reservations.filter(reservation_time__lte=time_to)
    
    # 顧客名（複数選択）
    customer_ids = request.GET.getlist('customers')
    if customer_ids:
        reservations = reservations.filter(customer_id__in=customer_ids)
    
    # ステータス（複数選択）
    statuses = request.GET.getlist('statuses')
    if statuses:
        reservations = reservations.filter(status__in=statuses)
    
    # 全顧客とステータス選択肢を取得
    all_customers = Customer.objects.all()
    status_choices = Reservation.STATUS_CHOICES
    
    return render(request, 'main/reservation_list.html', {
        'reservations': reservations,
        'all_customers': all_customers,
        'status_choices': status_choices,
        'date_from': date_from,
        'date_to': date_to,
        'time_from': time_from,
        'time_to': time_to,
        'selected_customers': customer_ids,
        'selected_statuses': statuses,
    })

# 予約追加
@login_required
def reservation_add(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        reservation_date = request.POST.get('reservation_date')
        reservation_time = request.POST.get('reservation_time')
        service = request.POST.get('service')
        duration = request.POST.get('duration', 60)
        status = request.POST.get('status', 'pending')
        memo = request.POST.get('memo', '')
        
        Reservation.objects.create(
            customer_id=customer_id,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            service=service,
            duration=duration,
            status=status,
            memo=memo
        )
        return redirect('reservation_list')
    
    # 今日の日付を追加
    from datetime import date
    today = date.today()
    
    customers = Customer.objects.all()
    return render(request, 'main/reservation_add.html', {
        'customers': customers,
        'today': today
    })
    
# 予約編集
@login_required
def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        reservation.customer_id = request.POST.get('customer')
        reservation.reservation_date = request.POST.get('reservation_date')
        reservation.reservation_time = request.POST.get('reservation_time')
        reservation.service = request.POST.get('service')
        reservation.duration = request.POST.get('duration', 60)
        reservation.status = request.POST.get('status')
        reservation.memo = request.POST.get('memo', '')
        reservation.save()
        return redirect('reservation_list')
    
    # 今日の日付を追加
    from datetime import date
    today = date.today()
    
    customers = Customer.objects.all()
    return render(request, 'main/reservation_edit.html', {
        'reservation': reservation,
        'customers': customers,
        'today': today
    })
    
# 予約削除
@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    reservation.delete()
    return redirect('reservation_list')

# カスタム404ページ
def custom_404(request, exception):
    return render(request, '404.html', status=404)