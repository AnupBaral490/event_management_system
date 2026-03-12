from django.core.mail import send_mail

from .models import EmailLog, Notification


def create_notification(user, title, message, notification_type='SYSTEM', event=None):
    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        event=event,
    )


def send_email_notification(subject, body, to_email):
    success = True
    try:
        send_mail(subject, body, None, [to_email], fail_silently=False)
    except Exception:
        success = False
    EmailLog.objects.create(to_email=to_email, subject=subject, body=body, success=success)
    return success
