"""MVD / Chilonzor rollari uchun loyihaning qolgan bo'limlarini yopadi.

Menyudan yashirish yetarli emas - havolani qo'lda yozib kirish mumkin.
Shuning uchun tekshiruv server tomonida, har bir so'rovda bajariladi.

MVD / Chilonzor xodimi (admin bo'lmagan) uchun faqat:
  - /apk/...       (o'z bo'limi)
  - /messages/...  (bo'lim xabarnomalari shu yerga keladi)
  - login / logout / til almashtirish
ruxsat etiladi. Qolgan hamma joyda APK bo'limiga qaytariladi.
"""

from django.shortcuts import redirect

from .permissions import user_is_apk_only

# app ilovasidagi ruxsat etilgan sahifalar (url_name bo'yicha)
ALLOWED_APP_URL_NAMES = {
    "login",
    "logout",
    "set_language",
    "message_inbox",
    "message_thread",
    "home",
}


class ApkOnlyAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if user is None or not user_is_apk_only(user):
            return None

        match = request.resolver_match
        if match is None:
            return None

        if match.app_name == "apk":
            return None

        if match.app_name == "app" and match.url_name in ALLOWED_APP_URL_NAMES:
            return None

        return redirect("apk:home")
