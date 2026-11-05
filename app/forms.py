from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group

from .models import AdminMessage, Users
from .security import (
    get_active_login_block,
    get_login_block,
    get_login_failure_limit,
    get_login_lockout_message,
    register_login_failure,
    reset_login_failures,
)
from .ui_i18n import (
    display_group_name,
    lazy_translate as _,
    translate,
    translate_password_validation_errors,
)

User = get_user_model()
PUBLIC_REGISTRATION_BLOCKED_GROUPS = ()


def get_public_registration_group_queryset():
    queryset = Group.objects.order_by("name")
    for group_name in PUBLIC_REGISTRATION_BLOCKED_GROUPS:
        queryset = queryset.exclude(name__iexact=group_name)
    return queryset


class StyledFieldsMixin:
    def apply_form_classes(self):
        for field in self.fields.values():
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing_class} form-input".strip()


class BaseStyledForm(StyledFieldsMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_form_classes()


class BaseStyledPlainForm(StyledFieldsMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_form_classes()


class StyledAuthenticationForm(StyledFieldsMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = _("Login")
        self.fields["password"].label = _("Parol")
        self.fields["username"].widget.attrs["placeholder"] = _("Login")
        self.fields["password"].widget.attrs["placeholder"] = _("Parol")
        self.error_messages["invalid_login"] = translate("Login va parol noto'g'ri.")
        self.apply_form_classes()


class LockoutAuthenticationForm(StyledAuthenticationForm):
    def clean(self):
        active_login_block = get_active_login_block(self.request)
        if active_login_block:
            raise forms.ValidationError(
                get_login_lockout_message(active_login_block),
                code="locked_out",
            )

        try:
            cleaned_data = super().clean()
        except forms.ValidationError as exc:
            username = self.data.get("username", "")
            updated_login_block = register_login_failure(self.request, username=username)
            active_login_block = get_active_login_block(self.request)
            if active_login_block:
                raise forms.ValidationError(
                    get_login_lockout_message(active_login_block),
                    code="locked_out",
                ) from exc

            failure_limit = get_login_failure_limit()
            remaining_attempts = max(0, failure_limit - updated_login_block.failed_attempts)
            if updated_login_block.failed_attempts < failure_limit:
                raise forms.ValidationError(
                    translate(
                        "Login yoki parol xato. Qolgan urinishlar: {remaining_attempts}.",
                        remaining_attempts=remaining_attempts,
                    ),
                    code="invalid_login",
                ) from exc
            raise

        reset_login_failures(self.request)
        get_login_block(self.request)
        return cleaned_data


class UserCreateForm(BaseStyledPlainForm):
    username = forms.CharField(
        label=_("Login"),
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": _("Login")}),
    )
    first_name = forms.CharField(
        label=_("Ism"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Ism")}),
    )
    last_name = forms.CharField(
        label=_("Familiya"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Familiya")}),
    )
    password = forms.CharField(
        label=_("Parol"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Parol")}, render_value=False),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        label=_("Guruhlar"),
        widget=forms.SelectMultiple(),
    )
    is_staff = forms.BooleanField(required=False, label=_("Admin huquqi"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].label_from_instance = lambda group: display_group_name(group.name)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(translate("Bu login band, boshqasini kiriting."))
        return username

    def save(self):
        account = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            is_staff=self.cleaned_data["is_staff"],
        )
        account.groups.set(self.cleaned_data["groups"])
        profile, _ = Users.objects.get_or_create(
            account=account,
            defaults={
                "first_name": self.cleaned_data["first_name"],
                "last_name": self.cleaned_data["last_name"],
            },
        )
        return profile


class UserUpdateForm(BaseStyledPlainForm):
    username = forms.CharField(
        label=_("Login"),
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": _("Login")}),
    )
    first_name = forms.CharField(
        label=_("Ism"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Ism")}),
    )
    last_name = forms.CharField(
        label=_("Familiya"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Familiya")}),
    )
    password = forms.CharField(
        required=False,
        label=_("Yangi parol"),
        widget=forms.PasswordInput(
            attrs={"placeholder": _("Bo'sh qoldirilsa o'zgarmaydi")},
            render_value=False,
        ),
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        label=_("Guruhlar"),
        widget=forms.SelectMultiple(),
    )
    is_staff = forms.BooleanField(required=False, label=_("Admin huquqi"))

    def __init__(self, *args, profile, can_manage_roles=False, **kwargs):
        self.profile = profile
        self.account = profile.account
        self.can_manage_roles = can_manage_roles
        super().__init__(*args, **kwargs)

        self.fields["first_name"].initial = profile.first_name
        self.fields["last_name"].initial = profile.last_name

        if self.account:
            self.fields["username"].initial = self.account.username
            if self.can_manage_roles:
                self.fields["is_staff"].initial = self.account.is_staff
                self.fields["groups"].initial = self.account.groups.all()
                self.fields["groups"].label_from_instance = lambda group: display_group_name(group.name)

        if not self.can_manage_roles:
            self.fields.pop("groups")
            self.fields.pop("is_staff")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        queryset = User.objects.filter(username=username)
        if self.account:
            queryset = queryset.exclude(pk=self.account.pk)
        if queryset.exists():
            raise forms.ValidationError(translate("Bu login band, boshqasini kiriting."))
        return username

    def clean(self):
        cleaned_data = super().clean()
        if not self.account and not cleaned_data.get("password"):
            self.add_error("password", translate("Yangi login uchun parol kiritilishi kerak."))
        return cleaned_data

    def save(self):
        username = self.cleaned_data["username"]
        first_name = self.cleaned_data["first_name"]
        last_name = self.cleaned_data["last_name"]
        password = self.cleaned_data["password"]
        is_staff = self.cleaned_data.get("is_staff", False)

        if self.account:
            account = self.account
            account.username = username
            account.first_name = first_name
            account.last_name = last_name
            if self.can_manage_roles:
                account.is_staff = is_staff
            if password:
                account.set_password(password)
            account.save()
        else:
            account = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff if self.can_manage_roles else False,
            )
            self.profile.account = account

        if self.can_manage_roles:
            account.groups.set(self.cleaned_data["groups"])

        self.profile.first_name = first_name
        self.profile.last_name = last_name
        self.profile.save()
        return self.profile


class UserRegistrationForm(BaseStyledPlainForm):
    username = forms.CharField(
        label=_("Login"),
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": _("Login")}),
    )
    first_name = forms.CharField(
        label=_("Ism"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Ism")}),
    )
    last_name = forms.CharField(
        label=_("Familiya"),
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": _("Familiya")}),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        empty_label=_("Guruhni tanlang"),
        label=_("Guruh"),
        widget=forms.Select(),
    )
    password1 = forms.CharField(
        label=_("Parol"),
        widget=forms.PasswordInput(attrs={"placeholder": _("Parol")}, render_value=False),
    )
    password2 = forms.CharField(
        label=_("Parolni tasdiqlang"),
        widget=forms.PasswordInput(
            attrs={"placeholder": _("Parolni qayta kiriting")},
            render_value=False,
        ),
    )

    def __init__(self, *args, available_groups=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = (
            available_groups
            if available_groups is not None
            else get_public_registration_group_queryset()
        )
        self.fields["group"].label_from_instance = lambda group: display_group_name(group.name)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(translate("Bu login band, boshqasini kiriting."))
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(translate("Parollar bir xil emas."))
        try:
            password_validation.validate_password(password2)
        except forms.ValidationError as exc:
            raise forms.ValidationError(translate_password_validation_errors(exc)) from exc
        return password2

    def save(self):
        account = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            is_staff=False,
        )
        account.groups.set([self.cleaned_data["group"]])
        return account


class GroupManageForm(BaseStyledPlainForm):
    name = forms.CharField(
        label=_("Guruh nomi"),
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": _("Masalan: Alpha Team")}),
    )

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields["name"].initial = self.instance.name

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        queryset = Group.objects.filter(name__iexact=name)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError(translate("Bu nomdagi guruh allaqachon mavjud."))
        return name

    def save(self):
        group = self.instance or Group()
        group.name = self.cleaned_data["name"]
        group.save()
        return group


class AdminMessageForm(BaseStyledPlainForm):
    recipient = forms.ModelChoiceField(
        queryset=Users.objects.none(),
        required=False,
        empty_label=_("Barcha foydalanuvchilar"),
        label=_("Kimga"),
        widget=forms.Select(),
    )
    body = forms.CharField(
        label=_("Xabar"),
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Xabar matnini kiriting"),
                "rows": 5,
            }
        ),
    )

    def __init__(self, *args, recipients=None, initial_recipient=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipient"].queryset = recipients or Users.objects.none()
        if initial_recipient is not None:
            self.fields["recipient"].initial = initial_recipient

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError(translate("Xabar matni bo'sh bo'lmasligi kerak."))
        return body

    def save(self, *, sender):
        return AdminMessage.objects.create(
            sender=sender,
            recipient=self.cleaned_data.get("recipient"),
            body=self.cleaned_data["body"],
        )


class UserFilterForm(BaseStyledPlainForm):
    search = forms.CharField(required=False, label=_("Qidirish"))
    group = forms.ModelChoiceField(
        queryset=Group.objects.none(),
        required=False,
        empty_label=_("Barcha guruhlar"),
        label=_("Guruh"),
    )
    ordering = forms.ChoiceField(
        required=False,
        label=_("Saralash"),
        choices=(
            ("name_asc", _("Ism A-Z")),
            ("name_desc", _("Ism Z-A")),
            ("latest", _("Eng yangi")),
            ("oldest", _("Eng eski")),
        ),
        initial="name_asc",
    )

    def __init__(self, *args, visible_groups=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = visible_groups or Group.objects.none()
        self.fields["group"].label_from_instance = lambda group: display_group_name(group.name)
