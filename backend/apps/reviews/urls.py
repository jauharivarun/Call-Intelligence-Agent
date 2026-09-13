from django.urls import path

from . import views

urlpatterns = [
    path("", views.review_list, name="review-list"),
    path("<uuid:review_id>/", views.review_detail, name="review-detail"),
    path("<uuid:review_id>/decision/", views.review_decision, name="review-decision"),
]
