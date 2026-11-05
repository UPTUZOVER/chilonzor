from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Users

User = get_user_model()


@receiver(post_save, sender=User)
def sync_profile_with_auth_user(sender, instance, created, **kwargs):
    defaults = {
        "first_name": instance.first_name or instance.username,
        "last_name": instance.last_name,
    }
    profile, profile_created = Users.objects.get_or_create(
        account=instance,
        defaults=defaults,
    )

    update_fields = []
    desired_first_name = instance.first_name or instance.username
    if profile_created:
        return
    if profile.first_name != desired_first_name:
        profile.first_name = desired_first_name
        update_fields.append("first_name")
    if profile.last_name != instance.last_name:
        profile.last_name = instance.last_name
        update_fields.append("last_name")
    if update_fields:
        profile.save(update_fields=update_fields)
