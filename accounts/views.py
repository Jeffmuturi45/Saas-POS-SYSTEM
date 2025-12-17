# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib import messages
from django.views.generic import CreateView
from django import forms
from django.db.models import Count, Sum, Q, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate, TruncMonth
import json
import secrets
import string


from .models import User
from businesses.models import Business
from licenses.models import License
from pos.models import Sale
from superadmin.models import SystemActivity, Notification
from businesses.actions import (
    renew_license, suspend_business,
    activate_business, delete_business
)

# Helper functions


def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g. 3 days ago, 5 hours ago etc.
    """
    now = timezone.now()
    diff = now - dt

    seconds = diff.total_seconds()
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{int(days)} days ago"
    elif hours > 0:
        return f"{int(hours)} hours ago"
    elif minutes > 0:
        return f"{int(minutes)} minutes ago"
    else:
        return default

# Decorators


def super_admin_required(function=None):
    """Decorator for views that require super admin access."""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_super_admin,
        login_url='/accounts/login/',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# Views


# accounts/views.py (update login_view)
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        # If user is already logged in, redirect to appropriate dashboard
        if request.user.is_super_admin:
            return redirect('super_admin_dashboard')
        elif request.user.is_business_admin:
            return redirect('business_admin_dashboard')
        else:
            return redirect('cashier_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user's business is suspended
            if user.business and user.business.status == 'SUSPENDED':
                messages.error(
                    request, 'Your business account has been suspended. Please contact the system administrator.')
                return render(request, 'accounts/login.html')

            # Check if user account is active
            if not user.is_active:
                messages.error(
                    request, 'Your account is disabled. Please contact the system administrator.')
                return render(request, 'accounts/login.html')

            if user.is_active:
                login(request, user)

                # Log login activity
                SystemActivity.objects.create(
                    activity_type=SystemActivity.ActivityType.LOGIN,
                    description=f"User {user.username} logged in",
                    user=user,
                    performed_by=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )

                messages.success(
                    request, f'Welcome back, {user.get_full_name() or user.username}!')

                # Redirect based on role
                if user.is_super_admin:
                    return redirect('super_admin_dashboard')
                elif user.is_business_admin:
                    return redirect('business_admin_dashboard')
                else:
                    return redirect('cashier_dashboard')
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """User logout view."""
    # Log logout activity
    SystemActivity.objects.create(
        activity_type=SystemActivity.ActivityType.LOGOUT,
        description=f"User {request.user.username} logged out",
        user=request.user,
        performed_by=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# Forms


class BusinessRegistrationForm(forms.Form):
    """Form for super admin to register a new business."""
    business_name = forms.CharField(max_length=255, label="Business Name")
    business_type = forms.ChoiceField(
        choices=[
            ('RETAIL', 'Retail Store'),
            ('RESTAURANT', 'Restaurant'),
            ('SERVICE', 'Service Business'),
            ('WHOLESALE', 'Wholesale'),
            ('OTHER', 'Other')
        ],
        label="Business Type"
    )
    contact_email = forms.EmailField(label="Contact Email")
    contact_phone = forms.CharField(max_length=20, label="Contact Phone")
    address = forms.CharField(widget=forms.Textarea(
        attrs={'rows': 3}), label="Address")
    city = forms.CharField(max_length=100, label="City")
    country = forms.CharField(max_length=100, label="Country")

    # Admin user details
    admin_username = forms.CharField(max_length=150, label="Admin Username")
    admin_email = forms.EmailField(label="Admin Email")
    admin_first_name = forms.CharField(
        max_length=30, required=False, label="First Name")
    admin_last_name = forms.CharField(
        max_length=30, required=False, label="Last Name")
    admin_phone = forms.CharField(max_length=20, required=False, label="Phone")

    # License details
    license_tier = forms.ChoiceField(
        choices=[
            ('DEMO', 'Demo (30 days)'),
            ('BASIC', 'Basic'),
            ('PRO', 'Professional'),
            ('ENTERPRISE', 'Enterprise')
        ],
        label="License Tier"
    )
    license_duration = forms.ChoiceField(
        choices=[
            (30, '30 days'),
            (90, '90 days'),
            (180, '180 days'),
            (365, '1 year')
        ],
        label="License Duration"
    )


@login_required
@super_admin_required
def business_registration_view(request):
    """View for super admin to register a new business."""
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create Business
                business = Business.objects.create(
                    name=form.cleaned_data['business_name'],
                    business_type=form.cleaned_data['business_type'],
                    email=form.cleaned_data['contact_email'],
                    phone=form.cleaned_data['contact_phone'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    country=form.cleaned_data['country'],
                    status=Business.Status.ACTIVE,
                    is_demo_account=(
                        form.cleaned_data['license_tier'] == 'DEMO'),
                    created_by=request.user
                )

                # Create License
                start_date = timezone.now().date()
                end_date = start_date + \
                    timedelta(days=int(form.cleaned_data['license_duration']))

                license_obj = License.objects.create(
                    business=business,
                    tier=form.cleaned_data['license_tier'],
                    start_date=start_date,
                    end_date=end_date,
                    # KSH
                    monthly_price=0.00 if form.cleaned_data['license_tier'] == 'DEMO' else 2999.00,
                    max_users=3 if form.cleaned_data['license_tier'] == 'DEMO' else 10,
                    max_products=100 if form.cleaned_data['license_tier'] == 'DEMO' else 1000,
                    max_branches=1
                )

                # Create Business Admin User
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for _ in range(12))

                admin_user = User.objects.create_user(
                    username=form.cleaned_data['admin_username'],
                    email=form.cleaned_data['admin_email'],
                    first_name=form.cleaned_data['admin_first_name'],
                    last_name=form.cleaned_data['admin_last_name'],
                    phone_number=form.cleaned_data['admin_phone'],
                    role=User.Role.BUSINESS_ADMIN,
                    business=business,
                    license_tier=form.cleaned_data['license_tier'],
                    is_active=True
                )
                admin_user.set_password(password)
                admin_user.save()

                # Log activity
                SystemActivity.objects.create(
                    activity_type=SystemActivity.ActivityType.BUSINESS_CREATED,
                    description=f"Business {business.name} created",
                    business=business,
                    performed_by=request.user,
                    data={
                        'admin_username': admin_user.username,
                        'license_tier': license_obj.tier,
                        'license_end_date': end_date.isoformat()
                    }
                )

                # Create notification for super admin
                Notification.objects.create(
                    title="New Business Registered",
                    message=f"Business {business.name} has been registered successfully",
                    notification_type=Notification.NotificationType.SUCCESS,
                    audience=Notification.Audience.SUPER_ADMINS,
                    business=business
                )

                messages.success(
                    request, f'Business "{business.name}" registered successfully!')
                messages.info(
                    request, f'Admin login: {admin_user.username} | Password: {password}')

                return redirect('manage_businesses')

            except Exception as e:
                messages.error(request, f'Error creating business: {str(e)}')
    else:
        form = BusinessRegistrationForm()

    return render(request, 'super_admin/register_business.html', {'form': form})

# Dashboard Views


@login_required
def super_admin_dashboard(request):
    """Super Admin Dashboard."""
    if not request.user.is_super_admin:
        messages.error(
            request, 'Access denied. Super admin privileges required.')
        return redirect('login')

    # Get real data from database
    businesses_count = Business.objects.count()
    users_count = User.objects.count()
    active_licenses = License.objects.filter(is_active=True).count()

    # Calculate monthly revenue in KSH
    monthly_revenue = Sale.objects.filter(
        created_at__month=timezone.now().month,
        created_at__year=timezone.now().year
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Business types distribution
    business_types_data = Business.objects.values('business_type').annotate(
        count=Count('business_type')
    ).order_by('-count')

    business_types = []
    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
    for i, data in enumerate(business_types_data[:5]):
        business_types.append({
            'name': dict(Business._meta.get_field('business_type').choices).get(data['business_type'], data['business_type']),
            'count': data['count'],
            'color': colors[i % len(colors)]
        })

    # Recent businesses (last 5)
    recent_businesses = Business.objects.select_related(
        'license').order_by('-created_at')[:5]

    # Real recent activities from database
    recent_activities_list = SystemActivity.objects.select_related(
        'business', 'user').order_by('-created_at')[:10]

    recent_activities = []
    for activity in recent_activities_list:
        recent_activities.append({
            'icon': activity.icon,
            'color': activity.color,
            'text': activity.description,
            'time': timesince(activity.created_at)
        })

    # License statistics
    total_licenses = License.objects.count()
    active_licenses_count = License.objects.filter(
        is_active=True,
        end_date__gte=timezone.now().date()
    ).count()

    expired_licenses = License.objects.filter(
        Q(is_active=False) | Q(end_date__lt=timezone.now().date())
    ).count()

    demo_licenses = License.objects.filter(tier='DEMO').count()

    # Licenses expiring soon (within 30 days)
    expiring_date = timezone.now().date() + timedelta(days=30)
    expiring_soon = License.objects.filter(
        end_date__gte=timezone.now().date(),
        end_date__lte=expiring_date,
        is_active=True
    ).count()

    # Calculate percentages
    active_percentage = (active_licenses_count /
                         total_licenses * 100) if total_licenses > 0 else 0
    expired_percentage = (expired_licenses / total_licenses *
                          100) if total_licenses > 0 else 0
    demo_percentage = (demo_licenses / total_licenses *
                       100) if total_licenses > 0 else 0
    expiring_percentage = (expiring_soon / total_licenses *
                           100) if total_licenses > 0 else 0

    license_stats = {
        'active': active_licenses_count,
        'expired': expired_licenses,
        'demo': demo_licenses,
        'expiring_soon': expiring_soon,
        'active_percentage': active_percentage,
        'expired_percentage': expired_percentage,
        'demo_percentage': demo_percentage,
        'expiring_percentage': expiring_percentage,
    }

    # Get unread notifications count
    unread_notifications = Notification.objects.filter(
        is_active=True,
        is_read=False
    ).count()

    context = {
        'user': request.user,
        'businesses_count': businesses_count,
        'users_count': users_count,
        'active_licenses': active_licenses,
        'monthly_revenue': monthly_revenue,
        'business_types': business_types,
        'recent_businesses': recent_businesses,
        'recent_activities': recent_activities,
        'license_stats': license_stats,
        'unread_notifications': unread_notifications,
    }

    return render(request, 'super_admin/dashboard.html', context)


@login_required
@super_admin_required
def manage_businesses(request):
    """View all businesses."""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    license_filter = request.GET.get('license', '')
    search_query = request.GET.get('search', '')

    # Base queryset
    businesses = Business.objects.select_related(
        'license').prefetch_related('users').order_by('-created_at')

    # Apply filters
    if status_filter:
        businesses = businesses.filter(status=status_filter)

    if license_filter:
        businesses = businesses.filter(license__tier=license_filter)

    if search_query:
        businesses = businesses.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(businesses, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistics
    stats = {
        'total_businesses': Business.objects.count(),
        'active_businesses': Business.objects.filter(status='ACTIVE').count(),
        'demo_businesses': Business.objects.filter(is_demo_account=True).count(),
        'expiring_soon': License.objects.filter(
            end_date__gte=timezone.now().date(),
            end_date__lte=timezone.now().date() + timedelta(days=30),
            is_active=True
        ).count(),
    }

    context = {
        'businesses': page_obj,
        'stats': stats,
        'filter_status': status_filter,
        'filter_license': license_filter,
        'search_query': search_query,
    }

    return render(request, 'super_admin/businesses.html', context)


@login_required
@super_admin_required
def business_detail_view(request, business_id):
    """View business details."""
    try:
        business = Business.objects.select_related(
            'license').prefetch_related('users').get(id=business_id)

        # Get recent activities for this business
        recent_activities = SystemActivity.objects.filter(
            business=business
        ).order_by('-created_at')[:10]

        # Get notifications for this business
        notifications = Notification.objects.filter(
            business=business,
            is_active=True
        ).order_by('-created_at')[:5]

        context = {
            'business': business,
            'recent_activities': recent_activities,
            'notifications': notifications,
        }

        return render(request, 'super_admin/business_detail.html', context)
    except Business.DoesNotExist:
        messages.error(request, 'Business not found')
        return redirect('manage_businesses')


@login_required
@super_admin_required
def theme_customization(request):
    """Theme customization page."""
    return render(request, 'super_admin/themes.html')


@login_required
@super_admin_required
def manage_users(request):
    """Manage all users in the system."""
    users = User.objects.select_related('business').order_by('-date_joined')

    # Apply filters if any
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    # Pagination
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Real statistics
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'super_admins': User.objects.filter(role=User.Role.SUPER_ADMIN).count(),
        'business_admins': User.objects.filter(role=User.Role.BUSINESS_ADMIN).count(),
        'cashiers': User.objects.filter(role=User.Role.CASHIER).count(),
        'staff': User.objects.filter(role=User.Role.STAFF).count(),
        'users_today': User.objects.filter(
            date_joined__date=timezone.now().date()
        ).count(),
        'users_this_week': User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }

    context = {
        'users': page_obj,
        'stats': stats,
        'all_businesses': Business.objects.all(),
    }

    return render(request, 'super_admin/users.html', context)


@login_required
def business_admin_dashboard(request):
    """Business Admin Dashboard with real data."""
    if not request.user.is_business_admin:
        messages.error(
            request, 'Access denied. Business admin privileges required.')
        return redirect('login')

    business = request.user.business

    if not business:
        messages.error(request, 'No business assigned to your account.')
        return redirect('login')

    # Get real statistics
    from pos.models import Sale, Product, Category
    from datetime import datetime, timedelta

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Sales statistics
    today_sales = Sale.objects.filter(
        business=business,
        created_at__date=today
    ).aggregate(
        total_amount=Sum('total_amount'),
        count=Count('id')
    )

    week_sales = Sale.objects.filter(
        business=business,
        created_at__date__gte=week_ago
    ).aggregate(
        total_amount=Sum('total_amount'),
        count=Count('id')
    )

    month_sales = Sale.objects.filter(
        business=business,
        created_at__date__gte=month_ago
    ).aggregate(
        total_amount=Sum('total_amount'),
        count=Count('id')
    )

    # Product statistics
    total_products = Product.objects.filter(business=business).count()
    low_stock_products = Product.objects.filter(
        business=business,
        stock_quantity__lte=F('low_stock_threshold'),
        track_inventory=True
    ).count()

    # Staff statistics
    total_staff = User.objects.filter(business=business).count()

    # Recent sales
    recent_sales = Sale.objects.filter(
        business=business
    ).select_related('cashier').order_by('-created_at')[:10]

    # Top selling products
    from django.db.models import Sum
    top_products = Product.objects.filter(
        business=business,
        sale_items__sale__created_at__gte=month_ago
    ).annotate(
        total_sold=Sum('sale_items__quantity')
    ).order_by('-total_sold')[:5]

    # Daily revenue for chart
    daily_revenue = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_sales = Sale.objects.filter(
            business=business,
            created_at__date=date
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        daily_revenue.append({
            'date': date.strftime('%a'),
            'revenue': float(day_sales)
        })

    daily_revenue.reverse()

    # Get notifications for this business
    from superadmin.models import Notification
    recent_notifications = Notification.objects.filter(
        business=business,
        is_active=True
    ).order_by('-created_at')[:5]

    unread_notifications_count = Notification.objects.filter(
        business=business,
        is_active=True,
        is_read=False
    ).count()

    context = {
        'user': request.user,
        'business': business,
        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_staff': total_staff,
        'recent_sales': recent_sales,
        'top_products': top_products,
        'daily_revenue': daily_revenue,
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_notifications_count,
    }

    return render(request, 'business_admin/dashboard.html', context)


@login_required
def cashier_dashboard(request):
    """Cashier Dashboard."""
    context = {
        'user': request.user,
        'business': request.user.business,
    }

    return render(request, 'cashier/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view."""
    return render(request, 'accounts/profile.html', {'user': request.user})

# API Endpoints


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def renew_license_view(request):
    """API endpoint to renew business license."""
    try:
        data = json.loads(request.body)
        business_id = data.get('business_id')
        duration_days = int(data.get('duration_days', 30))
        tier = data.get('tier')

        success, message = renew_license(
            business_id, duration_days, tier, request.user)

        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def suspend_business_view(request):
    """API endpoint to suspend business."""
    try:
        data = json.loads(request.body)
        business_id = data.get('business_id')
        reason = data.get('reason', 'No reason provided')

        success, message = suspend_business(business_id, reason, request.user)

        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def activate_business_view(request):
    """API endpoint to activate business."""
    try:
        data = json.loads(request.body)
        business_id = data.get('business_id')

        success, message = activate_business(business_id, request.user)

        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
@super_admin_required
def delete_business_view(request):
    """API endpoint to delete business."""
    try:
        data = json.loads(request.body)
        business_id = data.get('business_id')

        success, message = delete_business(business_id, request.user)

        if success:
            return JsonResponse({'success': True, 'message': message})
        else:
            return JsonResponse({'success': False, 'message': message}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# Notification Views


@login_required
@super_admin_required
def notifications_view(request):
    """View all notifications."""
    notifications = Notification.objects.filter(
        is_active=True).order_by('-created_at')

    context = {
        'notifications': notifications,
    }

    return render(request, 'super_admin/notifications.html', context)


@csrf_exempt
@require_POST
@login_required
def mark_notification_read_view(request, notification_id):
    """Mark notification as read."""
    try:
        notification = Notification.objects.get(
            id=notification_id, is_active=True)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True, 'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def delete_notification_view(request, notification_id):
    """Delete notification."""
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_active = False
        notification.save()

        return JsonResponse({'success': True, 'message': 'Notification deleted'})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)


@csrf_exempt
@require_POST
@login_required
def mark_all_notifications_read_view(request):
    """Mark all notifications as read."""
    Notification.objects.filter(
        is_active=True, is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'message': 'All notifications marked as read'})


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def clear_all_notifications_view(request):
    """Clear all notifications."""
    Notification.objects.filter(is_active=True).update(is_active=False)
    return JsonResponse({'success': True, 'message': 'All notifications cleared'})

# accounts/views.py (add these functions)


@login_required
@super_admin_required
def edit_business_view(request, business_id):
    """Edit business details."""
    try:
        business = Business.objects.get(id=business_id)

        if request.method == 'POST':
            form = BusinessEditForm(
                request.POST, request.FILES, instance=business)
            if form.is_valid():
                business = form.save()
                messages.success(
                    request, f'Business "{business.name}" updated successfully!')
                return redirect('business_detail', business_id=business.id)
        else:
            form = BusinessEditForm(instance=business)

        context = {
            'business': business,
            'form': form,
        }

        return render(request, 'super_admin/edit_business.html', context)
    except Business.DoesNotExist:
        messages.error(request, 'Business not found')
        return redirect('manage_businesses')


@login_required
@super_admin_required
def manage_licenses(request):
    """Manage all licenses."""
    licenses_list = License.objects.select_related(
        'business').order_by('-created_at')

    # Apply filters
    tier_filter = request.GET.get('tier', '')
    status_filter = request.GET.get('status', '')

    if tier_filter:
        licenses_list = licenses_list.filter(tier=tier_filter)

    if status_filter:
        if status_filter == 'active':
            licenses_list = licenses_list.filter(
                is_active=True, end_date__gte=timezone.now().date())
        elif status_filter == 'expired':
            licenses_list = licenses_list.filter(
                Q(is_active=False) | Q(end_date__lt=timezone.now().date()))
        elif status_filter == 'expiring':
            expiring_date = timezone.now().date() + timedelta(days=7)
            licenses_list = licenses_list.filter(
                is_active=True,
                end_date__gte=timezone.now().date(),
                end_date__lte=expiring_date
            )
        elif status_filter == 'suspended':
            licenses_list = licenses_list.filter(is_active=False)

    # Pagination
    paginator = Paginator(licenses_list, 15)
    page_number = request.GET.get('page')
    licenses = paginator.get_page(page_number)

    # Statistics
    stats = {
        'total_licenses': License.objects.count(),
        'active_licenses': License.objects.filter(
            is_active=True,
            end_date__gte=timezone.now().date()
        ).count(),
        'expiring_soon': License.objects.filter(
            end_date__gte=timezone.now().date(),
            end_date__lte=timezone.now().date() + timedelta(days=7),
            is_active=True
        ).count(),
        'expired_licenses': License.objects.filter(
            Q(is_active=False) | Q(end_date__lt=timezone.now().date())
        ).count(),
    }

    context = {
        'licenses': licenses,
        'stats': stats,
        'all_businesses': Business.objects.all(),
    }

    return render(request, 'super_admin/licenses.html', context)


@login_required
@super_admin_required
def analytics_view(request):
    """Analytics dashboard with real data."""
    # Calculate dates
    end_date = timezone.now()
    start_date_7d = end_date - timedelta(days=7)
    start_date_30d = end_date - timedelta(days=30)

    # Get revenue data for last 7 days
    revenue_data = []
    sales_last_7d = Sale.objects.filter(
        created_at__gte=start_date_7d,
        created_at__lte=end_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total_revenue=Sum('total_amount')
    ).order_by('date')

    # Fill missing dates with 0
    date_dict = {item['date']: item['total_revenue'] for item in sales_last_7d}
    for i in range(7):
        current_date = (end_date - timedelta(days=i)).date()
        revenue = date_dict.get(current_date, 0)
        revenue_data.append({
            'date': current_date,
            'revenue': float(revenue) if revenue else 0
        })

    revenue_data.reverse()  # Oldest to newest

    # Get top businesses by revenue (last 30 days)
    top_businesses_data = Sale.objects.filter(
        created_at__gte=start_date_30d,
        created_at__lte=end_date
    ).values(
        'business__id',
        'business__name',
        'business__license__tier'
    ).annotate(
        revenue=Sum('total_amount'),
        sale_count=Count('id')
    ).order_by('-revenue')[:10]

    top_businesses = []
    for item in top_businesses_data:
        # Calculate growth (placeholder - implement proper growth calculation)
        previous_month_revenue = Sale.objects.filter(
            business_id=item['business__id'],
            created_at__gte=start_date_30d - timedelta(days=30),
            created_at__lt=start_date_30d
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        growth = 0
        if previous_month_revenue > 0:
            growth = ((float(item['revenue']) - float(previous_month_revenue)
                       ) / float(previous_month_revenue)) * 100

        top_businesses.append({
            'id': item['business__id'],
            'name': item['business__name'],
            'license_tier': item['business__license__tier'],
            'revenue': float(item['revenue']),
            'sale_count': item['sale_count'],
            'growth': round(growth, 1)
        })

    # User growth data (last 6 months)
    user_growth_data = []
    for i in range(6):
        month_start = end_date.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)
                     ).replace(day=1) - timedelta(days=1)

        new_users = User.objects.filter(
            date_joined__gte=month_start,
            date_joined__lte=month_end
        ).count()

        user_growth_data.append({
            'month': month_start.strftime('%b'),
            'count': new_users
        })

    user_growth_data.reverse()

    # License distribution
    license_distribution = License.objects.values('tier').annotate(
        count=Count('id')
    ).order_by('tier')

    # Real statistics
    stats = {
        'total_sales': Sale.objects.filter(
            created_at__gte=start_date_30d,
            created_at__lte=end_date
        ).count(),
        'total_revenue': Sale.objects.filter(
            created_at__gte=start_date_30d,
            created_at__lte=end_date
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'new_users': User.objects.filter(
            date_joined__gte=start_date_30d,
            date_joined__lte=end_date
        ).count(),
        'new_businesses': Business.objects.filter(
            created_at__gte=start_date_30d,
            created_at__lte=end_date
        ).count(),
    }

    # Active users (logged in last 30 days)
    active_users_count = User.objects.filter(
        last_login__gte=start_date_30d,
        last_login__lte=end_date
    ).count()

    # Monthly business growth
    monthly_business_growth = Business.objects.filter(
        created_at__gte=start_date_30d - timedelta(days=60),
        created_at__lt=start_date_30d
    ).count()

    current_month_growth = stats['new_businesses']
    business_growth_percentage = 0
    if monthly_business_growth > 0:
        business_growth_percentage = (
            (current_month_growth - monthly_business_growth) / monthly_business_growth) * 100

    context = {
        'revenue_data': revenue_data,
        'top_businesses': top_businesses,
        'user_growth_data': user_growth_data,
        'license_distribution': license_distribution,
        'stats': stats,
        'active_users_count': active_users_count,
        'business_growth_percentage': round(business_growth_percentage, 1),
        'current_month': timezone.now().strftime('%B %Y'),
        'expiring_count': License.objects.filter(
            end_date__gte=timezone.now().date(),
            end_date__lte=timezone.now().date() + timedelta(days=30),
            is_active=True
        ).count(),
        'total_revenue_k': round(float(stats['total_revenue'] / 1000), 1) if stats['total_revenue'] else 0,
    }

    return render(request, 'super_admin/analytics.html', context)


@login_required
@super_admin_required
def system_settings_view(request):
    """System settings page."""
    from datetime import datetime

    context = {
        'current_date': timezone.now(),
        'active_businesses_count': Business.objects.filter(status='ACTIVE').count(),
        'total_users_count': User.objects.count(),
        'db_size': 25.5,  # Placeholder - implement database size calculation
    }

    return render(request, 'super_admin/system_settings.html', context)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def create_user_view(request):
    """API endpoint to create a new user."""
    try:
        data = json.loads(request.body)

        # Validate required fields
        if not data.get('username') or not data.get('email') or not data.get('role'):
            return JsonResponse({
                'success': False,
                'message': 'Username, email, and role are required'
            }, status=400)

        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)

        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists'
            }, status=400)

        # Generate password if not provided
        password = data.get('password')
        if not password:
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for _ in range(12))

        # Create user
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone_number=data.get('phone_number', ''),
            role=data['role'],
            license_tier=data.get('license_tier', 'DEMO'),
            is_active=data.get('is_active', True)
        )

        # Assign business if provided
        business_id = data.get('business')
        if business_id:
            try:
                business = Business.objects.get(id=business_id)
                user.business = business
                user.save()
            except Business.DoesNotExist:
                pass

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_CREATED,
            description=f"User {user.username} created",
            user=user,
            performed_by=request.user,
            data={
                'role': user.role,
                'business_id': business_id
            }
        )

        # Create notification
        Notification.objects.create(
            title="New User Created",
            message=f"User {user.username} has been created",
            notification_type=Notification.NotificationType.INFO,
            audience=Notification.Audience.SUPER_ADMINS
        )

        return JsonResponse({
            'success': True,
            'message': 'User created successfully',
            'user_id': user.id,
            'password': password if not data.get('password') else None
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@super_admin_required
def get_user_view(request, user_id):
    """API endpoint to get user details."""
    try:
        user = User.objects.get(id=user_id)

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'role': user.role,
            'license_tier': user.license_tier,
            'business_id': user.business.id if user.business else None,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'date_joined': user.date_joined.isoformat()
        }

        return JsonResponse({
            'success': True,
            'user': user_data
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["PUT"])
@login_required
@super_admin_required
def update_user_view(request, user_id):
    """API endpoint to update user details."""
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)

        # Update fields
        if 'username' in data and data['username'] != user.username:
            if User.objects.filter(username=data['username']).exclude(id=user.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                }, status=400)
            user.username = data['username']

        if 'email' in data and data['email'] != user.email:
            if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                }, status=400)
            user.email = data['email']

        if 'first_name' in data:
            user.first_name = data['first_name']

        if 'last_name' in data:
            user.last_name = data['last_name']

        if 'phone_number' in data:
            user.phone_number = data['phone_number']

        if 'role' in data:
            user.role = data['role']

        if 'license_tier' in data:
            user.license_tier = data['license_tier']

        if 'is_active' in data:
            user.is_active = data['is_active']

        # Update business
        if 'business' in data:
            if data['business']:
                try:
                    business = Business.objects.get(id=data['business'])
                    user.business = business
                except Business.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Business not found'
                    }, status=400)
            else:
                user.business = None

        user.save()

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_UPDATED,
            description=f"User {user.username} updated",
            user=user,
            performed_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'User updated successfully'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def deactivate_user_view(request, user_id):
    """API endpoint to deactivate user."""
    try:
        user = User.objects.get(id=user_id)

        # Cannot deactivate yourself
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'Cannot deactivate your own account'
            }, status=400)

        user.is_active = False
        user.save()

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_UPDATED,
            description=f"User {user.username} deactivated",
            user=user,
            performed_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'User deactivated successfully'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def activate_user_view(request, user_id):
    """API endpoint to activate user."""
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_UPDATED,
            description=f"User {user.username} activated",
            user=user,
            performed_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'User activated successfully'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@csrf_exempt
@require_POST
@login_required
@super_admin_required
def reset_password_view(request, user_id):
    """API endpoint to reset user password."""
    try:
        user = User.objects.get(id=user_id)

        # Generate new password
        alphabet = string.ascii_letters + string.digits
        new_password = ''.join(secrets.choice(alphabet) for _ in range(12))

        user.set_password(new_password)
        user.save()

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_UPDATED,
            description=f"Password reset for user {user.username}",
            user=user,
            performed_by=request.user
        )

        return JsonResponse({
            'success': True,
            'message': 'Password reset successfully',
            'password': new_password
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
@super_admin_required
def delete_user_view(request, user_id):
    """API endpoint to delete user."""
    try:
        user = User.objects.get(id=user_id)

        # Cannot delete yourself
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete your own account'
            }, status=400)

        # Cannot delete super admin if only one exists
        if user.role == User.Role.SUPER_ADMIN:
            super_admin_count = User.objects.filter(
                role=User.Role.SUPER_ADMIN).count()
            if super_admin_count <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot delete the only super admin'
                }, status=400)

        username = user.username
        user.delete()

        # Log activity
        SystemActivity.objects.create(
            activity_type=SystemActivity.ActivityType.USER_DELETED,
            description=f"User {username} deleted",
            performed_by=request.user,
            data={'username': username}
        )

        return JsonResponse({
            'success': True,
            'message': 'User deleted successfully'
        })

    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

# Analytics API Endpoints


@login_required
@super_admin_required
def revenue_analytics_api(request):
    """API endpoint for revenue analytics data."""
    period = request.GET.get('period', '7')

    try:
        days = int(period)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Get revenue data for the period
        revenue_data = Sale.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            revenue=Sum('total_amount')
        ).order_by('date')

        # Format data for chart
        labels = []
        values = []

        for item in revenue_data:
            labels.append(item['date'].strftime('%b %d'))
            values.append(float(item['revenue']) if item['revenue'] else 0)

        return JsonResponse({
            'success': True,
            'labels': labels,
            'values': values
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@super_admin_required
def export_analytics_api(request):
    """API endpoint to export analytics data."""
    from django.http import HttpResponse
    import csv

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics-{timezone.now().date()}.csv"'

    writer = csv.writer(response)

    # Write headers
    writer.writerow(['Metric', 'Value', 'Period', 'Date'])

    # Get current date
    current_date = timezone.now().date()

    # Write revenue data
    revenue_30d = Sale.objects.filter(
        created_at__gte=current_date - timedelta(days=30),
        created_at__lte=timezone.now()
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    writer.writerow(
        ['Total Revenue', f'KSh {revenue_30d:.2f}', 'Last 30 days', current_date])

    # Write user data
    new_users_30d = User.objects.filter(
        date_joined__gte=current_date - timedelta(days=30)
    ).count()

    writer.writerow(['New Users', new_users_30d, 'Last 30 days', current_date])

    # Write business data
    new_businesses_30d = Business.objects.filter(
        created_at__gte=current_date - timedelta(days=30)
    ).count()

    writer.writerow(['New Businesses', new_businesses_30d,
                    'Last 30 days', current_date])

    # Write sales data
    total_sales_30d = Sale.objects.filter(
        created_at__gte=current_date - timedelta(days=30)
    ).count()

    writer.writerow(['Total Sales', total_sales_30d,
                    'Last 30 days', current_date])

    return response
