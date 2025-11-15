def user_permissions(request):
    """全ページで権限情報を利用可能にする"""
    if request.user.is_authenticated:
        try:
            from main.models import Administrator, UserProfile
            admin = Administrator.objects.get(user=request.user)
            profile = UserProfile.objects.get(user=admin)
            is_super_admin = (
                profile.can_edit_customer and 
                profile.can_delete_customer and 
                profile.can_edit_reservation and 
                profile.can_delete_reservation
            )
        except:
            is_super_admin = False
    else:
        is_super_admin = False
    
    return {
        'is_super_admin': is_super_admin,
    }