from django.urls import path

from . import views

app_name = "apk"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    # Asosiy jadval va APK ish sahifasi
    path("works/", views.submission_list_view, name="submission_list"),
    path("works/<int:pk>/", views.submission_detail_view, name="submission_detail"),
    path("works/<int:pk>/download/", views.submission_download_view, name="submission_download"),
    path("works/<int:pk>/delete/", views.submission_delete_view, name="submission_delete"),

    # Kursant
    path("works/<int:pk>/claim/", views.submission_claim_view, name="submission_claim"),
    path("works/<int:pk>/release/", views.submission_release_view, name="submission_release"),
    path("works/<int:pk>/send/", views.submission_send_view, name="submission_send"),
    path("works/<int:pk>/findings/add/", views.finding_add_view, name="finding_add"),
    path(
        "works/<int:pk>/findings/<int:finding_pk>/delete/",
        views.finding_delete_view,
        name="finding_delete",
    ),
    path("works/<int:pk>/findings/copy/", views.findings_copy_view, name="findings_copy"),
    path("works/<int:pk>/note/", views.analysis_note_view, name="analysis_note"),

    # Chilonzor
    path("review/", views.review_queue_view, name="review_queue"),
    path("works/<int:pk>/review/", views.submission_review_view, name="submission_review"),

    # Admin
    path("kursants/", views.kursant_list_view, name="kursant_list"),
    path("kursants/create/", views.kursant_create_view, name="kursant_create"),
    path("kursants/<int:pk>/edit/", views.kursant_update_view, name="kursant_update"),
    path("kursants/<int:pk>/delete/", views.kursant_delete_view, name="kursant_delete"),
    path("api-keys/", views.api_client_list_view, name="api_clients"),
    path("api-keys/<int:pk>/toggle/", views.api_client_toggle_view, name="api_client_toggle"),
    path("api-keys/<int:pk>/delete/", views.api_client_delete_view, name="api_client_delete"),
]
