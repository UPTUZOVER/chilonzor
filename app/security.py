from datetime import timedelta
import ipaddress

from django.conf import settings
from django.utils import timezone

from .models import LoginBlock
from .ui_i18n import translate

DEFAULT_LOGIN_FAILURE_LIMIT = 7
DEFAULT_LOGIN_LOCKOUT_HOURS = 1


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_login_failure_limit():
    return max(1, int(getattr(settings, "LOGIN_FAILURE_LIMIT", DEFAULT_LOGIN_FAILURE_LIMIT)))


def get_login_lockout_hours():
    return max(1, int(getattr(settings, "LOGIN_LOCKOUT_HOURS", DEFAULT_LOGIN_LOCKOUT_HOURS)))


def get_trust_x_forwarded_for():
    return parse_bool(getattr(settings, "TRUST_X_FORWARDED_FOR", False))


def get_trusted_proxy_hops():
    return max(1, int(getattr(settings, "TRUSTED_PROXY_HOPS", 1)))


def get_trusted_proxy_ips():
    configured_ips = getattr(settings, "TRUSTED_PROXY_IPS", [])
    return {
        str(ip).strip()
        for ip in configured_ips
        if str(ip).strip()
    }


def normalize_ip(value):
    if not value:
        return ""
    try:
        return str(ipaddress.ip_address(str(value).strip()))
    except ValueError:
        return ""


def get_client_ip(request):
    remote_addr = normalize_ip(request.META.get("REMOTE_ADDR"))
    if not remote_addr:
        return "unknown"

    if not get_trust_x_forwarded_for():
        return remote_addr

    trusted_proxy_ips = get_trusted_proxy_ips()
    if not trusted_proxy_ips or remote_addr not in trusted_proxy_ips:
        return remote_addr

    forwarded_for_header = request.META.get("HTTP_X_FORWARDED_FOR") or ""
    forwarded_chain = [
        normalized_ip
        for normalized_ip in (
            normalize_ip(raw_ip)
            for raw_ip in forwarded_for_header.split(",")
        )
        if normalized_ip
    ]
    if not forwarded_chain:
        return remote_addr

    proxy_hops = get_trusted_proxy_hops()
    full_chain = forwarded_chain + [remote_addr]
    if len(full_chain) <= proxy_hops:
        return remote_addr

    trusted_proxy_segment = full_chain[-proxy_hops:]
    if any(proxy_ip not in trusted_proxy_ips for proxy_ip in trusted_proxy_segment):
        return remote_addr

    return full_chain[-(proxy_hops + 1)]


def get_user_agent(request):
    return (request.META.get("HTTP_USER_AGENT") or "")[:255]


def get_login_block(request):
    source_ip = get_client_ip(request)
    login_block, _ = LoginBlock.objects.get_or_create(source_ip=source_ip)
    return reset_expired_login_block(login_block)


def reset_expired_login_block(login_block):
    now = timezone.now()
    if login_block.blocked_until and login_block.blocked_until <= now:
        login_block.failed_attempts = 0
        login_block.blocked_until = None
        login_block.save(update_fields=["failed_attempts", "blocked_until"])
    return login_block


def get_active_login_block(request):
    login_block = get_login_block(request)
    if login_block.blocked_until and login_block.blocked_until > timezone.now():
        return login_block
    return None


def register_login_failure(request, username=""):
    now = timezone.now()
    login_block = get_login_block(request)
    login_block.failed_attempts += 1
    login_block.last_attempt_at = now
    login_block.last_username = (username or "")[:150]
    login_block.last_user_agent = get_user_agent(request)

    update_fields = [
        "failed_attempts",
        "last_attempt_at",
        "last_username",
        "last_user_agent",
    ]
    if login_block.failed_attempts >= get_login_failure_limit():
        login_block.blocked_until = now + timedelta(hours=get_login_lockout_hours())
        update_fields.append("blocked_until")
    login_block.save(update_fields=update_fields)
    return login_block


def reset_login_failures(request):
    login_block = get_login_block(request)
    if not (
        login_block.failed_attempts
        or login_block.blocked_until
        or login_block.last_attempt_at
        or login_block.last_username
        or login_block.last_user_agent
    ):
        return login_block

    login_block.failed_attempts = 0
    login_block.blocked_until = None
    login_block.last_attempt_at = timezone.now()
    login_block.last_username = ""
    login_block.last_user_agent = get_user_agent(request)
    login_block.save(
        update_fields=[
            "failed_attempts",
            "blocked_until",
            "last_attempt_at",
            "last_username",
            "last_user_agent",
        ]
    )
    return login_block


def get_login_lockout_message(login_block):
    blocked_until = timezone.localtime(login_block.blocked_until)
    failure_limit = get_login_failure_limit()
    lockout_hours = get_login_lockout_hours()
    return translate(
        "Bu IP manzil {failure_limit} marta xato urinish sabab {lockout_hours} soatga bloklangan. Qayta kirish vaqti: {blocked_until}.",
        failure_limit=failure_limit,
        lockout_hours=lockout_hours,
        blocked_until=f"{blocked_until:%d.%m.%Y %H:%M}",
    )
