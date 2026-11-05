from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AdminMessage, LoginBlock, Users

User = get_user_model()


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "first_name", "last_name", "is_staff", "is_active")


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ("account", "first_name", "last_name", "created_at")
    search_fields = ("account__username", "first_name", "last_name")
    ordering = ("first_name",)


@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "recipient", "created_at")
    search_fields = ("body", "sender__first_name", "recipient__first_name")


@admin.register(LoginBlock)
class LoginBlockAdmin(admin.ModelAdmin):
    list_display = ("source_ip", "failed_attempts", "last_attempt_at", "blocked_until", "last_username")
    search_fields = ("source_ip", "last_username")
