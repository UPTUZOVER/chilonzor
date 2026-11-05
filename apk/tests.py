import hashlib
import io
import shutil
import tempfile
import zipfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from app.models import AdminMessage, Users

from . import workflow
from .models import ApiClient, ApkEvent, ApkFinding, ApkSubmission, Kursant
from .parsing import normalize_domain, normalize_finding, normalize_ip, normalize_telegram, parse_lines
from .permissions import GROUP_CHILONZOR, GROUP_MVD

User = get_user_model()


def apk_bytes(label="demo"):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("AndroidManifest.xml", label)
    return buffer.getvalue()


class TempMediaMixin:
    """Fayllar test tugagach o'chadigan vaqtinchalik papkaga yoziladi."""

    def setUp(self):
        super().setUp()
        self._media_dir = tempfile.mkdtemp()
        self._override = override_settings(MEDIA_ROOT=self._media_dir)
        self._override.enable()

    def tearDown(self):
        self._override.disable()
        shutil.rmtree(self._media_dir, ignore_errors=True)
        super().tearDown()


class RolesMixin(TempMediaMixin):
    def setUp(self):
        super().setUp()
        self.admin_account = User.objects.create_user("admin_t", password="pw12345!x", is_staff=True)
        self.mvd_account = User.objects.create_user("mvd_t", password="pw12345!x")
        self.mvd_account.groups.add(Group.objects.get(name=GROUP_MVD))
        self.chilonzor_account = User.objects.create_user("chil_t", password="pw12345!x")
        self.chilonzor_account.groups.add(Group.objects.get(name=GROUP_CHILONZOR))
        self.kursant_account = User.objects.create_user("kur_t", password="pw12345!x")
        self.kursant2_account = User.objects.create_user("kur2_t", password="pw12345!x")
        self.plain_account = User.objects.create_user("plain_t", password="pw12345!x")

        self.mvd = Users.objects.get(account=self.mvd_account)
        self.chilonzor = Users.objects.get(account=self.chilonzor_account)
        self.kursant = Users.objects.get(account=self.kursant_account)
        self.kursant2 = Users.objects.get(account=self.kursant2_account)
        Kursant.objects.create(user=self.kursant)
        Kursant.objects.create(user=self.kursant2)

    def make_submission(self, name="sample.apk", sender_username="tester", content=None):
        data = content or apk_bytes(name)
        submission = ApkSubmission(
            sender_name="Tester",
            sender_username=sender_username,
            sender_user_id=111,
            chat_title="Guruh",
            chat_type="supergroup",
            chat_id=-100222,
            file_name=name,
            file_size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            source=self.mvd,
        )
        submission.file.save(name, ContentFile(data), save=False)
        submission.save()
        workflow.record_received(submission)
        return submission


class ParsingTests(TestCase):
    def test_ip_variants(self):
        self.assertEqual(normalize_ip("192.168.1.10"), "192.168.1.10")
        self.assertEqual(normalize_ip(" 203.0.113.5:8080 "), "203.0.113.5:8080")
        self.assertEqual(normalize_ip("http://203.0.113.5:80/x"), "203.0.113.5")
        self.assertEqual(normalize_ip("2001:DB8::1"), "2001:db8::1")
        self.assertEqual(normalize_ip("[2001:db8::1]:443"), "[2001:db8::1]:443")
        for bad in ("999.1.1.1", "1.2.3", "abc", "1.2.3.4:70000", ""):
            with self.assertRaises(ValueError, msg=bad):
                normalize_ip(bad)

    def test_domain_variants(self):
        self.assertEqual(normalize_domain("Example.COM"), "example.com")
        self.assertEqual(normalize_domain("https://Sub.Example.com:8443/path?x=1"), "sub.example.com")
        self.assertEqual(normalize_domain("example.com."), "example.com")
        for bad in ("localhost", "1.2.3.4", "-bad.com", "bad_.com", "a..b.com", "x.c"):
            with self.assertRaises(ValueError, msg=bad):
                normalize_domain(bad)

    def test_telegram_variants(self):
        self.assertEqual(normalize_telegram("5907562354"), "5907562354")
        self.assertEqual(normalize_telegram("-1003542328393"), "-1003542328393")
        self.assertEqual(normalize_telegram("@Salom6233"), "@salom6233")
        self.assertEqual(normalize_telegram("salom6233"), "@salom6233")
        self.assertEqual(normalize_telegram("https://t.me/Salom6233"), "@salom6233")
        for bad in ("12", "@a", "@1abcde", "not valid!", ""):
            with self.assertRaises(ValueError, msg=bad):
                normalize_telegram(bad)

    def test_parse_lines_dedupes_and_reports_errors(self):
        values, errors = parse_lines("domain", "a.com\n\nA.com\nbad\nb.org,\n")
        self.assertEqual(values, ["a.com", "b.org"])
        self.assertEqual([line for line, _ in errors], ["bad"])
        with self.assertRaises(ValueError):
            normalize_finding("nope", "x")


class ApiTests(TempMediaMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.mvd_account = User.objects.create_user("api_mvd", password="pw12345!x")
        self.mvd_account.groups.add(Group.objects.get(name=GROUP_MVD))
        self.mvd = Users.objects.get(account=self.mvd_account)
        self.client_obj, self.token = ApiClient.create_with_token("Bot", self.mvd)
        self.url = reverse("api_receive_apk")

    def post(self, token=None, **overrides):
        data = {
            "profile_name": "Ўткир",
            "username": "@salom6233",
            "user_id": "5907562354",
            "title": "My music",
            "type": "supergroup",
            "chat_id": "-1003542328393",
            "file": SimpleUploadedFile("SafarAI_Kameralar_BEPUL.apk", apk_bytes("a")),
        }
        data.update(overrides)
        data = {key: value for key, value in data.items() if value is not None}
        headers = {}
        if token is not False:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {token or self.token}"
        return self.client.post(self.url, data, **headers)

    def test_token_is_stored_hashed(self):
        self.assertNotEqual(self.client_obj.token_hash, self.token)
        self.assertEqual(self.client_obj.token_hash, ApiClient.hash_token(self.token))
        self.assertTrue(self.token.startswith(self.client_obj.token_prefix))

    def test_successful_upload_saves_everything(self):
        response = self.post()
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertIsNone(body["duplicate_of"])

        submission = ApkSubmission.objects.get(pk=body["id"])
        self.assertEqual(submission.sender_name, "Ўткир")
        self.assertEqual(submission.sender_username, "@salom6233")
        self.assertEqual(submission.sender_user_id, 5907562354)
        self.assertEqual(submission.chat_title, "My music")
        self.assertEqual(submission.chat_type, "supergroup")
        self.assertEqual(submission.chat_id, -1003542328393)
        self.assertEqual(submission.file_name, "SafarAI_Kameralar_BEPUL.apk")
        self.assertEqual(submission.status, ApkSubmission.STATUS_NEW)
        self.assertEqual(submission.source, self.mvd)
        self.assertEqual(submission.sha256, body["sha256"])
        self.assertEqual(submission.file.read(), apk_bytes("a"))
        self.assertEqual(submission.events.get().action, ApkEvent.ACTION_RECEIVED)
        self.client_obj.refresh_from_db()
        self.assertIsNotNone(self.client_obj.last_used_at)

    def test_duplicate_file_points_to_first_copy(self):
        first = self.post().json()
        second = self.post().json()
        self.assertEqual(second["duplicate_of"], first["id"])
        self.assertEqual(ApkSubmission.objects.count(), 2)

    def test_auth_failures(self):
        self.assertEqual(self.post(token=False).status_code, 401)
        self.assertEqual(self.post(token="wrong").status_code, 401)
        self.client_obj.is_active = False
        self.client_obj.save()
        self.assertEqual(self.post().status_code, 401)
        self.assertEqual(ApkSubmission.objects.count(), 0)

    def test_x_api_token_header_is_accepted(self):
        data = {"file": SimpleUploadedFile("a.apk", apk_bytes())}
        response = self.client.post(self.url, data, HTTP_X_API_TOKEN=self.token)
        self.assertEqual(response.status_code, 201)

    def test_only_post_is_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_validation_errors(self):
        self.assertEqual(self.post(file=None).status_code, 400)
        not_apk = SimpleUploadedFile("tool.exe", apk_bytes())
        self.assertEqual(self.post(file=not_apk).status_code, 400)
        fake = SimpleUploadedFile("fake.apk", b"this is not a zip file")
        self.assertEqual(self.post(file=fake).status_code, 400)
        self.assertEqual(self.post(user_id="abc").status_code, 400)
        self.assertEqual(self.post(chat_id="x1").status_code, 400)
        self.assertEqual(ApkSubmission.objects.count(), 0)

    @override_settings(APK_MAX_UPLOAD_MB=0)
    def test_too_large_file_is_rejected(self):
        self.assertEqual(self.post().status_code, 413)

    def test_optional_fields_may_be_missing(self):
        response = self.post(
            profile_name=None, username=None, user_id=None, title=None, type=None, chat_id=None
        )
        self.assertEqual(response.status_code, 201)
        submission = ApkSubmission.objects.get()
        self.assertIsNone(submission.sender_user_id)
        self.assertIsNone(submission.chat_id)


class WorkflowViewTests(RolesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.submission = self.make_submission()
        self.pk = self.submission.pk

    def login(self, account):
        self.client.force_login(account)

    def refresh(self):
        self.submission.refresh_from_db()
        return self.submission

    def claim(self):
        self.login(self.kursant_account)
        return self.client.post(reverse("apk:submission_claim", args=[self.pk]))

    def add(self, kind, values):
        return self.client.post(
            reverse("apk:finding_add", args=[self.pk]), {f"{kind}_values": values}
        )

    def test_all_finding_types_can_be_added_together_without_duplicates(self):
        self.claim()
        url = reverse("apk:finding_add", args=[self.pk])
        data = {
            "ip_values": "203.0.113.5\n203.0.113.5\n192.168.1.10:8080",
            "domain_values": "Example.COM\nhttps://example.com/path",
            "telegram_values": "5907562354\n@Salom6233",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("apk:submission_detail", args=[self.pk]))
        expected = {
            ("ip", "203.0.113.5"), ("ip", "192.168.1.10:8080"),
            ("domain", "example.com"),
            ("telegram", "5907562354"), ("telegram", "@salom6233"),
        }
        self.assertEqual(set(self.submission.findings.values_list("kind", "value")), expected)
        self.client.post(url, data)
        self.assertEqual(self.submission.findings.count(), len(expected))
        self.assertFalse(self.submission.findings.exclude(added_by=self.kursant).exists())

    def test_invalid_finding_type_preserves_all_inputs_and_saves_nothing(self):
        self.claim()
        response = self.client.post(reverse("apk:finding_add", args=[self.pk]), {
            "ip_values": "203.0.113.5", "domain_values": "invalid-domain",
            "telegram_values": "5907562354",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("domain_values", response.context["findings_form"].errors)
        for value in ("203.0.113.5", "invalid-domain", "5907562354"):
            self.assertContains(response, value)
        self.assertFalse(self.submission.findings.exists())

    def test_empty_findings_are_rejected(self):
        self.claim()
        response = self.client.post(reverse("apk:finding_add", args=[self.pk]), {})
        self.assertContains(response, "Kamida bitta qiymat kiriting.")
        self.assertFalse(self.submission.findings.exists())

    def test_detail_has_separate_inputs_for_all_finding_types(self):
        self.claim()
        response = self.client.get(reverse("apk:submission_detail", args=[self.pk]))
        for name in ("ip_values", "domain_values", "telegram_values"):
            self.assertContains(response, f'name="{name}"')
        self.assertNotContains(response, 'name="kind"')

    def test_first_kursant_to_claim_wins(self):
        self.claim()
        self.assertEqual(self.refresh().assigned_to, self.kursant)
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_IN_PROGRESS)

        self.login(self.kursant2_account)
        self.client.post(reverse("apk:submission_claim", args=[self.pk]))
        self.assertEqual(self.refresh().assigned_to, self.kursant)

    def test_mvd_chilonzor_and_plain_users_cannot_claim(self):
        for account in (self.mvd_account, self.chilonzor_account, self.plain_account):
            self.login(account)
            self.client.post(reverse("apk:submission_claim", args=[self.pk]))
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_NEW)
        self.assertIsNone(self.refresh().assigned_to)

    def test_findings_are_normalised_and_validated(self):
        self.claim()
        self.add("domain", "Example.COM\nhttps://example.com/x\nother.org")
        self.assertEqual(
            sorted(self.submission.findings.values_list("value", flat=True)),
            ["example.com", "other.org"],
        )
        response = self.add("ip", "1.2.3.4\nnot-an-ip")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not-an-ip")
        self.assertFalse(self.submission.findings.filter(kind="ip").exists())
        self.add("telegram", "5907562354\n@Salom6233")
        self.assertEqual(self.submission.findings.filter(kind="telegram").count(), 2)

    def test_only_owner_can_edit_findings(self):
        self.claim()
        self.login(self.kursant2_account)
        self.add("ip", "1.2.3.4")
        self.assertFalse(self.submission.findings.exists())

    def test_cannot_send_without_findings(self):
        self.claim()
        self.client.post(reverse("apk:submission_send", args=[self.pk]))
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_IN_PROGRESS)

    def send(self):
        self.client.post(reverse("apk:submission_send", args=[self.pk]))

    def review(self, decision, note=""):
        return self.client.post(
            reverse("apk:submission_review", args=[self.pk]), {"decision": decision, "note": note}
        )

    def test_full_cycle_with_return_and_accept(self):
        self.claim()
        self.add("ip", "203.0.113.5")
        self.send()
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_SENT)
        self.assertTrue(
            AdminMessage.objects.filter(recipient=self.chilonzor, body__contains="sample.apk").exists()
        )

        # Yuborilgandan keyin kursant o'zgartira olmaydi
        self.add("ip", "1.1.1.1")
        self.assertEqual(self.submission.findings.count(), 1)

        # Kursant va MVD ko'rib chiqa olmaydi
        for account in (self.kursant_account, self.mvd_account):
            self.login(account)
            self.review("accept")
            self.assertEqual(self.refresh().status, ApkSubmission.STATUS_SENT)

        # Chilonzor sababsiz qaytara olmaydi
        self.login(self.chilonzor_account)
        self.review("return", note="  ")
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_SENT)

        self.review("return", note="Domen topilmagan")
        submission = self.refresh()
        self.assertEqual(submission.status, ApkSubmission.STATUS_RETURNED)
        self.assertEqual(submission.review_note, "Domen topilmagan")
        self.assertEqual(submission.return_count, 1)
        self.assertEqual(submission.assigned_to, self.kursant)
        self.assertTrue(
            AdminMessage.objects.filter(recipient=self.kursant, body__contains="Domen topilmagan").exists()
        )

        # Kursant tuzatib qayta yuboradi
        self.login(self.kursant_account)
        self.add("domain", "panel.example.com")
        self.send()
        self.assertEqual(self.refresh().status, ApkSubmission.STATUS_SENT)

        self.login(self.chilonzor_account)
        self.review("accept", note="To'g'ri")
        submission = self.refresh()
        self.assertEqual(submission.status, ApkSubmission.STATUS_ACCEPTED)
        self.assertEqual(submission.reviewed_by, self.chilonzor)
        actions = list(submission.events.values_list("action", flat=True))
        self.assertEqual(
            actions,
            ["received", "claimed", "sent", "returned", "sent", "accepted"],
        )

        # Qabul qilingan ishni o'zgartirib bo'lmaydi
        self.login(self.kursant_account)
        self.add("ip", "9.9.9.9")
        self.assertFalse(self.submission.findings.filter(value="9.9.9.9").exists())

    def test_release_returns_work_to_the_pool_and_keeps_findings(self):
        self.claim()
        self.add("ip", "203.0.113.5")
        self.client.post(reverse("apk:submission_release", args=[self.pk]))
        submission = self.refresh()
        self.assertEqual(submission.status, ApkSubmission.STATUS_NEW)
        self.assertIsNone(submission.assigned_to)
        self.assertEqual(submission.findings.count(), 1)

        self.login(self.kursant2_account)
        self.client.post(reverse("apk:submission_claim", args=[self.pk]))
        self.assertEqual(self.refresh().assigned_to, self.kursant2)

    def test_copy_findings_from_same_file(self):
        original = self.make_submission(name="a.apk", content=apk_bytes("same"))
        ApkFinding.objects.create(submission=original, kind="ip", value="203.0.113.5")
        ApkFinding.objects.create(submission=original, kind="domain", value="x.example.com")
        again = self.make_submission(name="b.apk", content=apk_bytes("same"))
        again.duplicate_of = original
        again.save()

        self.login(self.kursant_account)
        self.client.post(reverse("apk:submission_claim", args=[again.pk]))
        self.client.post(reverse("apk:findings_copy", args=[again.pk]))
        self.assertEqual(again.findings.count(), 2)
        self.client.post(reverse("apk:findings_copy", args=[again.pk]))
        self.assertEqual(again.findings.count(), 2)

    def test_detail_page_shows_cross_references(self):
        other = self.make_submission(name="other.apk")
        ApkFinding.objects.create(submission=other, kind="domain", value="shared.example.com")
        self.claim()
        self.add("domain", "shared.example.com")
        response = self.client.get(reverse("apk:submission_detail", args=[self.pk]))
        self.assertContains(response, "+1 APK")


class AccessTests(RolesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.submission = self.make_submission()

    def test_download_requires_access_and_is_an_attachment(self):
        url = reverse("apk:submission_download", args=[self.submission.pk])
        self.client.force_login(self.plain_account)
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

        for account in (self.mvd_account, self.chilonzor_account, self.kursant_account, self.admin_account):
            self.client.force_login(account)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn("attachment", response["Content-Disposition"])
            self.assertEqual(b"".join(response.streaming_content), apk_bytes("sample.apk"))

    def test_media_is_not_served_publicly(self):
        response = self.client.get("/media/" + self.submission.file.name)
        self.assertEqual(response.status_code, 404)

    def test_every_role_sees_the_table(self):
        for account in (self.mvd_account, self.chilonzor_account, self.kursant_account, self.admin_account):
            self.client.force_login(account)
            response = self.client.get(reverse("apk:submission_list"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "sample.apk")

    def test_user_without_role_is_sent_away(self):
        self.client.force_login(self.plain_account)
        for name in ("submission_list", "review_queue", "dashboard"):
            response = self.client.get(reverse(f"apk:{name}"))
            self.assertEqual(response.status_code, 302, name)

    def test_home_redirects_by_role(self):
        self.client.force_login(self.chilonzor_account)
        self.assertRedirects(self.client.get(reverse("apk:home")), reverse("apk:review_queue"))
        self.client.force_login(self.kursant_account)
        self.assertRedirects(self.client.get(reverse("apk:home")), reverse("apk:submission_list"))
        self.client.force_login(self.mvd_account)
        self.assertRedirects(self.client.get(reverse("apk:home")), reverse("apk:submission_list"))

    def test_dashboard_is_for_admin_mvd_chilonzor_only(self):
        url = reverse("apk:dashboard")
        for account in (self.admin_account, self.mvd_account, self.chilonzor_account):
            self.client.force_login(account)
            self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.kursant_account)
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_review_queue_lists_sent_works_and_hides_buttons_from_mvd(self):
        workflow.claim(self.submission.pk, self.kursant)
        ApkFinding.objects.create(submission=self.submission, kind="ip", value="203.0.113.5")
        workflow.send_to_chilonzor(self.submission.pk, self.kursant)

        self.client.force_login(self.mvd_account)
        response = self.client.get(reverse("apk:review_queue"))
        self.assertContains(response, "sample.apk")
        detail = self.client.get(reverse("apk:submission_detail", args=[self.submission.pk]))
        self.assertNotContains(detail, reverse("apk:submission_review", args=[self.submission.pk]))

        self.client.force_login(self.chilonzor_account)
        detail = self.client.get(reverse("apk:submission_detail", args=[self.submission.pk]))
        self.assertContains(detail, reverse("apk:submission_review", args=[self.submission.pk]))

    def test_role_users_are_locked_out_of_the_rest_of_the_site(self):
        for account in (self.mvd_account, self.chilonzor_account):
            self.client.force_login(account)
            response = self.client.get(reverse("app:user_list"))
            self.assertRedirects(response, reverse("apk:home"), fetch_redirect_response=False)
        self.client.force_login(self.admin_account)
        self.assertEqual(self.client.get(reverse("app:user_list")).status_code, 200)

    def test_search_finds_by_finding_sender_and_chat(self):
        ApkFinding.objects.create(submission=self.submission, kind="domain", value="evil.example.com")
        self.make_submission(name="other.apk", sender_username="someone_else")
        self.client.force_login(self.kursant_account)
        for query, expected in (
            ("evil.example", 1),
            ("someone_else", 1),
            ("tester", 2),
            ("sample", 1),
            ("111", 2),
            ("-100222", 2),
            ("nothing-like-this", 0),
        ):
            response = self.client.get(reverse("apk:submission_list"), {"q": query})
            self.assertEqual(len(response.context["submissions"]), expected, query)

    def test_admin_can_delete_work_and_file(self):
        path = self.submission.file.path
        self.client.force_login(self.kursant_account)
        self.client.post(reverse("apk:submission_delete", args=[self.submission.pk]))
        self.assertTrue(ApkSubmission.objects.filter(pk=self.submission.pk).exists())

        self.client.force_login(self.admin_account)
        self.client.post(reverse("apk:submission_delete", args=[self.submission.pk]))
        self.assertFalse(ApkSubmission.objects.filter(pk=self.submission.pk).exists())
        import os

        self.assertFalse(os.path.exists(path))

    def test_api_key_page_is_admin_only_and_shows_token_once(self):
        url = reverse("apk:api_clients")
        self.client.force_login(self.mvd_account)
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.admin_account)
        response = self.client.post(url, {"name": "Bot", "user": self.mvd.pk})
        self.assertEqual(response.status_code, 200)
        token = response.context["new_token"]
        self.assertContains(response, token)
        client = ApiClient.objects.get()
        self.assertEqual(client.user, self.mvd)
        self.assertNotContains(self.client.get(url), token)

        # Faqat MVD hisobiga kalit berish mumkin
        response = self.client.post(url, {"name": "Bot2", "user": self.kursant.pk})
        self.assertEqual(ApiClient.objects.count(), 1)
        self.assertIsNone(response.context["new_token"])

    def test_kursant_form_excludes_role_accounts(self):
        self.client.force_login(self.admin_account)
        response = self.client.get(reverse("apk:kursant_create"))
        queryset_users = set(response.context["form"].fields["user"].queryset)
        self.assertNotIn(self.mvd, queryset_users)
        self.assertNotIn(self.chilonzor, queryset_users)
        self.assertIn(self.plain_account.profile, queryset_users)
        self.assertNotIn(self.kursant, queryset_users)

    def test_role_groups_exist(self):
        self.assertTrue(Group.objects.filter(name=GROUP_MVD).exists())
        self.assertTrue(Group.objects.filter(name=GROUP_CHILONZOR).exists())
        self.assertFalse(
            Group.objects.filter(name__in=["Teacher", "Prokuratura", "Markaziy_bank"]).exists()
        )
