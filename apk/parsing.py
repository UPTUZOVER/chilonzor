"""Kursant kiritgan IP, domen va Telegram ID qiymatlarini tekshirish va bir xil ko'rinishga keltirish.

Bir xil qiymat turlicha yozilib ("Example.COM", "http://example.com/x") qolmasligi
kerak - aks holda takrorlanishlarni topib bo'lmaydi."""

import ipaddress
import re
from urllib.parse import urlsplit

from app.ui_i18n import translate

KIND_IP = "ip"
KIND_DOMAIN = "domain"
KIND_TELEGRAM = "telegram"

_IPV4_WITH_PORT = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$")
_IPV6_WITH_PORT = re.compile(r"^\[([0-9a-fA-F:.]+)\]:(\d{1,5})$")
_DOMAIN_LABEL = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")
_TELEGRAM_USERNAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{4,31}$")
_TELEGRAM_NUMERIC = re.compile(r"^-?\d{5,16}$")
_TELEGRAM_LINK = re.compile(
    r"^(?:https?://)?(?:www\.)?(?:t|telegram)\.me/([A-Za-z][A-Za-z0-9_]{4,31})/?$",
    re.IGNORECASE,
)


def _host_from_text(raw):
    """URL yoki "host:port/yo'l" ko'rinishidagi matndan host qismini ajratadi."""
    text = raw.strip()
    if "://" not in text:
        text = "//" + text
    try:
        return urlsplit(text).hostname or ""
    except ValueError:
        return ""


def _check_port(port_text):
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError(translate("Port 1 dan 65535 gacha bo'lishi kerak."))
    return port


def normalize_ip(raw):
    text = (raw or "").strip()
    if "://" in text or "/" in text:
        text = _host_from_text(text) or text

    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        pass

    match = _IPV4_WITH_PORT.match(text)
    if match:
        try:
            address = ipaddress.IPv4Address(match.group(1))
        except ValueError:
            raise ValueError(translate("IP manzil noto'g'ri.")) from None
        return f"{address}:{_check_port(match.group(2))}"

    match = _IPV6_WITH_PORT.match(text)
    if match:
        try:
            address = ipaddress.IPv6Address(match.group(1))
        except ValueError:
            raise ValueError(translate("IP manzil noto'g'ri.")) from None
        return f"[{address}]:{_check_port(match.group(2))}"

    raise ValueError(translate("IP manzil noto'g'ri."))


def normalize_domain(raw):
    text = (raw or "").strip()
    if not text:
        raise ValueError(translate("Domen bo'sh."))
    host = _host_from_text(text) if ("://" in text or "/" in text or ":" in text) else text
    host = host.strip().strip(".").lower()
    if not host or len(host) > 253:
        raise ValueError(translate("Domen noto'g'ri."))

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError(translate("Bu IP manzil, domen emas - IP bo'limiga kiriting."))

    labels = host.split(".")
    if len(labels) < 2 or not all(_DOMAIN_LABEL.match(label) for label in labels):
        raise ValueError(translate("Domen noto'g'ri."))
    tld = labels[-1]
    if not (tld.startswith("xn--") or (tld.isalpha() and 2 <= len(tld) <= 24)):
        raise ValueError(translate("Domen noto'g'ri."))
    return host


def normalize_telegram(raw):
    """Raqamli ID ("5907562354", "-1003542328393") yoki username ("@name", "t.me/name")."""
    text = (raw or "").strip()
    if _TELEGRAM_NUMERIC.match(text):
        return text

    link = _TELEGRAM_LINK.match(text)
    if link:
        return "@" + link.group(1).lower()

    bare = text[1:] if text.startswith("@") else text
    if _TELEGRAM_USERNAME.match(bare):
        return "@" + bare.lower()

    raise ValueError(
        translate("Telegram ID noto'g'ri: raqamli ID yoki @username kiriting.")
    )


NORMALIZERS = {
    KIND_IP: normalize_ip,
    KIND_DOMAIN: normalize_domain,
    KIND_TELEGRAM: normalize_telegram,
}


def normalize_finding(kind, raw):
    try:
        normalizer = NORMALIZERS[kind]
    except KeyError:
        raise ValueError(translate("Noma'lum tur.")) from None
    return normalizer(raw)


def parse_lines(kind, text):
    """Ko'p qatorli matnni tekshiradi: (to'g'ri qiymatlar, [(qator, xato), ...]).

    Bo'sh qatorlar o'tkazib yuboriladi, takrorlar bittaga qisqartiriladi."""
    values = []
    errors = []
    seen = set()
    for line in (text or "").splitlines():
        line = line.strip().strip(",;")
        if not line:
            continue
        try:
            value = normalize_finding(kind, line)
        except ValueError as exc:
            errors.append((line, str(exc)))
            continue
        if value not in seen:
            seen.add(value)
            values.append(value)
    return values, errors
