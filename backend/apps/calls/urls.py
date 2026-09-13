from django.urls import path

from . import views

urlpatterns = [
    path("", views.call_list_create, name="call-list-create"),
    path("<uuid:call_id>/", views.call_detail, name="call-detail"),
    path("<uuid:call_id>/transcript/", views.call_transcript, name="call-transcript"),
    path("<uuid:call_id>/analysis/", views.call_analysis, name="call-analysis"),
    path("<uuid:call_id>/recording/", views.call_recording, name="call-recording"),
    path("<uuid:call_id>/reanalyze/", views.call_reanalyze, name="call-reanalyze"),
]
