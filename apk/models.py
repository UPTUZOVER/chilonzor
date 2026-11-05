import hashlib
import secrets

from django.db import models
from django.utils import timezone

from app.models import Users
from app.ui_i18n import lazy_translate as _

# Holat CSS klasslari (styles.css: .st-*) - och fon + to'q matn.
STATE_NEW = "st-new"
STATE_PROGRESS = "st-progress"
STATE_SENT = "st-sent"
STATE_RETURNED = "st-returned"
STATE_ACCEPTED = "st-accepted"


class Kursant(models.Model):
    """Kursant - asosiy jadvalda ustun sifatida ko'rinadi va APK ishini oladi."""

    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        related_name="kursant_profile",
        verbose_name=_("Kursant"),
    )
    team = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name=_("Guruh"),
        help_text=_("Bo'sh qoldirilsa \"Guruhsiz\" bo'ladi."),
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Tartib"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["team", "sort_order", "user__first_name", "user__last_name"]
        verbose_name = _("Kursant")
        verbose_name_plural = _("Kursantlar")

    def __str__(self):
        return str(self.user)

    @property
    def team_label(self):
        from app.ui_i18n import translate

        return self.team or translate("Guruhsiz")


class ApiClient(models.Model):
    """APK yuboruvchi (bot) uchun API kaliti.

    Kalit bazada ochiq holda saqlanmaydi - faqat SHA-256 xeshi. Ochiq kalit
    yaratilganda bir marta ko'rsatiladi. Har bir kalit bitta MVD hisobiga
    bog'liq: bot yuborgan hamma yozuvlarda manba sifatida shu MVD ko'rinadi."""

    name = models.CharField(max_length=100, verbose_name=_("Nomi"))
    user = models.ForeignKey(
        Users,
        on_delete=models.PROTECT,
        related_name="api_clients",
        verbose_name=_("MVD hisobi"),
    )
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    token_prefix = models.CharField(max_length=12, editable=False)
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("API kaliti")
        verbose_name_plural = _("API kalitlari")

    def __str__(self):
        return f"{self.name} ({self.token_prefix}...)"

    @staticmethod
    def hash_token(raw_token):
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def create_with_token(cls, name, user):
        """(client, ochiq_kalit) qaytaradi. Ochiq kalitni keyin ko'rib bo'lmaydi."""
        raw_token = secrets.token_urlsafe(32)
        client = cls.objects.create(
            name=name,
            user=user,
            token_hash=cls.hash_token(raw_token),
            token_prefix=raw_token[:8],
        )
        return client, raw_token

    @classmethod
    def authenticate(cls, raw_token):
        if not raw_token:
            return None
        client = (
            cls.objects.select_related("user", "user__account")
            .filter(token_hash=cls.hash_token(raw_token), is_active=True)
            .first()
        )
        if client is None:
            return None
        account = client.user.account
        if account is not None and not account.is_active:
            return None
        return client


class ApkSubmission(models.Model):
    """Botdan kelgan bitta APK - jadvalning bir qatori (bir "ish")."""

    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SENT = "sent"
    STATUS_RETURNED = "returned"
    STATUS_ACCEPTED = "accepted"

    STATUS_CHOICES = (
        (STATUS_NEW, _("Yangi")),
        (STATUS_IN_PROGRESS, _("Tahlilda")),
        (STATUS_SENT, _("Yuborildi")),
        (STATUS_RETURNED, _("Qaytarildi")),
        (STATUS_ACCEPTED, _("Qabul qilindi")),
    )
    # Rang izohidagi qisqa tushuntirish
    STATUS_HINTS = {
        STATUS_NEW: _("hech kim olmagan"),
        STATUS_IN_PROGRESS: _("kursant tahlil qilmoqda"),
        STATUS_SENT: _("Chilonzor ko'rib chiqmoqda"),
        STATUS_RETURNED: _("kamchilik bor, kursant tuzatadi"),
        STATUS_ACCEPTED: _("Chilonzor tasdiqladi"),
    }
    STATUS_COLORS = {
        STATUS_NEW: STATE_NEW,
        STATUS_IN_PROGRESS: STATE_PROGRESS,
        STATUS_SENT: STATE_SENT,
        STATUS_RETURNED: STATE_RETURNED,
        STATUS_ACCEPTED: STATE_ACCEPTED,
    }
    # Rang ustiga yoziladigan harf - holat faqat rang bilan berilmasin.
    STATUS_CODES = {
        STATUS_NEW: "N",
        STATUS_IN_PROGRESS: "J",
        STATUS_SENT: "Y",
        STATUS_RETURNED: "Q",
        STATUS_ACCEPTED: "K",
    }
    # Kursant ishlay oladigan (tahrirlash mumkin) holatlar.
    EDITABLE_STATUSES = (STATUS_IN_PROGRESS, STATUS_RETURNED)

    # --- Bot yuborgan ma'lumot ---
    sender_name = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Yuborgan profil nomi")
    )
    sender_username = models.CharField(
        max_length=64, blank=True, default="", verbose_name=_("Yuborgan username")
    )
    sender_user_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, verbose_name=_("Yuborgan user ID")
    )
    chat_title = models.CharField(
        max_length=255, blank=True, default="", verbose_name=_("Guruh nomi")
    )
    chat_type = models.CharField(
        max_length=32, blank=True, default="", verbose_name=_("Guruh turi")
    )
    chat_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, verbose_name=_("Guruh ID")
    )

    file = models.FileField(upload_to="apk/%Y/%m/", verbose_name=_("APK fayl"))
    file_name = models.CharField(max_length=255, verbose_name=_("Fayl nomi"))
    file_size = models.BigIntegerField(default=0, verbose_name=_("Fayl hajmi (bayt)"))
    sha256 = models.CharField(max_length=64, db_index=True, verbose_name="SHA-256")
    duplicate_of = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicates",
        verbose_name=_("Oldin kelgan nusxa"),
    )
    source = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_apks",
        verbose_name=_("Manba (MVD)"),
    )

    # --- Ish oqimi ---
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_NEW, db_index=True,
        verbose_name=_("Holat"),
    )
    assigned_to = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="apk_assignments",
        verbose_name=_("Kursant"),
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    analysis_note = models.TextField(blank=True, default="", verbose_name=_("Tahlil izohi"))
    sent_at = models.DateTimeField(null=True, blank=True)
    return_count = models.PositiveIntegerField(default=0, verbose_name=_("Qaytarilgan marta"))
    reviewed_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Ko'rib chiqqan (Chilonzor)"),
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True, default="", verbose_name=_("Chilonzor izohi"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Kelgan vaqt"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="apk_status_created_idx"),
        ]
        verbose_name = _("APK ish")
        verbose_name_plural = _("APK ishlar")

    def __str__(self):
        return f"#{self.pk} {self.file_name}"

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, STATE_NEW)

    @property
    def status_code(self):
        return self.STATUS_CODES.get(self.status, "")

    @property
    def sender_username_display(self):
        username = (self.sender_username or "").strip()
        if not username:
            return ""
        return username if username.startswith("@") else f"@{username}"

    @property
    def file_size_display(self):
        size = float(self.file_size or 0)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return ""

    @property
    def is_editable(self):
        return self.status in self.EDITABLE_STATUSES


class ApkFinding(models.Model):
    """Kursant APK ichidan topgan IP, domen yoki Telegram ID."""

    KIND_IP = "ip"
    KIND_DOMAIN = "domain"
    KIND_TELEGRAM = "telegram"

    KIND_CHOICES = (
        (KIND_IP, _("IP manzil")),
        (KIND_DOMAIN, _("Domen")),
        (KIND_TELEGRAM, _("Telegram ID")),
    )

    submission = models.ForeignKey(
        ApkSubmission, on_delete=models.CASCADE, related_name="findings"
    )
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, verbose_name=_("Turi"))
    value = models.CharField(max_length=255, verbose_name=_("Qiymat"))
    added_by = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "kind", "value"], name="unique_apk_finding"
            ),
        ]
        indexes = [
            models.Index(fields=["kind", "value"], name="apk_finding_kind_value_idx"),
        ]
        verbose_name = _("Topilma")
        verbose_name_plural = _("Topilmalar")

    def __str__(self):
        return f"{self.kind}: {self.value}"


class ApkEvent(models.Model):
    """Ish tarixi: kim, qachon, nima qildi (MVD hammasini shu yerdan ko'radi)."""

    ACTION_RECEIVED = "received"
    ACTION_CLAIMED = "claimed"
    ACTION_RELEASED = "released"
    ACTION_SENT = "sent"
    ACTION_RETURNED = "returned"
    ACTION_ACCEPTED = "accepted"

    ACTION_CHOICES = (
        (ACTION_RECEIVED, _("Botdan keldi")),
        (ACTION_CLAIMED, _("Kursant oldi")),
        (ACTION_RELEASED, _("Kursant qaytarib berdi")),
        (ACTION_SENT, _("Chilonzorga yuborildi")),
        (ACTION_RETURNED, _("Chilonzor qaytardi")),
        (ACTION_ACCEPTED, _("Chilonzor qabul qildi")),
    )

    submission = models.ForeignKey(
        ApkSubmission, on_delete=models.CASCADE, related_name="events"
    )
    actor = models.ForeignKey(
        Users, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = _("Tarix yozuvi")
        verbose_name_plural = _("Tarix")

    def __str__(self):
        return f"{self.submission_id} {self.action}"

    @property
    def action_label(self):
        return dict(self.ACTION_CHOICES).get(self.action, self.action)
