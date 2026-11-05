from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class HomeRedirectTests(TestCase):
    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse("app:home"))
        self.assertRedirects(response, f"{reverse('app:login')}?next=/")

    def test_user_without_apk_access_sees_no_access_page(self):
        User.objects.create_user("plain", password="Pass12345!x")
        self.client.login(username="plain", password="Pass12345!x")
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/no_access.html")

    def test_role_group_member_goes_to_apk_home(self):
        user = User.objects.create_user("mvd", password="Pass12345!x")
        user.groups.add(Group.objects.get(name="MVD"))
        self.client.login(username="mvd", password="Pass12345!x")
        response = self.client.get(reverse("app:home"))
        self.assertRedirects(response, reverse("apk:home"), fetch_redirect_response=False)

    def test_profile_is_created_for_new_account(self):
        user = User.objects.create_user("someone", password="Pass12345!x")
        self.assertTrue(user.profile.pk)
