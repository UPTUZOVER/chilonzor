"""APK ishining holat o'tishlari.

Oqim: Yangi -> (kursant oladi) -> Kursant tahlil qilmoqda -> (Chilonzorga yuboradi)
-> Chilonzor ko'rib chiqmoqda -> Qabul qilindi  YOKI  Qaytarildi (sabab bilan) ->
kursant tuzatib qayta yuboradi.

Har bir o'tish bitta tranzaksiyada, qator qulflanib bajariladi - ikki kursant bir
vaqtda bitta ishni ololmaydi."""

from django.db import transaction
from django.utils import timezone

from app.ui_i18n import translate

from .models import ApkEvent, ApkFinding, ApkSubmission
from .notifications import notify_group, notify_user
from .permissions import GROUP_CHILONZOR


class WorkflowError(Exception):
    """Foydalanuvchiga ko'rsatiladigan o'tish xatosi."""


def _lock(submission_id):
    return ApkSubmission.objects.select_for_update().get(pk=submission_id)


def _log(submission, actor, action, note=""):
    ApkEvent.objects.create(submission=submission, actor=actor, action=action, note=note)


def record_received(submission):
    _log(submission, submission.source, ApkEvent.ACTION_RECEIVED)


def _ensure_owner(submission, actor_profile, is_staff):
    if is_staff:
        return
    if submission.assigned_to_id != actor_profile.pk:
        raise WorkflowError(translate("Bu ish sizga biriktirilmagan."))


def claim(submission_id, kursant_profile):
    with transaction.atomic():
        submission = _lock(submission_id)
        if submission.status != ApkSubmission.STATUS_NEW or submission.assigned_to_id:
            if submission.assigned_to_id == kursant_profile.pk:
                raise WorkflowError(translate("Bu ish allaqachon sizga biriktirilgan."))
            raise WorkflowError(
                translate(
                    "Bu ishni boshqa kursant olgan: {officer}.",
                    officer=str(submission.assigned_to or "-"),
                )
            )
        submission.assigned_to = kursant_profile
        submission.claimed_at = timezone.now()
        submission.status = ApkSubmission.STATUS_IN_PROGRESS
        submission.save(update_fields=["assigned_to", "claimed_at", "status", "updated_at"])
        _log(submission, kursant_profile, ApkEvent.ACTION_CLAIMED)
    return submission


def release(submission_id, actor_profile, is_staff=False):
    """Kursant ishni bo'shatadi - ish yana "Yangi" bo'ladi, topilmalar saqlanadi."""
    with transaction.atomic():
        submission = _lock(submission_id)
        _ensure_owner(submission, actor_profile, is_staff)
        if submission.status not in ApkSubmission.EDITABLE_STATUSES:
            raise WorkflowError(translate("Bu bosqichda ishni qaytarib bo'lmaydi."))
        submission.assigned_to = None
        submission.claimed_at = None
        submission.status = ApkSubmission.STATUS_NEW
        submission.save(update_fields=["assigned_to", "claimed_at", "status", "updated_at"])
        _log(submission, actor_profile, ApkEvent.ACTION_RELEASED)
    return submission


def send_to_chilonzor(submission_id, actor_profile, is_staff=False):
    with transaction.atomic():
        submission = _lock(submission_id)
        _ensure_owner(submission, actor_profile, is_staff)
        if submission.status not in ApkSubmission.EDITABLE_STATUSES:
            raise WorkflowError(translate("Bu ish hozir yuborib bo'lmaydigan holatda."))
        if not ApkFinding.objects.filter(submission=submission).exists():
            raise WorkflowError(
                translate("Yuborishdan oldin kamida bitta IP, domen yoki Telegram ID kiriting.")
            )
        submission.status = ApkSubmission.STATUS_SENT
        submission.sent_at = timezone.now()
        submission.save(update_fields=["status", "sent_at", "updated_at"])
        _log(submission, actor_profile, ApkEvent.ACTION_SENT)

    notify_group(
        actor_profile,
        GROUP_CHILONZOR,
        translate(
            "#{id} {file} bo'yicha tahlil ko'rib chiqishingizni kutmoqda.",
            id=submission.pk,
            file=submission.file_name,
        ),
    )
    return submission


def accept(submission_id, reviewer_profile, note=""):
    with transaction.atomic():
        submission = _lock(submission_id)
        if submission.status != ApkSubmission.STATUS_SENT:
            raise WorkflowError(translate("Bu ish ko'rib chiqish holatida emas."))
        submission.status = ApkSubmission.STATUS_ACCEPTED
        submission.reviewed_by = reviewer_profile
        submission.reviewed_at = timezone.now()
        submission.review_note = note
        submission.save(
            update_fields=["status", "reviewed_by", "reviewed_at", "review_note", "updated_at"]
        )
        _log(submission, reviewer_profile, ApkEvent.ACTION_ACCEPTED, note)

    notify_user(
        reviewer_profile,
        submission.assigned_to,
        translate(
            "#{id} {file} bo'yicha tahlilingiz qabul qilindi.",
            id=submission.pk,
            file=submission.file_name,
        ),
    )
    return submission


def send_back(submission_id, reviewer_profile, note):
    note = (note or "").strip()
    if not note:
        raise WorkflowError(translate("Qaytarish sababini (kamchiliklarni) yozish shart."))
    with transaction.atomic():
        submission = _lock(submission_id)
        if submission.status != ApkSubmission.STATUS_SENT:
            raise WorkflowError(translate("Bu ish ko'rib chiqish holatida emas."))
        submission.status = ApkSubmission.STATUS_RETURNED
        submission.reviewed_by = reviewer_profile
        submission.reviewed_at = timezone.now()
        submission.review_note = note
        submission.return_count += 1
        submission.save(
            update_fields=[
                "status", "reviewed_by", "reviewed_at", "review_note", "return_count",
                "updated_at",
            ]
        )
        _log(submission, reviewer_profile, ApkEvent.ACTION_RETURNED, note)

    notify_user(
        reviewer_profile,
        submission.assigned_to,
        translate(
            "#{id} {file} qaytarildi. Kamchiliklar: {note}",
            id=submission.pk,
            file=submission.file_name,
            note=note,
        ),
    )
    return submission


def add_findings(submission, kind, values, actor_profile):
    """Yangi qiymatlarni qo'shadi, allaqachon borlarini o'tkazib yuboradi. Qo'shilganlar sonini qaytaradi."""
    existing = set(
        ApkFinding.objects.filter(submission=submission, kind=kind).values_list("value", flat=True)
    )
    new_rows = [
        ApkFinding(submission=submission, kind=kind, value=value, added_by=actor_profile)
        for value in values
        if value not in existing
    ]
    ApkFinding.objects.bulk_create(new_rows)
    return len(new_rows)
