"""URL configuration for chilonzor project (APK tahlil tizimi).

APK fayllar ochiq `/media/` orqali berilmaydi - ular faqat tizimga kirgan va
ruxsati bor foydalanuvchiga `apk:submission_download` orqali yuklab olinadi."""
from django.contrib import admin
from django.urls import include, path

from apk.api import receive_apk_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Botdan APK qabul qilish (Authorization: Bearer <kalit>)
    path('api/apk/', receive_apk_view, name='api_receive_apk'),
    path('apk/', include('apk.urls')),
    path('', include('app.urls')),
]
