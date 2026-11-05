from django.contrib import admin

from .models import ApiClient, ApkEvent, ApkFinding, ApkSubmission, Kursant


@admin.register(Kursant)
class KursantAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "sort_order", "is_active")
    list_filter = ("is_active", "team")


class ApkFindingInline(admin.TabularInline):
    model = ApkFinding
    extra = 0
    raw_id_fields = ("added_by",)


@admin.register(ApkSubmission)
class ApkSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "file_name", "status", "assigned_to", "sender_username", "chat_title", "created_at",
    )
    list_filter = ("status",)
    search_fields = ("file_name", "sha256", "sender_name", "sender_username", "chat_title")
    readonly_fields = ("sha256", "file_size", "created_at", "updated_at")
    raw_id_fields = ("assigned_to", "source", "reviewed_by", "duplicate_of")
    inlines = [ApkFindingInline]


@admin.register(ApiClient)
class ApiClientAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "token_prefix", "is_active", "created_at", "last_used_at")
    readonly_fields = ("token_hash", "token_prefix", "created_at", "last_used_at")


@admin.register(ApkEvent)
class ApkEventAdmin(admin.ModelAdmin):
    list_display = ("submission", "action", "actor", "created_at")
    list_filter = ("action",)


ApiClientAdmin.has_add_permission = lambda self, request: False
