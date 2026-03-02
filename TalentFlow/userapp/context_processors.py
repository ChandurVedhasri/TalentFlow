from .models import Notification


def notifications(request):
    """Provide recent notifications and unread count to all templates."""
    if getattr(request, 'user', None) and request.user.is_authenticated:
        recent = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        unread = Notification.objects.filter(user=request.user, read=False).count()
        return {
            'recent_notifications': recent,
            'unread_notifications': unread,
        }
    return {}
