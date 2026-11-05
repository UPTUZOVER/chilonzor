from .permissions import (
    get_role_label,
    user_has_apk_access,
    user_is_apk_only,
    user_is_chilonzor,
    user_is_kursant,
)

EMPTY = {
    "show_apk_nav": False,
    "apk_role_label": "",
    "apk_only_user": False,
    "is_kursant_user": False,
    "is_chilonzor_user": False,
    "apk_new_count": 0,
    "apk_returned_count": 0,
    "apk_review_count": 0,
}


def apk_nav(request):
    """Menyudagi "APK tahlil" bo'limi va nishonlar (kutayotgan ishlar soni)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return dict(EMPTY)

    has_access = user_has_apk_access(user)
    context = dict(EMPTY)
    context.update(
        {
            "show_apk_nav": has_access,
            "apk_role_label": get_role_label(user) if has_access else "",
            "apk_only_user": user_is_apk_only(user),
        }
    )
    if not has_access:
        return context

    from .models import ApkSubmission

    is_kursant = user_is_kursant(user)
    is_chilonzor = user_is_chilonzor(user)
    context["is_kursant_user"] = is_kursant
    context["is_chilonzor_user"] = is_chilonzor

    if is_kursant:
        profile = getattr(user, "profile", None)
        context["apk_new_count"] = ApkSubmission.objects.filter(
            status=ApkSubmission.STATUS_NEW
        ).count()
        if profile is not None:
            context["apk_returned_count"] = ApkSubmission.objects.filter(
                status=ApkSubmission.STATUS_RETURNED, assigned_to=profile
            ).count()
    if is_chilonzor or user.is_staff:
        context["apk_review_count"] = ApkSubmission.objects.filter(
            status=ApkSubmission.STATUS_SENT
        ).count()
    return context
