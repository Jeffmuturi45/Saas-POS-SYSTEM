# businesses/actions.py
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from .models import Business
from licenses.models import License
from superadmin.models import SystemActivity, Notification
from accounts.models import User


def renew_license(business_id, duration_days, tier=None, performed_by=None):
    """Renew business license."""
    try:
        with transaction.atomic():
            business = Business.objects.get(id=business_id)
            license_obj = business.license

            # Update license
            if tier:
                license_obj.tier = tier

            # Calculate new end date
            if license_obj.end_date and license_obj.end_date > timezone.now().date():
                # Extend from current end date
                new_end_date = license_obj.end_date + \
                    timedelta(days=duration_days)
            else:
                # Start from today
                new_end_date = timezone.now().date() + timedelta(days=duration_days)

            license_obj.end_date = new_end_date
            license_obj.is_active = True
            license_obj.save()

            # Log activity
            SystemActivity.objects.create(
                activity_type=SystemActivity.ActivityType.LICENSE_RENEWED,
                description=f"License renewed for {business.name}",
                business=business,
                performed_by=performed_by,
                data={
                    'license_id': license_obj.id,
                    'tier': license_obj.tier,
                    'duration_days': duration_days,
                    'new_end_date': new_end_date.isoformat()
                }
            )

            # Create notification for business admin
            Notification.objects.create(
                title="License Renewed",
                message=f"Your license has been renewed until {new_end_date.strftime('%B %d, %Y')}",
                notification_type=Notification.NotificationType.SUCCESS,
                audience=Notification.Audience.SPECIFIC_BUSINESS,
                business=business,
                data={'license_id': license_obj.id}
            )

            return True, "License renewed successfully"
    except Business.DoesNotExist:
        return False, "Business not found"
    except Exception as e:
        return False, str(e)


def suspend_business(business_id, reason, performed_by=None):
    """Suspend a business."""
    try:
        with transaction.atomic():
            business = Business.objects.get(id=business_id)
            business.status = Business.Status.SUSPENDED
            business.save()

            # Log activity
            SystemActivity.objects.create(
                activity_type=SystemActivity.ActivityType.BUSINESS_SUSPENDED,
                description=f"Business {business.name} suspended",
                business=business,
                performed_by=performed_by,
                data={'reason': reason}
            )

            # Create notification for business admin
            Notification.objects.create(
                title="Account Suspended",
                message=f"Your account has been suspended. Reason: {reason}",
                notification_type=Notification.NotificationType.WARNING,
                audience=Notification.Audience.SPECIFIC_BUSINESS,
                business=business,
                data={'reason': reason}
            )

            return True, "Business suspended successfully"
    except Business.DoesNotExist:
        return False, "Business not found"
    except Exception as e:
        return False, str(e)


def activate_business(business_id, performed_by=None):
    """Activate a suspended business."""
    try:
        with transaction.atomic():
            business = Business.objects.get(id=business_id)
            business.status = Business.Status.ACTIVE
            business.save()

            # Log activity
            SystemActivity.objects.create(
                activity_type=SystemActivity.ActivityType.BUSINESS_ACTIVATED,
                description=f"Business {business.name} activated",
                business=business,
                performed_by=performed_by
            )

            # Create notification for business admin
            Notification.objects.create(
                title="Account Activated",
                message="Your account has been activated and is now active.",
                notification_type=Notification.NotificationType.SUCCESS,
                audience=Notification.Audience.SPECIFIC_BUSINESS,
                business=business
            )

            return True, "Business activated successfully"
    except Business.DoesNotExist:
        return False, "Business not found"
    except Exception as e:
        return False, str(e)


def delete_business(business_id, performed_by=None):
    """Delete a business (soft delete)."""
    try:
        with transaction.atomic():
            business = Business.objects.get(id=business_id)
            business_name = business.name
            business_email = business.email

            # Log activity before deletion
            SystemActivity.objects.create(
                activity_type=SystemActivity.ActivityType.BUSINESS_DELETED,
                description=f"Business {business_name} deleted",
                performed_by=performed_by,
                data={
                    'business_name': business_name,
                    'business_email': business_email
                }
            )

            # Actually delete (or you could do soft delete)
            business.delete()

            return True, "Business deleted successfully"
    except Business.DoesNotExist:
        return False, "Business not found"
    except Exception as e:
        return False, str(e)


def create_license_request_notification(business, requested_tier, requested_duration):
    """Create notification when business requests license renewal."""
    Notification.objects.create(
        title="License Renewal Request",
        message=f"{business.name} has requested license renewal to {requested_tier} tier for {requested_duration} days",
        notification_type=Notification.NotificationType.LICENSE,
        audience=Notification.Audience.SUPER_ADMINS,
        business=business,
        data={
            'requested_tier': requested_tier,
            'requested_duration': requested_duration,
            'business_id': business.id
        },
        action_url=f"/super-admin/businesses/?view={business.id}",
        action_text="Review Request"
    )
