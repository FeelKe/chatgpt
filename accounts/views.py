# accounts/views.py

from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

class UserLoginView(LoginView):
    template_name = 'login.html'
    next_page = reverse_lazy('chat')

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')
