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
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
    
        # スペースだけの入力をチェック
        if not username:
            messages.error(request, 'ユーザー名を入力してください')
            return render(request, 'main/register.html')
        
        if not email:
            messages.error(request, 'メールアドレスを入力してください')
            return render(request, 'main/register.html')
        
        if not password1:
            messages.error(request, 'パスワードを入力してください')
            return render(request, 'main/register.html')
        
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
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # スペースだけの入力をチェック
        if not username or not password:
            messages.error(request, 'ユーザー名とパスワードを入力してください')
            return render(request, 'main/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'ようこそ、{username}さん')
            return redirect('admin-home')
        else:
            messages.error(request, 'ユーザー名またはパスワードが正しくありません')
    
    return render(request, 'main/login.html')

def logout_view(request):
    """ログアウト"""
    logout(request)
    messages.success(request, 'ログアウトしました')
    return redirect('welcome')

@login_required(login_url='login')
def home(request):
    """ホーム画面（ダッシュボード）"""
    from datetime import date, timedelta
    from django.db.models import Count
    
    today = date.today()
    
    # 今日の予約数
    today_reservations_count = Reservation.objects.filter(
        reservation_date=today,
        status='pending'
    ).count()
    
    # 今週の予約数（月曜日から日曜日）
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    week_reservations_count = Reservation.objects.filter(
        reservation_date__range=[start_of_week, end_of_week],
        status='pending'
    ).count()
    
    # ステータス別集計
    status_counts = Reservation.objects.values('status').annotate(count=Count('status'))
    pending_count = 0
    completed_count = 0
    cancelled_count = 0
    
    for item in status_counts:
        if item['status'] == 'pending':
            pending_count = item['count']
        elif item['status'] == 'completed':
            completed_count = item['count']
        elif item['status'] == 'cancelled':
            cancelled_count = item['count']
    
    # 今日の予約リスト
    today_reservations = Reservation.objects.filter(
        reservation_date=today
    ).order_by('reservation_time')[:5]
    
    # 直近の顧客リスト
    recent_customers = Customer.objects.order_by('-created_at')[:5]
    
    # 全体の統計
    total_customers = Customer.objects.count()
    total_reservations = Reservation.objects.count()
    
    context = {
        'today_reservations_count': today_reservations_count,
        'week_reservations_count': week_reservations_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'today_reservations': today_reservations,
        'recent_customers': recent_customers,
        'total_customers': total_customers,
        'total_reservations': total_reservations,
    }
    
    return render(request, 'main/home.html', context)

# ========== 顧客管理機能 ==========

# 顧客一覧
@login_required
def customer_list(request):
    from django.core.paginator import Paginator
    
    query = request.GET.get('query', '')
    
    if query:
        # 検索条件に基づいてフィルタリング
        customers = Customer.objects.filter(
            name__icontains=query
        ) | Customer.objects.filter(
            phone_number__icontains=query
        ) | Customer.objects.filter(
            email__icontains=query
        )
    else:
        customers = Customer.objects.all()
    
    # 作成日時の降順でソート
    customers = customers.order_by('-created_at')
    
    # ページネーション（1ページあたり10件）
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'main/customer_list.html', {
        'customers': page_obj,
        'query': query,
        'page_obj': page_obj,
    })
    
# 顧客一覧CSV出力
@login_required
def customer_list_csv(request):
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    query = request.GET.get('query', '')
    
    if query:
        customers = Customer.objects.filter(
            name__icontains=query
        ) | Customer.objects.filter(
            phone_number__icontains=query
        ) | Customer.objects.filter(
            email__icontains=query
        )
    else:
        customers = Customer.objects.all()
    
    customers = customers.order_by('-created_at')
    
    # CSV出力
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['顧客名', '電話番号', 'メールアドレス', '最終来店日', '登録日'])
    
    for customer in customers:
        writer.writerow([
            customer.name,
            customer.phone_number,
            customer.email,
            customer.last_visit_date if customer.last_visit_date else '未設定',
            customer.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required(login_url='login')
def customer_add(request):
    """顧客新規登録"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        # スペースだけの入力をチェック
        if not name:
            messages.error(request, '顧客名を入力してください')
            return render(request, 'main/customer_add.html')
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
    
    # 顧客の予約履歴を取得（新しい順）
    reservations = Reservation.objects.filter(customer=customer).order_by('-reservation_date', '-reservation_time')
    
    # 予約回数の集計
    total_reservations = reservations.count()
    completed_reservations = reservations.filter(status='completed').count()
    pending_reservations = reservations.filter(status='pending').count()
    cancelled_reservations = reservations.filter(status='cancelled').count()
    
    return render(request, 'main/customer_detail.html', {
        'customer': customer,
        'reservations': reservations,
        'total_reservations': total_reservations,
        'completed_reservations': completed_reservations,
        'pending_reservations': pending_reservations,
        'cancelled_reservations': cancelled_reservations,
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
            name = request.POST.get('name', '').strip()
            # スペースだけの入力をチェック
            if not name:
                messages.error(request, '顧客名を入力してください')
                return render(request, 'main/customer_edit.html', {'customer': customer})
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

# 予約時間の重複チェック関数
def check_reservation_overlap(reservation_date, reservation_time, duration, exclude_id=None):
    """
    予約時間の重複をチェックする
    exclude_id: 編集時に自分自身を除外するためのID
    """
    from datetime import datetime, timedelta
    
    # 新規予約の開始時刻と終了時刻を計算
    start_datetime = datetime.combine(reservation_date, reservation_time)
    end_datetime = start_datetime + timedelta(minutes=int(duration))
    
    # 同じ日の予約を取得
    reservations = Reservation.objects.filter(
        reservation_date=reservation_date,
        status='pending'  # 予約中のもののみチェック
    )
    
    # 編集時は自分自身を除外
    if exclude_id:
        reservations = reservations.exclude(pk=exclude_id)
    
    # 各予約と時間が重なるかチェック
    for reservation in reservations:
        existing_start = datetime.combine(
            reservation.reservation_date, 
            reservation.reservation_time
        )
        existing_end = existing_start + timedelta(minutes=reservation.duration)
        
        # 時間が重なる条件：
        # 1. 新規予約の開始が既存予約の範囲内
        # 2. 新規予約の終了が既存予約の範囲内
        # 3. 新規予約が既存予約を完全に含む
        if (start_datetime < existing_end and end_datetime > existing_start):
            return True, reservation  # 重複あり
    
    return False, None  # 重複なし

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
    
# 予約一覧CSV出力
@login_required
def reservation_list_csv(request):
    import csv
    from django.http import HttpResponse
    from datetime import datetime, date
    
    # 検索条件を取得
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    time_from = request.GET.get('time_from')
    time_to = request.GET.get('time_to')
    selected_customers = request.GET.getlist('customers')
    selected_statuses = request.GET.getlist('statuses')
    
    reservations = Reservation.objects.all()
    
    # 検索条件でフィルタリング
    if date_from:
        reservations = reservations.filter(reservation_date__gte=date_from)
    if date_to:
        reservations = reservations.filter(reservation_date__lte=date_to)
    if time_from:
        reservations = reservations.filter(reservation_time__gte=time_from)
    if time_to:
        reservations = reservations.filter(reservation_time__lte=time_to)
    if selected_customers:
        reservations = reservations.filter(customer_id__in=selected_customers)
    if selected_statuses:
        reservations = reservations.filter(status__in=selected_statuses)
    
    reservations = reservations.order_by('-reservation_date', '-reservation_time')
    
    # CSV出力
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename = f'reservations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['予約日', '時間', '顧客名', 'サービス', '所要時間', 'ステータス', '備考'])
    
    status_dict = {'pending': '予約中', 'completed': '完了', 'cancelled': 'キャンセル'}
    
    for reservation in reservations:
        writer.writerow([
            reservation.reservation_date,
            reservation.reservation_time.strftime('%H:%M'),
            reservation.customer.name,
            reservation.service,
            f'{reservation.duration}分',
            status_dict.get(reservation.status, reservation.status),
            reservation.memo
        ])
    
    return response

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
        
        # 日付と時刻をdatetimeオブジェクトに変換
        from datetime import datetime
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(reservation_time, '%H:%M').time()
        
        # 重複チェック
        is_overlapping, overlapping_reservation = check_reservation_overlap(
            date_obj, time_obj, duration
        )
        
        if is_overlapping:
            # 重複エラー
            messages.error(
                request, 
                f'予約時間が重複しています。{overlapping_reservation.customer.name}様の予約（{overlapping_reservation.reservation_time}〜）と重なっています。'
            )
            # エラー時は入力値を保持
            from datetime import date
            today = date.today()
            customers = Customer.objects.all()
            return render(request, 'main/reservation_add.html', {
                'customers': customers,
                'today': today,
                'selected_customer': customer_id,
                'reservation_date': reservation_date,
                'reservation_time': reservation_time,
                'service': service,
                'duration': duration,
                'status': status,
                'memo': memo,
            })
        
        # 重複がなければ予約を作成
        Reservation.objects.create(
            customer_id=customer_id,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            service=service,
            duration=duration,
            status=status,
            memo=memo
        )
        messages.success(request, '予約を登録しました')
        return redirect('reservation_list')
    
    # 今日の日付を追加
    from datetime import date
    today = date.today()

    # URLパラメータから日付と時間を取得（カレンダーから遷移した場合）
    selected_date = request.GET.get('date', '')
    selected_time = request.GET.get('time', '')

    customers = Customer.objects.all()
    return render(request, 'main/reservation_add.html', {
        'customers': customers,
        'today': today,
        'selected_date': selected_date,
        'selected_time': selected_time,  # 追加
    })
    
# 予約編集
@login_required
def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        reservation_date = request.POST.get('reservation_date')
        reservation_time = request.POST.get('reservation_time')
        service = request.POST.get('service')
        duration = request.POST.get('duration', 60)
        status = request.POST.get('status')
        memo = request.POST.get('memo', '')
        
        # 日付と時刻をdatetimeオブジェクトに変換
        from datetime import datetime
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(reservation_time, '%H:%M').time()
        
        # 重複チェック（自分自身は除外）
        is_overlapping, overlapping_reservation = check_reservation_overlap(
            date_obj, time_obj, duration, exclude_id=pk
        )
        
        if is_overlapping:
            # 重複エラー
            messages.error(
                request, 
                f'予約時間が重複しています。{overlapping_reservation.customer.name}様の予約（{overlapping_reservation.reservation_time}〜）と重なっています。'
            )
            # エラー時は入力値を保持して再表示
            from datetime import date
            today = date.today()
            customers = Customer.objects.all()
            # 一時的に値を更新（保存はしない）
            reservation.customer_id = customer_id
            reservation.reservation_date = date_obj
            reservation.reservation_time = time_obj
            reservation.service = service
            reservation.duration = duration
            reservation.status = status
            reservation.memo = memo
            return render(request, 'main/reservation_edit.html', {
                'reservation': reservation,
                'customers': customers,
                'today': today
            })
        
        # 重複がなければ更新
        reservation.customer_id = customer_id
        reservation.reservation_date = reservation_date
        reservation.reservation_time = reservation_time
        reservation.service = service
        reservation.duration = duration
        reservation.status = status
        reservation.memo = memo
        reservation.save()
        
        # ステータスが完了になった場合、顧客の最終来店日を更新
        print(f"DEBUG: status = {status}, type = {type(status)}")
        if status == 'completed':
            customer = reservation.customer
            customer.last_visit_date = date_obj
            customer.save()
            print(f"DEBUG: 最終来店日を更新しました - {customer.name}: {customer.last_visit_date}")
        
        messages.success(request, '予約を更新しました')
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
    
# 予約詳細（閲覧専用）
@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    return render(request, 'main/reservation_detail.html', {
        'reservation': reservation,
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

# カレンダー表示
@login_required
def reservation_calendar(request):
    """予約カレンダー表示"""
    return render(request, 'main/reservation_calendar.html')

# カレンダー用の予約データをJSON形式で返す
@login_required
def reservation_calendar_data(request):
    """カレンダー用の予約データAPI"""
    from django.http import JsonResponse
    
    # 全ての予約データを取得（日付フィルタなし）
    reservations = Reservation.objects.all()
    
    # JSON形式に変換
    events = []
    for reservation in reservations:
        # 色の設定（ステータスによって変更）
        if reservation.status == 'pending':
            color = '#ffc107'  # 黄色
        elif reservation.status == 'completed':
            color = '#28a745'  # 緑
        else:
            color = '#6c757d'  # 灰色
        
        # 日時をISO形式の文字列に変換
        start_datetime = f'{reservation.reservation_date}T{reservation.reservation_time}'
        
        events.append({
            'id': reservation.pk,
            'title': f'{reservation.customer.name} - {reservation.service}',
            'start': start_datetime,
            'color': color,
            'extendedProps': {
                'customer': reservation.customer.name,
                'service': reservation.service,
                'duration': reservation.duration,
                'status': reservation.get_status_display(),
            }
        })
    
    return JsonResponse(events, safe=False)

# ========== 一般ユーザー向け予約機能 ==========

def public_booking(request):
    """一般ユーザー向け予約フォーム"""
    from datetime import date
    today = date.today()
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()

        # スペースだけの入力をチェック
        if not name:
            messages.error(request, 'お名前を入力してください')
            return render(request, 'main/public_booking.html', {'today': today})
    
        if not phone_number:
            messages.error(request, '電話番号を入力してください')
            return render(request, 'main/public_booking.html', {'today': today})
    
        if not email:
            messages.error(request, 'メールアドレスを入力してください')
            return render(request, 'main/public_booking.html', {'today': today})
        reservation_date = request.POST.get('reservation_date')
        reservation_time = request.POST.get('reservation_time')
        service = request.POST.get('service')
        duration = request.POST.get('duration', 60)
        memo = request.POST.get('memo', '')
        
        # 日付と時刻をdatetimeオブジェクトに変換
        from datetime import datetime
        date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(reservation_time, '%H:%M').time()
        
        # 重複チェック
        is_overlapping, overlapping_reservation = check_reservation_overlap(
            date_obj, time_obj, duration
        )
        
        if is_overlapping:
            messages.error(
                request, 
                f'申し訳ございません。ご希望の時間帯は既に予約が入っております。別の時間帯をお選びください。'
            )
            return render(request, 'main/public_booking.html', {
                'today': today,
                'name': name,
                'phone_number': phone_number,
                'email': email,
                'reservation_date': reservation_date,
                'reservation_time': reservation_time,
                'service': service,
                'duration': duration,
                'memo': memo,
            })
        
        # 顧客の存在確認または作成
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'phone_number': phone_number,
            }
        )
        
        # 既存顧客の場合は情報を更新
        if not created:
            customer.name = name
            customer.phone_number = phone_number
            customer.save()
        
        # 予約作成
        reservation = Reservation.objects.create(
            customer=customer,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            service=service,
            duration=duration,
            status='pending',
            memo=memo
        )
        
        # 予約完了画面へリダイレクト
        return redirect('public_booking_complete', pk=reservation.pk)
    
    return render(request, 'main/public_booking.html', {
        'today': today,
    })

def public_booking_complete(request, pk):
    """予約完了画面"""
    reservation = get_object_or_404(Reservation, pk=pk)
    return render(request, 'main/public_booking_complete.html', {
        'reservation': reservation,
    })

def public_booking_check(request):
    """予約確認画面"""
    reservations = None
    email = ''
    
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # メールアドレスで顧客を検索
        try:
            customer = Customer.objects.get(email=email)
            # その顧客の予約を取得（未来の予約のみ）
            from datetime import date
            today = date.today()
            reservations = Reservation.objects.filter(
                customer=customer,
                reservation_date__gte=today
            ).order_by('reservation_date', 'reservation_time')
            
            # メールアドレスをセッションに保存（詳細画面でのアクセス制御用）
            if reservations.exists():
                request.session['verified_email'] = email
                
        except Customer.DoesNotExist:
            messages.error(request, 'ご入力いただいたメールアドレスで予約が見つかりませんでした。')
    
    return render(request, 'main/public_booking_check.html', {
        'reservations': reservations,
        'email': email,
    })
    
# 一般ユーザー向け予約詳細
def public_booking_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # セッションで確認済みのメールアドレスを取得
    verified_email = request.session.get('verified_email')
    
    # メールアドレスが一致しない場合はアクセス拒否
    if not verified_email or verified_email != reservation.customer.email:
        messages.error(request, 'この予約にアクセスする権限がありません')
        return redirect('public_booking_check')
    
    return render(request, 'main/public_booking_detail.html', {
        'reservation': reservation,
    })