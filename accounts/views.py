from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.contrib.auth.models import User
from .forms import LoginForm
from django.urls import reverse_lazy

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password', '')

            try:
                user = User.objects.get(username=username)

                if not user.password or user.password.startswith('!'):
                    login(request, user)  # Вход без пароля
                    return redirect('chat:index')
                else:  # Если пароль установлен
                    if password:  # Если пароль введён
                        authenticated_user = authenticate(request, username=username, password=password)
                        if authenticated_user:
                            login(request, authenticated_user)
                            return redirect('chat:index')
                        else:
                            form.add_error('password', 'Пароль неверен.')  # Пароль неверен
                    else:
                        form.add_error('password', 'Пароль обязателен для этого пользователя.')  # Пароль не введён

            except User.DoesNotExist:
                form.add_error('username', 'Пользователь с таким именем не существует.')  # Пользователь не найден

        form.add_error(None, 'Неверное имя пользователя или пароль.')  # Общая ошибка
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})
