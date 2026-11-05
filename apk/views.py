"""APK tahlil bo'limi: botdan kelgan APK -> kursant tahlili -> Chilonzor qarori."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.models import Users
from app.ui_i18n import translate

from . import workflow
from .forms import (
    AnalysisNoteForm,
    ApiClientForm,
    FindingsForm,
    KursantForm,
    ReviewForm,
)
from .models import ApiClient, ApkEvent, ApkFinding, ApkSubmission, Kursant
from .permissions import (
    get_role_label,
    require_admin_or_redirect,
    require_apk_access_or_redirect,
    require_reviewer_or_redirect,
    require_worker_or_redirect,
    user_can_review,
    user_can_work,
    user_is_chilonzor,
    user_is_kursant,
    user_is_mvd,
)

PAGE_SIZE = 50
# Chilonzor navbatida shundan uzoq kutgan ish kechikkan deb belgilanadi.
REVIEW_OVERDUE_HOURS = 48


def status_legend():
    """Rang izohi: har holat uchun rang + harf-kod + qisqa tushuntirish
    (holat faqat rang bilan berilmaydi)."""
    return [
        {
            "color": ApkSubmission.STATUS_COLORS[code],
            "code": ApkSubmission.STATUS_CODES[code],
            "label": str(label),
            "hint": str(ApkSubmission.STATUS_HINTS[code]),
        }
        for code, label in ApkSubmission.STATUS_CHOICES
    ]


def humanize_wait(delta):
    """timedelta -> "3 kun", "5 soat", "12 daqiqa"."""
    seconds = max(int(delta.total_seconds()), 0)
    if seconds >= 86400:
        return translate("{count} kun", count=seconds // 86400)
    if seconds >= 3600:
        return translate("{count} soat", count=seconds // 3600)
    return translate("{count} daqiqa", count=max(seconds // 60, 1))


# --------------------------------------------------------------------------
# Yordamchi funksiyalar
# --------------------------------------------------------------------------


def get_profile_for_user(user):
    profile = getattr(user, "profile", None)
    if profile is not None:
        return profile
    profile, _created = Users.objects.get_or_create(
        account=user,
        defaults={
            "first_name": user.first_name or user.username,
            "last_name": user.last_name,
        },
    )
    return profile


def with_finding_counts(queryset):
    return queryset.annotate(
        ip_count=Count("findings", filter=Q(findings__kind=ApkFinding.KIND_IP), distinct=True),
        domain_count=Count(
            "findings", filter=Q(findings__kind=ApkFinding.KIND_DOMAIN), distinct=True
        ),
        telegram_count=Count(
            "findings", filter=Q(findings__kind=ApkFinding.KIND_TELEGRAM), distinct=True
        ),
    )


def search_filter(queryset, search):
    """Fayl nomi, SHA-256, yuboruvchi, guruh va topilmalar (IP/domen/Telegram ID) bo'yicha."""
    if not search:
        return queryset
    condition = (
        Q(file_name__icontains=search)
        | Q(sha256__istartswith=search)
        | Q(sender_name__icontains=search)
        | Q(sender_username__icontains=search)
        | Q(chat_title__icontains=search)
        | Q(findings__value__icontains=search)
    )
    if search.lstrip("-").isdigit():
        number = int(search)
        condition |= Q(sender_user_id=number) | Q(chat_id=number) | Q(pk=number)
    return queryset.filter(condition).distinct()


def status_filter_options(queryset=None):
    queryset = ApkSubmission.objects.all() if queryset is None else queryset
    counts = {
        row["status"]: row["count"]
        for row in queryset.values("status").annotate(count=Count("id"))
    }
    return [
        {"key": code, "label": str(label), "count": counts.get(code, 0)}
        for code, label in ApkSubmission.STATUS_CHOICES
    ]


# --------------------------------------------------------------------------
# Kirish nuqtasi
# --------------------------------------------------------------------------


@login_required
def home_view(request):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response

    user = request.user
    if user_is_chilonzor(user) and not user.is_staff and not user_is_kursant(user):
        return redirect("apk:review_queue")
    return redirect("apk:submission_list")


# --------------------------------------------------------------------------
# Asosiy jadval
# --------------------------------------------------------------------------


@login_required
def submission_list_view(request):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response

    profile = get_profile_for_user(request.user)
    search = (request.GET.get("q") or "").strip()
    selected_status = request.GET.get("holat") or ""
    selected_scope = request.GET.get("kim") or ""

    base = ApkSubmission.objects.all()
    submissions = with_finding_counts(
        search_filter(base, search).select_related("assigned_to", "source")
    )
    if selected_status:
        submissions = submissions.filter(status=selected_status)
    if selected_scope == "mening":
        submissions = submissions.filter(assigned_to=profile)
    elif selected_scope == "bosh":
        submissions = submissions.filter(status=ApkSubmission.STATUS_NEW)

    paginator = Paginator(submissions.order_by("-created_at", "-id"), PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    kursant_count = Kursant.objects.filter(is_active=True).count()

    my_count = base.filter(assigned_to=profile).count()
    new_count = base.filter(status=ApkSubmission.STATUS_NEW).count()
    filters = [
        {
            "name": "holat",
            "label": translate("Holat"),
            "options": status_filter_options(),
            "selected": selected_status,
        },
        {
            "name": "kim",
            "label": translate("Kim"),
            "options": [
                {"key": "mening", "label": translate("Mening ishlarim"), "count": my_count},
                {"key": "bosh", "label": translate("Olinmaganlar"), "count": new_count},
            ],
            "selected": selected_scope,
        },
    ]
    query = request.GET.copy()
    query.pop("page", None)

    return render(
        request,
        "apk/submission_list.html",
        {
            "submissions": page.object_list,
            "kursant_count": kursant_count,
            "page": page,
            "page_query": query.urlencode(),
            "legend": status_legend(),
            "search": search,
            "search_placeholder": translate(
                "Fayl, yuboruvchi, guruh, IP, domen yoki Telegram ID..."
            ),
            "filters": filters,
            "is_filtered": bool(search or selected_status or selected_scope),
            "result_count": paginator.count,
            "total_count": base.count(),
            "current_profile": profile,
            "can_work": user_can_work(request.user),
            "can_manage": request.user.is_staff,
        },
    )


# --------------------------------------------------------------------------
# APK ish sahifasi
# --------------------------------------------------------------------------


def _cross_reference_counts(submission, findings):
    """Har bir topilma boshqa nechta APK da ham uchragani: {(tur, qiymat): son}."""
    if not findings:
        return {}
    rows = (
        ApkFinding.objects.filter(value__in={item.value for item in findings})
        .exclude(submission=submission)
        .values("kind", "value")
        .annotate(count=Count("submission", distinct=True))
    )
    return {(row["kind"], row["value"]): row["count"] for row in rows}


def _detail_context(request, submission, **overrides):
    profile = get_profile_for_user(request.user)
    can_work = user_can_work(request.user)
    is_owner = submission.assigned_to_id == profile.pk
    can_edit = bool(
        can_work
        and submission.is_editable
        and (request.user.is_staff or is_owner)
    )
    can_claim = bool(
        can_work
        and submission.status == ApkSubmission.STATUS_NEW
        and not submission.assigned_to_id
        and user_is_kursant(request.user)
    )
    can_review = bool(user_can_review(request.user) and submission.status == ApkSubmission.STATUS_SENT)

    findings = list(submission.findings.select_related("added_by"))
    cross = _cross_reference_counts(submission, findings)
    groups = []
    for kind, label in ApkFinding.KIND_CHOICES:
        items = []
        for finding in findings:
            if finding.kind == kind:
                finding.other_count = cross.get((finding.kind, finding.value), 0)
                items.append(finding)
        groups.append({"kind": kind, "label": label, "items": items})

    same_file_count = 0
    if submission.duplicate_of_id:
        same_file_count = (
            ApkFinding.objects.filter(submission__sha256=submission.sha256)
            .exclude(submission=submission)
            .count()
        )

    context = {
        "submission": submission,
        "finding_groups": groups,
        "finding_total": len(findings),
        "events": submission.events.select_related("actor"),
        "same_file_submissions": (
            ApkSubmission.objects.filter(sha256=submission.sha256)
            .exclude(pk=submission.pk)
            .order_by("created_at")
        ),
        "same_file_finding_count": same_file_count,
        "is_owner": is_owner,
        "can_edit": can_edit,
        "can_claim": can_claim,
        "can_review": can_review,
        "can_manage": request.user.is_staff,
        "findings_form": FindingsForm(),
        "note_form": AnalysisNoteForm(initial={"analysis_note": submission.analysis_note}),
        "review_form": ReviewForm(),
    }
    context.update(overrides)
    return context


@login_required
def submission_detail_view(request, pk):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission = get_object_or_404(
        ApkSubmission.objects.select_related(
            "assigned_to", "source", "reviewed_by", "duplicate_of"
        ),
        pk=pk,
    )
    return render(request, "apk/submission_detail.html", _detail_context(request, submission))


def _workflow_action(request, pk, action, success_message, **kwargs):
    """Umumiy qobiq: workflow xatosini xabarga aylantirib, ish sahifasiga qaytaradi."""
    profile = get_profile_for_user(request.user)
    try:
        action(pk, profile, **kwargs)
    except workflow.WorkflowError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, success_message)
    return redirect("apk:submission_detail", pk=pk)


@login_required
@require_POST
def submission_claim_view(request, pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response
    if not user_is_kursant(request.user):
        messages.error(
            request,
            translate("Sizga jadvalda ustun ochilmagan - avval admin sizni kursant sifatida qo'shishi kerak."),
        )
        return redirect("apk:submission_detail", pk=pk)
    return _workflow_action(
        request, pk, workflow.claim, translate("Ish sizga biriktirildi - jadvalda sariq rangda.")
    )


@login_required
@require_POST
def submission_release_view(request, pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response
    response = _workflow_action(
        request,
        pk,
        workflow.release,
        translate("Ish qaytarib berildi - boshqa kursant olishi mumkin."),
        is_staff=request.user.is_staff,
    )
    return response


@login_required
@require_POST
def submission_send_view(request, pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response
    return _workflow_action(
        request,
        pk,
        workflow.send_to_chilonzor,
        translate("Chilonzorga yuborildi."),
        is_staff=request.user.is_staff,
    )


def _editable_submission_or_error(request, pk):
    """Topilma/izoh o'zgartirish uchun ish (yoki xato xabari bilan redirect)."""
    submission = get_object_or_404(ApkSubmission, pk=pk)
    profile = get_profile_for_user(request.user)
    if not submission.is_editable:
        return None, translate("Bu bosqichda ma'lumotni o'zgartirib bo'lmaydi.")
    if not request.user.is_staff and submission.assigned_to_id != profile.pk:
        return None, translate("Bu ish sizga biriktirilmagan.")
    return submission, None


@login_required
@require_POST
def finding_add_view(request, pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission, error = _editable_submission_or_error(request, pk)
    if error:
        messages.error(request, error)
        return redirect("apk:submission_detail", pk=pk)

    form = FindingsForm(request.POST)
    if form.is_valid():
        profile = get_profile_for_user(request.user)
        with transaction.atomic():
            added = sum(
                workflow.add_findings(submission, kind, values, profile)
                for kind, values in form.cleaned_data["parsed_values"].items()
                if values
            )
        if added:
            messages.success(request, translate("{count} ta qiymat qo'shildi.", count=added))
        else:
            messages.info(request, translate("Barcha qiymatlar allaqachon kiritilgan."))
        return redirect("apk:submission_detail", pk=pk)

    submission = get_object_or_404(
        ApkSubmission.objects.select_related("assigned_to", "source", "reviewed_by", "duplicate_of"),
        pk=pk,
    )
    return render(
        request,
        "apk/submission_detail.html",
        _detail_context(request, submission, findings_form=form),
    )


@login_required
@require_POST
def finding_delete_view(request, pk, finding_pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission, error = _editable_submission_or_error(request, pk)
    if error:
        messages.error(request, error)
        return redirect("apk:submission_detail", pk=pk)

    ApkFinding.objects.filter(pk=finding_pk, submission=submission).delete()
    messages.success(request, translate("Qiymat o'chirildi."))
    return redirect("apk:submission_detail", pk=pk)


@login_required
@require_POST
def findings_copy_view(request, pk):
    """Shu fayl (SHA-256) bo'yicha oldingi ishlardagi topilmalarni ko'chiradi."""
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission, error = _editable_submission_or_error(request, pk)
    if error:
        messages.error(request, error)
        return redirect("apk:submission_detail", pk=pk)

    profile = get_profile_for_user(request.user)
    existing = set(submission.findings.values_list("kind", "value"))
    new_rows = []
    for finding in (
        ApkFinding.objects.filter(submission__sha256=submission.sha256)
        .exclude(submission=submission)
        .order_by("created_at", "pk")
    ):
        key = (finding.kind, finding.value)
        if key in existing:
            continue
        existing.add(key)
        new_rows.append(
            ApkFinding(submission=submission, kind=finding.kind, value=finding.value, added_by=profile)
        )
    ApkFinding.objects.bulk_create(new_rows)

    if new_rows:
        messages.success(
            request, translate("{count} ta qiymat oldingi ishdan ko'chirildi.", count=len(new_rows))
        )
    else:
        messages.info(request, translate("Ko'chiriladigan yangi qiymat yo'q."))
    return redirect("apk:submission_detail", pk=pk)


@login_required
@require_POST
def analysis_note_view(request, pk):
    blocked_response = require_worker_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission, error = _editable_submission_or_error(request, pk)
    if error:
        messages.error(request, error)
        return redirect("apk:submission_detail", pk=pk)

    form = AnalysisNoteForm(request.POST)
    if form.is_valid():
        submission.analysis_note = form.cleaned_data["analysis_note"].strip()
        submission.save(update_fields=["analysis_note", "updated_at"])
        messages.success(request, translate("Izoh saqlandi."))
    return redirect("apk:submission_detail", pk=pk)


@login_required
@require_POST
def submission_review_view(request, pk):
    """Chilonzor: qabul qiladi yoki kamchiliklarini yozib qaytaradi."""
    blocked_response = require_reviewer_or_redirect(request)
    if blocked_response:
        return blocked_response

    profile = get_profile_for_user(request.user)
    form = ReviewForm(request.POST)
    note = form.cleaned_data["note"].strip() if form.is_valid() else ""
    decision = request.POST.get("decision")

    try:
        if decision == "accept":
            workflow.accept(pk, profile, note)
            messages.success(request, translate("Qabul qilindi."))
        elif decision == "return":
            workflow.send_back(pk, profile, note)
            messages.warning(request, translate("Kursantga qaytarildi."))
        else:
            messages.error(request, translate("Noto'g'ri amal."))
    except workflow.WorkflowError as exc:
        messages.error(request, str(exc))
    return redirect("apk:submission_detail", pk=pk)


@login_required
def submission_download_view(request, pk):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission = get_object_or_404(ApkSubmission, pk=pk)
    try:
        handle = submission.file.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404(translate("Fayl topilmadi.")) from None

    response = FileResponse(
        handle,
        as_attachment=True,
        filename=submission.file_name,
        content_type="application/vnd.android.package-archive",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def submission_delete_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    submission = get_object_or_404(ApkSubmission, pk=pk)
    submission.file.delete(save=False)
    submission.delete()
    messages.success(request, translate("Ish va APK fayl o'chirildi."))
    return redirect("apk:submission_list")


# --------------------------------------------------------------------------
# Chilonzor navbati
# --------------------------------------------------------------------------


@login_required
def review_queue_view(request):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response

    search = (request.GET.get("q") or "").strip()
    base = with_finding_counts(
        search_filter(ApkSubmission.objects.select_related("assigned_to"), search)
    )
    paginator = Paginator(base.filter(status=ApkSubmission.STATUS_SENT).order_by("sent_at", "pk"), PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))
    now = timezone.now()
    pending = list(page.object_list)
    for item in pending:
        waited = now - (item.sent_at or item.created_at)
        item.wait_label = humanize_wait(waited)
        item.is_overdue = waited >= timedelta(hours=REVIEW_OVERDUE_HOURS)
    query = request.GET.copy()
    query.pop("page", None)
    decided = list(
        base.filter(
            status__in=[ApkSubmission.STATUS_ACCEPTED, ApkSubmission.STATUS_RETURNED],
            reviewed_at__isnull=False,
        )
        .select_related("reviewed_by")
        .order_by("-reviewed_at")[:50]
    )
    return render(
        request,
        "apk/review_queue.html",
        {
            "pending": pending,
            "page": page,
            "page_query": query.urlencode(),
            "overdue_hours": REVIEW_OVERDUE_HOURS,
            "decided": decided,
            "search": search,
            "search_placeholder": translate("Fayl, yuboruvchi, IP, domen yoki Telegram ID..."),
            "is_filtered": bool(search),
            "result_count": paginator.count,
            "total_count": ApkSubmission.objects.filter(status=ApkSubmission.STATUS_SENT).count(),
            "filters": [],
            "can_review": user_can_review(request.user),
        },
    )


# --------------------------------------------------------------------------
# Statistika (admin, MVD, Chilonzor)
# --------------------------------------------------------------------------


@login_required
def dashboard_view(request):
    blocked_response = require_apk_access_or_redirect(request)
    if blocked_response:
        return blocked_response
    user = request.user
    if not (user.is_staff or user_is_mvd(user) or user_is_chilonzor(user)):
        return require_admin_or_redirect(request)

    status_counts = {
        row["status"]: row["count"]
        for row in ApkSubmission.objects.values("status").annotate(count=Count("id"))
    }
    total = sum(status_counts.values())
    status_rows = [
        {
            "label": str(label),
            "color": ApkSubmission.STATUS_COLORS[code],
            "count": status_counts.get(code, 0),
            "share": round(status_counts.get(code, 0) * 100 / total) if total else 0,
        }
        for code, label in ApkSubmission.STATUS_CHOICES
    ]

    distinct_by_kind = {
        row["kind"]: row["count"]
        for row in ApkFinding.objects.values("kind").annotate(
            count=Count("value", distinct=True)
        )
    }
    finding_cards = [
        {"label": str(label), "count": distinct_by_kind.get(kind, 0)}
        for kind, label in ApkFinding.KIND_CHOICES
    ]

    repeated = {kind: [] for kind, _label in ApkFinding.KIND_CHOICES}
    for row in (
        ApkFinding.objects.values("kind", "value")
        .annotate(count=Count("submission", distinct=True))
        .filter(count__gte=2)
        .order_by("-count", "value")
    ):
        if len(repeated[row["kind"]]) < 5:
            repeated[row["kind"]].append(row)
    repeated_groups = [
        {"label": str(label), "items": repeated[kind]}
        for kind, label in ApkFinding.KIND_CHOICES
    ]

    active_statuses = [
        ApkSubmission.STATUS_IN_PROGRESS,
        ApkSubmission.STATUS_RETURNED,
        ApkSubmission.STATUS_SENT,
    ]
    kursants = list(
        Kursant.objects.select_related("user")
        .filter(is_active=True)
        .annotate(
            active_count=Count(
                "user__apk_assignments",
                filter=Q(user__apk_assignments__status__in=active_statuses),
                distinct=True,
            ),
            accepted_count=Count(
                "user__apk_assignments",
                filter=Q(user__apk_assignments__status=ApkSubmission.STATUS_ACCEPTED),
                distinct=True,
            ),
        )
        .order_by("-accepted_count", "user__first_name")
    )

    since = timezone.localdate() - timedelta(days=13)
    per_day = {
        row["day"]: row["count"]
        for row in ApkSubmission.objects.filter(created_at__date__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
    }
    days = [since + timedelta(days=offset) for offset in range(14)]
    peak = max([per_day.get(day, 0) for day in days] + [1])
    daily = [
        {"day": day, "count": per_day.get(day, 0), "height": round(per_day.get(day, 0) * 100 / peak)}
        for day in days
    ]
    # So'nggi 7 kun va undan oldingi 7 kun (KPI ostidagi o'zgarish uchun)
    week_count = sum(per_day.get(day, 0) for day in days[7:])
    prev_week_count = sum(per_day.get(day, 0) for day in days[:7])

    return render(
        request,
        "apk/dashboard.html",
        {
            "total": total,
            "status_rows": status_rows,
            "new_count": status_counts.get(ApkSubmission.STATUS_NEW, 0),
            "sent_count": status_counts.get(ApkSubmission.STATUS_SENT, 0),
            "returned_count": status_counts.get(ApkSubmission.STATUS_RETURNED, 0),
            "accepted_count": status_counts.get(ApkSubmission.STATUS_ACCEPTED, 0),
            "in_progress_count": status_counts.get(ApkSubmission.STATUS_IN_PROGRESS, 0),
            "finding_cards": finding_cards,
            "repeated_groups": repeated_groups,
            "kursants": kursants,
            "daily": daily,
            "week_count": week_count,
            "week_delta": week_count - prev_week_count,
            "has_repeated": any(group["items"] for group in repeated_groups),
            "recent_events": ApkEvent.objects.select_related("actor", "submission").order_by(
                "-created_at", "-id"
            )[:12],
            "role_label": get_role_label(request.user),
        },
    )


# --------------------------------------------------------------------------
# Admin: kursantlar (jadval ustunlari)
# --------------------------------------------------------------------------


@login_required
def kursant_list_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    search = (request.GET.get("q") or "").strip()
    kursants = Kursant.objects.select_related("user", "user__account")
    if search:
        kursants = kursants.filter(
            Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__account__username__icontains=search)
            | Q(team__icontains=search)
        )
    kursants = list(
        kursants.annotate(
            work_count=Count("user__apk_assignments", distinct=True),
            accepted_count=Count(
                "user__apk_assignments",
                filter=Q(user__apk_assignments__status=ApkSubmission.STATUS_ACCEPTED),
                distinct=True,
            ),
        ).order_by("team", "sort_order", "user__first_name")
    )
    return render(
        request,
        "apk/kursant_list.html",
        {
            "kursants": kursants,
            "search": search,
            "search_placeholder": translate("Kursant ismi, login yoki guruh..."),
            "filters": [],
            "is_filtered": bool(search),
            "result_count": len(kursants),
            "total_count": Kursant.objects.count(),
        },
    )


@login_required
def kursant_create_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    form = KursantForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, translate("Kursant jadvalga ustun sifatida qo'shildi."))
        return redirect("apk:kursant_list")
    return render(
        request,
        "apk/form_page.html",
        {
            "form": form,
            "page_title": translate("Jadvalga kursant qo'shish"),
            "submit_text": translate("Saqlash"),
            "back_url": reverse("apk:kursant_list"),
        },
    )


@login_required
def kursant_update_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    kursant = get_object_or_404(Kursant, pk=pk)
    form = KursantForm(request.POST or None, instance=kursant)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, translate("Kursant ma'lumoti yangilandi."))
        return redirect("apk:kursant_list")
    return render(
        request,
        "apk/form_page.html",
        {
            "form": form,
            "page_title": translate("Kursantni tahrirlash"),
            "submit_text": translate("Yangilash"),
            "back_url": reverse("apk:kursant_list"),
        },
    )


@login_required
@require_POST
def kursant_delete_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    get_object_or_404(Kursant, pk=pk).delete()
    messages.success(request, translate("Kursant jadvaldan olib tashlandi."))
    return redirect("apk:kursant_list")


# --------------------------------------------------------------------------
# Admin: API kalitlari
# --------------------------------------------------------------------------


@login_required
def api_client_list_view(request):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    form = ApiClientForm(request.POST or None)
    new_token = None
    new_client = None
    if request.method == "POST" and form.is_valid():
        new_client, new_token = form.save()
        form = ApiClientForm()

    return render(
        request,
        "apk/api_clients.html",
        {
            "clients": ApiClient.objects.select_related("user", "user__account"),
            "form": form,
            "new_token": new_token,
            "new_client": new_client,
            "api_url": request.build_absolute_uri(reverse("api_receive_apk")),
        },
    )


@login_required
@require_POST
def api_client_toggle_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    client = get_object_or_404(ApiClient, pk=pk)
    client.is_active = not client.is_active
    client.save(update_fields=["is_active"])
    messages.success(
        request,
        translate("Kalit yoqildi.") if client.is_active else translate("Kalit o'chirildi (faolsiz)."),
    )
    return redirect("apk:api_clients")


@login_required
@require_POST
def api_client_delete_view(request, pk):
    blocked_response = require_admin_or_redirect(request)
    if blocked_response:
        return blocked_response

    get_object_or_404(ApiClient, pk=pk).delete()
    messages.success(request, translate("API kaliti o'chirildi."))
    return redirect("apk:api_clients")
