"""Botdan APK qabul qiladigan API.

    POST /api/apk/
    Authorization: Bearer <API kaliti>
    Content-Type: multipart/form-data

Maydonlar:
    file          - APK fayl (majburiy)
    profile_name  - yuborgan profil nomi
    username      - yuborgan username (@ bilan yoki @siz)
    user_id       - yuborgan Telegram user ID
    title         - APK yuborilgan guruh nomi
    type          - guruh turi (masalan: supergroup)
    chat_id       - guruh ID

Muvaffaqiyatli javob (201):
    {"ok": true, "id": 12, "status": "new", "sha256": "...", "duplicate_of": null}
`duplicate_of` - shu fayl (SHA-256 bo'yicha) oldin kelgan bo'lsa, birinchi yozuv ID'si.
Xatolarda: {"ok": false, "error": "..."} va 400 / 401 / 413 / 405 status.
"""

import hashlib

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import ApiClient, ApkSubmission
from .workflow import record_received

DEFAULT_MAX_UPLOAD_MB = 200
ZIP_MAGIC = b"PK\x03\x04"


def _error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


def _token_from_request(request):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if header[:7].lower() == "bearer ":
        return header[7:].strip()
    return request.META.get("HTTP_X_API_TOKEN", "").strip()


def _optional_int(request, field):
    raw = (request.POST.get(field) or "").strip()
    if not raw:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{field} butun son bo'lishi kerak."


@csrf_exempt
def receive_apk_view(request):
    if request.method != "POST":
        return _error("Faqat POST so'rovi qabul qilinadi.", status=405)

    client = ApiClient.authenticate(_token_from_request(request))
    if client is None:
        return _error("API kaliti noto'g'ri yoki faol emas.", status=401)

    uploaded = request.FILES.get("file")
    if uploaded is None:
        return _error("`file` maydoni (APK fayl) yuborilmagan.")

    file_name = (uploaded.name or "").strip()
    if not file_name.lower().endswith(".apk"):
        return _error("Faqat .apk fayl qabul qilinadi.")

    max_bytes = int(getattr(settings, "APK_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB)) * 1024 * 1024
    if uploaded.size > max_bytes:
        return _error("Fayl juda katta.", status=413)

    header = uploaded.read(4)
    uploaded.seek(0)
    if header != ZIP_MAGIC:
        return _error("Fayl haqiqiy APK (ZIP) emas.")

    digest = hashlib.sha256()
    for chunk in uploaded.chunks():
        digest.update(chunk)
    uploaded.seek(0)

    sender_user_id, error = _optional_int(request, "user_id")
    if error:
        return _error(error)
    chat_id, error = _optional_int(request, "chat_id")
    if error:
        return _error(error)

    sha256 = digest.hexdigest()
    with transaction.atomic():
        first_copy = (
            ApkSubmission.objects.filter(sha256=sha256).order_by("created_at", "pk").first()
        )
        submission = ApkSubmission(
            sender_name=(request.POST.get("profile_name") or "").strip()[:255],
            sender_username=(request.POST.get("username") or "").strip()[:64],
            sender_user_id=sender_user_id,
            chat_title=(request.POST.get("title") or "").strip()[:255],
            chat_type=(request.POST.get("type") or "").strip()[:32],
            chat_id=chat_id,
            file_name=file_name[:255],
            file_size=uploaded.size,
            sha256=sha256,
            duplicate_of=first_copy,
            source=client.user,
        )
        submission.file.save(file_name, uploaded, save=False)
        submission.save()
        record_received(submission)

    ApiClient.objects.filter(pk=client.pk).update(last_used_at=timezone.now())

    return JsonResponse(
        {
            "ok": True,
            "id": submission.pk,
            "status": submission.status,
            "sha256": sha256,
            "duplicate_of": first_copy.pk if first_copy else None,
        },
        status=201,
    )
