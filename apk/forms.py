from django import forms
from django.db.models import Q

from app.forms import BaseStyledForm, BaseStyledPlainForm
from app.models import Users
from app.ui_i18n import lazy_translate as _, translate

from .models import ApiClient, ApkFinding, Kursant
from .parsing import parse_lines
from .permissions import GROUP_MVD, ROLE_GROUPS


class FindingsForm(BaseStyledPlainForm):
    """Uch turdagi topilmalarni bir vaqtda, har qatorda bittadan qo'shish."""

    FINDING_FIELDS = (
        ("ip_values", ApkFinding.KIND_IP),
        ("domain_values", ApkFinding.KIND_DOMAIN),
        ("telegram_values", ApkFinding.KIND_TELEGRAM),
    )

    ip_values = forms.CharField(
        required=False,
        label=_("IP manzili"),
        help_text=_("Har qatorda bittadan IP manzil kiriting. Port ham ko'rsatilishi mumkin."),
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": _("192.168.1.10\n203.0.113.5:8080"),
            }
        ),
    )
    domain_values = forms.CharField(
        required=False,
        label=_("Domen"),
        help_text=_("Har qatorda bittadan domen kiriting."),
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "example.com\npanel.example.org"}),
    )
    telegram_values = forms.CharField(
        required=False,
        label=_("Telegram ID"),
        help_text=_("Har qatorda bittadan raqamli ID yoki @username kiriting."),
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "5907562354\n@username"}),
    )

    def clean(self):
        cleaned = super().clean()
        parsed_values = {}
        for field_name, kind in self.FINDING_FIELDS:
            values, errors = parse_lines(kind, cleaned.get(field_name, ""))
            parsed_values[kind] = values
            if errors:
                self.add_error(
                    field_name,
                    "; ".join(f"{line}: {message}" for line, message in errors[:5])
                    + ("..." if len(errors) > 5 else ""),
                )
        if not self.errors and not any(parsed_values.values()):
            raise forms.ValidationError(translate("Kamida bitta qiymat kiriting."))
        cleaned["parsed_values"] = parsed_values
        return cleaned


class AnalysisNoteForm(BaseStyledPlainForm):
    analysis_note = forms.CharField(
        required=False,
        label=_("Tahlil izohi"),
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": _("Qanday tahlil qilindi, qayerdan topildi...")}
        ),
    )


class ReviewForm(BaseStyledPlainForm):
    note = forms.CharField(
        required=False,
        label=_("Izoh / kamchiliklar"),
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": _("Qaytarishda kamchiliklarni yozing")}
        ),
    )


class KursantForm(BaseStyledForm):
    """Admin jadvalga yangi ustun (kursant) qo'shadi."""

    class Meta:
        model = Kursant
        fields = ["user", "team", "sort_order", "is_active"]
        widgets = {
            "team": forms.TextInput(attrs={"placeholder": _("Masalan: 1-guruh")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # MVD / Chilonzor xodimlari kursant bo'lmaydi - ular alohida rollar.
        queryset = (
            Users.objects.select_related("account")
            .filter(account__isnull=False)
            .exclude(account__groups__name__in=ROLE_GROUPS)
        )
        if self.instance and self.instance.pk:
            queryset = queryset.filter(
                Q(kursant_profile__isnull=True) | Q(kursant_profile=self.instance)
            )
        else:
            queryset = queryset.filter(kursant_profile__isnull=True)
        self.fields["user"].queryset = queryset.order_by("first_name", "last_name")
        self.fields["user"].label_from_instance = lambda profile: str(profile)


class ApiClientForm(BaseStyledPlainForm):
    name = forms.CharField(
        max_length=100,
        label=_("Nomi"),
        widget=forms.TextInput(attrs={"placeholder": _("Masalan: Telegram bot")}),
    )
    user = forms.ModelChoiceField(
        queryset=Users.objects.none(),
        label=_("MVD hisobi"),
        help_text=_("Bot yuborgan hamma yozuvlarda manba sifatida shu MVD ko'rinadi."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = (
            Users.objects.select_related("account")
            .filter(account__groups__name__iexact=GROUP_MVD, account__is_active=True)
            .distinct()
            .order_by("first_name", "last_name")
        )
        self.fields["user"].label_from_instance = lambda profile: (
            f"{profile} ({profile.account.username})"
        )

    def save(self):
        client, raw_token = ApiClient.create_with_token(
            self.cleaned_data["name"], self.cleaned_data["user"]
        )
        return client, raw_token
