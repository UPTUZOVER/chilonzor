from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from .ui_i18n import translate

User = get_user_model()


class Users(models.Model):
    """Django akkauntiga bog'langan profil (ism-familiya va xabarlar holati)."""

    account = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        blank=True,
        null=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    messages_last_read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        if full_name:
            return full_name
        if self.account:
            return self.account.username
        return translate("Foydalanuvchi {pk}", pk=self.pk)

    def incoming_messages_queryset(self):
        return AdminMessage.objects.exclude(sender=self).filter(
            Q(recipient=self) | Q(recipient__isnull=True)
        )

    def unread_messages_queryset(self):
        queryset = self.incoming_messages_queryset()
        if self.messages_last_read_at:
            queryset = queryset.filter(created_at__gt=self.messages_last_read_at)
        return queryset

    def unread_message_count(self):
        return self.unread_messages_queryset().count()

    def mark_messages_read(self):
        latest_message_time = (
            self.incoming_messages_queryset()
            .order_by("-created_at")
            .values_list("created_at", flat=True)
            .first()
        )
        if not latest_message_time:
            return False
        if self.messages_last_read_at and latest_message_time <= self.messages_last_read_at:
            return False
        self.messages_last_read_at = latest_message_time
        self.save(update_fields=["messages_last_read_at"])
        return True


class AdminMessage(models.Model):
    sender = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        blank=True,
        null=True,
        help_text="Bo'sh bo'lsa - tizim tomonidan avtomatik yuborilgan xabar.",
    )
    recipient = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="received_messages",
        blank=True,
        null=True,
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["recipient", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sender_display} -> {self.audience_label}"

    @property
    def is_broadcast(self):
        return self.recipient_id is None

    @property
    def sender_display(self):
        """Tizim o'zi (masalan, karta tasdiqlashga avtomatik yuborilganda)
        yuborgan xabarlarda `sender` bo'sh bo'ladi - shunda o'rniga shu
        matn ko'rsatiladi."""
        if self.sender_id:
            return str(self.sender)
        return translate("Tizim")

    @property
    def audience_label(self):
        if self.is_broadcast:
            return translate("Barcha foydalanuvchilar")
        return str(self.recipient)


class LoginBlock(models.Model):
    source_ip = models.CharField(max_length=64, unique=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    last_attempt_at = models.DateTimeField(blank=True, null=True)
    blocked_until = models.DateTimeField(blank=True, null=True)
    last_username = models.CharField(max_length=150, blank=True)
    last_user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-last_attempt_at", "source_ip"]
        indexes = [
            models.Index(fields=["blocked_until"]),
        ]

    def __str__(self):
        return f"{self.source_ip} - {self.failed_attempts}"
