from decimal import Decimal, InvalidOperation

from django import template

from app.ui_i18n import (
    display_group_name,
    display_role_name,
    display_status_name,
    number_to_uzbek_words,
    translate,
)

register = template.Library()


@register.simple_tag
def t(text, **kwargs):
    return translate(text, **kwargs)


@register.filter
def ui_group(value):
    return display_group_name(value)


@register.filter
def ui_role(value):
    return display_role_name(value)


@register.filter
def ui_status(value):
    return display_status_name(value)


@register.filter
def thousands(value):
    """1345342 yoki 1345342.5 -> "1,345,342" turida mingliklarga ajratib chiqaradi."""
    if value in (None, ""):
        return value
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value
    if number == number.to_integral_value():
        return f"{int(number):,}"
    return f"{number:,}"


@register.filter
def sum_words(value):
    """1200000 -> "bir million ikki yuz ming" turida so'z bilan yozadi."""
    if value in (None, ""):
        return ""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ""
    return number_to_uzbek_words(number)
