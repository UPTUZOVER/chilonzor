from .models import Users
from .ui_i18n import get_language_options, get_language_from_request


def ui_i18n(request):
    message_unread_count = 0
    if request.user.is_authenticated:
        profile = getattr(request, "_message_profile", None)
        if profile is None:
            profile = getattr(request.user, "profile", None)
            if profile is None:
                profile, _ = Users.objects.get_or_create(
                    account=request.user,
                    defaults={
                        "first_name": request.user.first_name or request.user.username,
                        "last_name": request.user.last_name,
                    },
                )
            request._message_profile = profile
        message_unread_count = profile.unread_message_count()

    return {
        "ui_language": getattr(request, "ui_language", get_language_from_request(request)),
        "ui_languages": get_language_options(),
        "message_unread_count": message_unread_count,
    }
