# accounts/context_processors.py
from superadmin.models import Notification


def notifications_context(request):
    """Add notifications data to all templates."""
    context = {}

    if request.user.is_authenticated:
        # Get unread notifications count
        unread_count = Notification.objects.filter(
            is_active=True,
            is_read=False
        ).count()

        # Get recent notifications
        recent_notifications = Notification.objects.filter(
            is_active=True
        ).select_related('business').order_by('-created_at')[:5]

        context.update({
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        })

    return context
