# example/urls.py
from django.urls import path

from example.views import liveDetection


urlpatterns = [
    path('', liveDetection),
]