# sidebar/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Chat
from django.contrib import messages

@login_required
def sidebar_view(request):
    chats = Chat.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'add_chat' in request.POST:
            chat_name = request.POST.get('chat_name')
            if chat_name:
                Chat.objects.create(user=request.user, name=chat_name)
                messages.success(request, 'Чат добавлен успешно!')
            else:
                messages.error(request, 'Имя чата не может быть пустым!')
        elif 'delete_chat' in request.POST:
            chat_id = request.POST.get('chat_id')
            try:
                chat = Chat.objects.get(id=chat_id, user=request.user)
                chat.delete()
                messages.success(request, 'Чат удален успешно!')
            except Chat.DoesNotExist:
                messages.error(request, 'Чат не найден!')

    return render(request, 'sidebar.html', {'chats': chats})
