from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import (
    AdminMessageForm,
    GroupManageForm,
    LockoutAuthenticationForm,
    UserCreateForm,
    UserFilterForm,
    UserUpdateForm,
)
from .models import AdminMessage, Users
from .ui_i18n import (
    UI_LANGUAGE_SESSION_KEY,
    display_group_name,
    normalize_language,
    translate,
)


def post_rate_limit(limit=5, timeout=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method == "POST" and request.user.is_authenticated:
                # Har bir foydalanuvchi (PK) va funksiya uchun alohida xotira kaliti yaratiladi
                cache_key = f"rl_{request.user.pk}_{view_func.__name__}"
                try:
                    cache.add(cache_key, 0, timeout)
                    count = cache.incr(cache_key)
                except Exception:
                    count = cache.get(cache_key, 0) + 1
                    cache.set(cache_key, count, timeout)

                if count > limit:
                    messages.error(request, translate("Siz 1 daqiqada ruxsat etilgan so'rovlar limitidan (5 ta) oshib ketdingiz. Iltimos, bir oz kuting."))
                    return redirect(request.path)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class SecureLoginView(LoginView):
    authentication_form = LockoutAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_invalid(self, form):
        error_codes = {
            error.code
            for errors in form.errors.as_data().values()
            for error in errors
        }
        response = super().form_invalid(form)
        if "locked_out" in error_codes:
            response.status_code = 429
        return response


@require_POST
def set_language_view(request):
    language = normalize_language(request.POST.get("language"))
    request.session[UI_LANGUAGE_SESSION_KEY] = language
    next_url = request.POST.get("next") or reverse("app:home")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("app:home")
    return redirect(next_url)


@login_required
def home_view(request):
    """Bosh sahifa: APK bo'limiga ruxsati borlar to'g'ridan-to'g'ri o'sha yerga
    yuboriladi, qolganlar ruxsat yo'qligi haqidagi sahifani ko'radi."""
    from apk.permissions import user_has_apk_access

    if user_has_apk_access(request.user):
        return redirect("apk:home")
    return render(request, "app/no_access.html")


def get_or_create_profile(user):
    profile, _ = Users.objects.get_or_create(
        account=user,
        defaults={
            "first_name": user.first_name or user.username,
            "last_name": user.last_name,
        },
    )
    update_fields = []
    fallback_first_name = user.first_name or user.username
    if not profile.first_name and fallback_first_name:
        profile.first_name = fallback_first_name
        update_fields.append("first_name")
    if not profile.last_name and user.last_name:
        profile.last_name = user.last_name
        update_fields.append("last_name")
    if update_fields:
        profile.save(update_fields=update_fields)
    return profile


def account_has_group(account, group_name):
    if not account:
        return False

    prefetched_objects = getattr(account, "_prefetched_objects_cache", {})
    prefetched_groups = prefetched_objects.get("groups")
    normalized_group_name = group_name.casefold()
    if prefetched_groups is not None:
        return any(group.name.casefold() == normalized_group_name for group in prefetched_groups)
    return account.groups.filter(name__iexact=group_name).exists()


def get_role_label_for_account(account):
    """Ro'yxatda ko'rinadigan rol: Admin / MVD / Chilonzor / Kursant (bir nechtasi bo'lishi mumkin)."""
    if not account:
        return translate("Foydalanuvchi")
    from apk.permissions import get_role_label

    return get_role_label(account) or translate("Rol berilmagan")


def require_admin_or_redirect(request):
    if request.user.is_staff:
        return None
    messages.error(request, translate("Bu bo'lim faqat admin uchun."))
    return redirect("app:home")


def get_group_ids_for_user(user):
    return list(user.groups.values_list("id", flat=True))


def get_visible_user_queryset_for_user(user):
    queryset = Users.objects.select_related("account").prefetch_related("account__groups")
    if user.is_staff:
        return queryset

    profile = get_or_create_profile(user)
    group_ids = get_group_ids_for_user(user)
    if not group_ids:
        return queryset.filter(pk=profile.pk)
    return queryset.filter(Q(pk=profile.pk) | Q(account__groups__id__in=group_ids)).distinct()


def get_visible_user_queryset_for_request(request):
    return get_visible_user_queryset_for_user(request.user)


def get_visible_group_queryset_for_user(user):
    if user.is_staff:
        return Group.objects.order_by("name")

    group_ids = get_group_ids_for_user(user)
    if not group_ids:
        return Group.objects.none()
    return Group.objects.filter(id__in=group_ids).order_by("name")


def get_visible_group_queryset_for_request(request):
    return get_visible_group_queryset_for_user(request.user)


def get_messageable_user_queryset():
    return (
        Users.objects.select_related("account")
        .prefetch_related("account__groups")
        .filter(account__isnull=False)
        .order_by("first_name", "last_name", "pk")
    )


def get_message_thread_profile_for_request(request, pk=None):
    current_profile = get_or_create_profile(request.user)
    if pk is None:
        return current_profile

    profile = get_object_or_404(get_messageable_user_queryset(), pk=pk)
    if request.user.is_staff or profile.account_id == request.user.id:
        return profile
    raise Http404("Bu xabar oynasi siz uchun yopiq.")


def get_message_queryset_for_profile(profile):
    return (
        AdminMessage.objects.select_related(
            "sender",
            "sender__account",
            "recipient",
            "recipient__account",
        )
        .prefetch_related("sender__account__groups", "recipient__account__groups")
        .filter(Q(recipient=profile) | Q(recipient__isnull=True))
        .order_by("created_at", "id")
    )


@login_required
@post_rate_limit(limit=5, timeout=60)
def message_inbox_view(request, pk=None):
    current_profile = get_or_create_profile(request.user)
    request._message_profile = current_profile
    thread_profile = get_message_thread_profile_for_request(request, pk=pk)
    can_send_messages = request.user.is_staff
    recipient_queryset = get_messageable_user_queryset()
    initial_recipient = None
    if can_send_messages and thread_profile.pk != current_profile.pk:
        initial_recipient = thread_profile

    if can_send_messages:
        form = AdminMessageForm(
            request.POST or None,
            recipients=recipient_queryset,
            initial_recipient=initial_recipient,
        )
        if request.method == "POST" and form.is_valid():
            created_message = form.save(sender=current_profile)
            if created_message.recipient_id:
                messages.success(
                    request,
                    translate("Xabar {recipient} ga yuborildi.", recipient=created_message.recipient),
                )
                return redirect("app:message_thread", pk=created_message.recipient_id)
            messages.success(request, translate("Hammaga e'lon yuborildi."))
            return redirect("app:message_thread", pk=thread_profile.pk)
    else:
        form = None
        if request.method == "POST":
            messages.error(request, translate("Xabar yuborish faqat admin uchun."))
            return redirect("app:message_inbox")

    if not can_send_messages:
        current_profile.mark_messages_read()

    thread_messages = list(get_message_queryset_for_profile(thread_profile))
    # Shaxsan shu foydalanuvchiga yo'llangan xabarlar (masalan, firibgarlik
    # bo'limidagi tasdiqlash bildirishnomalari) hammaga yuborilgan e'lonlar
    # bilan bir qatorda yo'qolib qolmasligi uchun ikkiga ajratib chiqariladi.
    personal_messages = [item for item in thread_messages if not item.is_broadcast]
    broadcast_messages = [item for item in thread_messages if item.is_broadcast]
    thread_users = list(recipient_queryset) if can_send_messages else []

    # MVD xodimlari faqat o'zlariga tegishli (shaxsiy) xabarlarni ko'radi -
    # hammaga yuborilgan umumiy e'lonlar ularga ko'rsatilmaydi.
    show_broadcast_messages = True
    if not can_send_messages and account_has_group(request.user, "MVD"):
        show_broadcast_messages = False
        broadcast_messages = []

    return render(
        request,
        "app/messages.html",
        {
            "thread_profile": thread_profile,
            "thread_messages": thread_messages,
            "personal_messages": personal_messages,
            "broadcast_messages": broadcast_messages,
            "show_broadcast_messages": show_broadcast_messages,
            "current_profile": current_profile,
            "thread_users": thread_users,
            "message_form": form,
            "can_send_messages": can_send_messages,
        },
    )


@login_required
def user_list_view(request):
    visible_groups = get_visible_group_queryset_for_request(request)
    filter_form = UserFilterForm(request.GET or None, visible_groups=visible_groups)
    users = get_visible_user_queryset_for_request(request)
    total_visible_user_count = users.count()

    if filter_form.is_valid():
        search = filter_form.cleaned_data.get("search")
        group = filter_form.cleaned_data.get("group")
        ordering = filter_form.cleaned_data.get("ordering") or "name_asc"

        if search:
            users = users.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(account__username__icontains=search)
            )
        if group:
            users = users.filter(account__groups=group)

        order_map = {
            "name_asc": ["first_name", "last_name"],
            "name_desc": ["-first_name", "-last_name"],
            "latest": ["-created_at", "first_name"],
            "oldest": ["created_at", "first_name"],
        }
        users = users.order_by(*order_map.get(ordering, order_map["name_asc"]))

    filtered_user_count = users.count()
    users = list(users)
    for user in users:
        user.role_label = get_role_label_for_account(user.account)

    return render(
        request,
        "app/user_list.html",
        {
            "users": users,
            "filtered_user_count": filtered_user_count,
            "filter_form": filter_form,
            "can_manage_users": request.user.is_staff,
            "total_visible_user_count": total_visible_user_count,
        },
    )


@login_required
def group_list_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    groups = Group.objects.annotate(member_count=Count("user")).order_by("name")
    return render(request, "app/group_list.html", {"groups": groups})


@login_required
def group_create_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    form = GroupManageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, translate("Yangi guruh qo'shildi."))
        return redirect("app:group_list")

    return render(
        request,
        "app/form_page.html",
        {
            "form": form,
            "page_title": translate("Yangi Guruh"),
            "submit_text": translate("Saqlash"),
            "back_url": reverse("app:group_list"),
        },
    )


@login_required
def group_update_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    group = get_object_or_404(Group, pk=pk)
    form = GroupManageForm(request.POST or None, instance=group)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, translate("Guruh yangilandi."))
        return redirect("app:group_list")

    return render(
        request,
        "app/form_page.html",
        {
            "form": form,
            "page_title": translate("Guruhni Tahrirlash"),
            "submit_text": translate("Yangilash"),
            "back_url": reverse("app:group_list"),
        },
    )


@login_required
def group_delete_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    group = get_object_or_404(Group, pk=pk)
    if request.method == "POST":
        group.delete()
        messages.success(request, translate("Guruh o'chirildi."))
    return redirect("app:group_list")


@login_required
def user_create_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, translate("Yangi foydalanuvchi qo'shildi."))
        return redirect("app:user_list")
    return render(
        request,
        "app/form_page.html",
        {
            "form": form,
            "page_title": translate("Yangi foydalanuvchi"),
            "submit_text": translate("Saqlash"),
            "back_url": reverse("app:user_list"),
        },
    )


@login_required
def user_update_view(request, pk):
    queryset = Users.objects.select_related("account")
    if request.user.is_staff:
        user = get_object_or_404(queryset, pk=pk)
    else:
        user = get_object_or_404(queryset, pk=pk, account=request.user)

    form = UserUpdateForm(
        request.POST or None,
        profile=user,
        can_manage_roles=request.user.is_staff,
    )
    if request.method == "POST" and form.is_valid():
        updated_user = form.save()
        if updated_user.account and request.user.pk == updated_user.account.pk and form.cleaned_data.get(
            "password"
        ):
            update_session_auth_hash(request, updated_user.account)
        messages.success(request, translate("Foydalanuvchi yangilandi."))
        return redirect("app:user_list")
    return render(
        request,
        "app/form_page.html",
        {
            "form": form,
            "page_title": translate("Foydalanuvchini tahrirlash"),
            "submit_text": translate("Yangilash"),
            "back_url": reverse("app:user_list"),
        },
    )


@login_required
def user_delete_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    user = get_object_or_404(Users.objects.select_related("account"), pk=pk)
    if request.method == "POST":
        if user.account:
            user.account.delete()
        else:
            user.delete()
        messages.success(request, translate("Foydalanuvchi o'chirildi."))
    return redirect("app:user_list")
