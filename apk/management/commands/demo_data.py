"""APK tahlil bo'limi uchun sinov (demo) hisoblari va ma'lumotlarini yaratadi.

Ishlatish:
    python manage.py demo_data            # yaratadi / yangilaydi
    python manage.py demo_data --clear    # faqat demo ma'lumot va hisoblarni o'chiradi

Faqat quyidagi loginlar va "demo_" bilan boshlanuvchi username'li APK ishlar bilan
ishlaydi - haqiqiy ma'lumotlaringizga TEGMAYDI.
"""

import hashlib
import io
import zipfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apk import workflow
from apk.models import ApkFinding, ApkSubmission, Kursant
from apk.permissions import GROUP_CHILONZOR, GROUP_MVD
from app.models import Users

User = get_user_model()

DEMO_PREFIX = "demo_"
DEFAULT_PASSWORD = "Apk2026!demo"

# login: (ism, familiya, guruh, is_staff, kursantmi)
ACCOUNTS = {
    "admin1": ("Admin", "Boshqaruvchi", None, True, False),
    "mvd1": ("Aziz", "Karimov", GROUP_MVD, False, False),
    "kursant1": ("Nodira", "Rahimova", None, False, True),
    "kursant2": ("Bobur", "Aliyev", None, False, True),
    "chilonzor1": ("Sardor", "Yusupov", GROUP_CHILONZOR, False, False),
}

# (fayl, profil nomi, username, user_id, guruh nomi, guruh turi, chat_id)
SAMPLES = [
    ("SafarAI_Kameralar_BEPUL.apk", "Ўткир", "demo_salom6233", 5907562354,
     "My music", "supergroup", -1003542328393),
    ("Bank_Bonus_2026.apk", "Dilshod", "demo_dilshod_k", 1122334455,
     "Tezkor kredit", "supergroup", -1001900000001),
    ("Gov_Subsidiya.apk", "Madina", "demo_madina77", 2233445566,
     "Subsidiya yangiliklari", "channel", -1001900000002),
    ("Taksi_Aksiya.apk", "Jasur", "demo_jasur_t", 3344556677,
     "Toshkent taksi", "supergroup", -1001900000003),
    ("Foto_Tozalash.apk", "Zarina", "demo_zarina_f", 4455667788,
     "Foto redaktor", "supergroup", -1001900000004),
]


def fake_apk_bytes(label):
    """Haqiqiy ZIP tuzilmali kichik fayl - API tekshiruvidan o'tadigan namunaviy APK."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("AndroidManifest.xml", f"demo {label}")
    return buffer.getvalue()


class Command(BaseCommand):
    help = "APK tahlil bo'limi uchun demo hisoblar va APK ishlarni yaratadi."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Demo ma'lumotni o'chirish")
        parser.add_argument("--parol", default=DEFAULT_PASSWORD, help="Demo hisoblar paroli")

    def handle(self, *args, **options):
        if options["clear"]:
            return self.clear()

        with transaction.atomic():
            profiles = self.make_accounts(options["parol"])
            self.make_submissions(profiles)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo ma'lumot tayyor."))
        self.stdout.write(f"  Parol (hammasi uchun): {options['parol']}")
        for username, (first, last, group, is_staff, is_kursant) in ACCOUNTS.items():
            role = "Admin" if is_staff else group or ("Kursant" if is_kursant else "-")
            self.stdout.write(f"  {username:<11} {role:<10} {first} {last}")
        self.stdout.write("  Kirish: /login/    O'chirish: python manage.py demo_data --clear")

    def make_accounts(self, password):
        profiles = {}
        for username, (first, last, group_name, is_staff, is_kursant) in ACCOUNTS.items():
            account, _created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "last_name": last}
            )
            account.first_name, account.last_name = first, last
            account.is_staff = is_staff
            account.is_superuser = is_staff
            account.is_active = True
            account.set_password(password)
            account.save()

            if group_name:
                group, _ = Group.objects.get_or_create(name=group_name)
                account.groups.add(group)

            profile, _ = Users.objects.get_or_create(
                account=account, defaults={"first_name": first, "last_name": last}
            )
            profile.first_name, profile.last_name = first, last
            profile.save()

            if is_kursant:
                kursant, _ = Kursant.objects.get_or_create(user=profile)
                kursant.is_active = True
                kursant.save()
            profiles[username] = profile
        return profiles

    def make_submissions(self, profiles):
        for old in ApkSubmission.objects.filter(sender_username__startswith=DEMO_PREFIX):
            old.file.delete(save=False)
            old.delete()
        mvd = profiles["mvd1"]
        kursant1, kursant2 = profiles["kursant1"], profiles["kursant2"]
        chilonzor = profiles["chilonzor1"]

        submissions = []
        for file_name, name, username, user_id, title, chat_type, chat_id in SAMPLES:
            data = fake_apk_bytes(file_name)
            submission = ApkSubmission(
                sender_name=name,
                sender_username=username,
                sender_user_id=user_id,
                chat_title=title,
                chat_type=chat_type,
                chat_id=chat_id,
                file_name=file_name,
                file_size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                source=mvd,
            )
            submission.file.save(file_name, ContentFile(data), save=False)
            submission.save()
            workflow.record_received(submission)
            submissions.append(submission)

        _new, in_progress, sent, returned, accepted = submissions  # 1-chisi "Yangi" qoladi

        # 2) Kursant oldi, topilma kiritmoqda
        workflow.claim(in_progress.pk, kursant1)
        workflow.add_findings(in_progress, ApkFinding.KIND_IP, ["203.0.113.5:8080"], kursant1)

        # 3) Chilonzorga yuborilgan
        workflow.claim(sent.pk, kursant2)
        workflow.add_findings(sent, ApkFinding.KIND_DOMAIN, ["cdn-bonus.example.com"], kursant2)
        workflow.add_findings(sent, ApkFinding.KIND_TELEGRAM, ["@bonus_admin_uz"], kursant2)
        workflow.send_to_chilonzor(sent.pk, kursant2)

        # 4) Chilonzor kamchilik bilan qaytargan
        workflow.claim(returned.pk, kursant1)
        workflow.add_findings(returned, ApkFinding.KIND_IP, ["198.51.100.20"], kursant1)
        workflow.send_to_chilonzor(returned.pk, kursant1)
        workflow.send_back(returned.pk, chilonzor, "Domen va Telegram ID topilmagan, qayta tekshiring.")

        # 5) Qabul qilingan
        workflow.claim(accepted.pk, kursant2)
        workflow.add_findings(accepted, ApkFinding.KIND_IP, ["192.0.2.44"], kursant2)
        workflow.add_findings(accepted, ApkFinding.KIND_DOMAIN, ["panel.example.org"], kursant2)
        workflow.add_findings(accepted, ApkFinding.KIND_TELEGRAM, ["5907562354"], kursant2)
        workflow.send_to_chilonzor(accepted.pk, kursant2)
        workflow.accept(accepted.pk, chilonzor, "Hammasi to'g'ri.")

    def clear(self):
        deleted_submissions = 0
        for submission in ApkSubmission.objects.filter(sender_username__startswith=DEMO_PREFIX):
            submission.file.delete(save=False)
            submission.delete()
            deleted_submissions += 1
        accounts = User.objects.filter(username__in=ACCOUNTS)
        count = accounts.count()
        Users.objects.filter(account__in=accounts).delete()
        accounts.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"O'chirildi: {deleted_submissions} demo APK ish va {count} demo hisob."
            )
        )
