from django.urls import path
from .views import login_view, UserLogoutView

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
]
