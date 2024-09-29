# sidebar/urls.py
from django.urls import path
from .views import sidebar_view

urlpatterns = [
    path('', sidebar_view, name='sidebar_view'),
]
