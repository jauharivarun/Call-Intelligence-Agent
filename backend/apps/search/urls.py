from django.urls import path

from . import views

urlpatterns = [
    path("transcripts/", views.search_transcripts, name="search-transcripts"),
]
