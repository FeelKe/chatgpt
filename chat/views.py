### views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Chat, Message
import logging
import aiohttp
import os
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

@login_required
def index(request, chat_id=None):
    chats = Chat.objects.filter(user=request.user)
    selected_chat = None
    messages = []
    current_model = "gpt-5-chat"

    if chat_id:
        selected_chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        messages_qs = selected_chat.messages.all()
        messages = list(messages_qs.values('sender', 'content'))
    else:
        messages = []

    return render(request, 'chat.html', {
        'chats': chats,
        'selected_chat': selected_chat,
        'messages': messages,
        'current_model': current_model,
    })

async def create_openai_thread():
    url = "https://api.openai.com/v1/threads"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "assistants=v2"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data['id']
            else:
                logger.error(f"Ошибка при создании потока: {await response.text()}")
                return None

@login_required
def create_chat(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        chat = Chat(user=request.user, title=title)
        chat.save()

        logger.info(f"Создание потока OpenAI для чата: {title}")
        thread_id = async_to_sync(create_openai_thread)()

        if thread_id:
            chat.thread_id = thread_id
            chat.save()
            logger.info(f"Поток создан с ID: {thread_id}")
        else:
            chat.delete()
            logger.error("Не удалось создать поток")
            return redirect('chat:index')

        return redirect('chat:index')
    return redirect('chat:index')

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    if chat.thread_id:
        async_to_sync(delete_openai_thread)(chat.thread_id)
    chat.delete()
    return redirect('chat:index')

async def delete_openai_thread(thread_id):
    url = f"https://api.openai.com/v1/threads/{thread_id}"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "assistants=v2"
    }
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            if response.status == 200:
                logger.info(f"Поток {thread_id} удалён успешно")
            else:
                logger.error(f"Ошибка при удалении потока: {await response.text()}")

@login_required
def rename_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    if request.method == 'POST':
        new_title = request.POST.get('title')
        if new_title:
            chat.title = new_title
            chat.save()
    return redirect('chat:index_with_chat', chat_id=chat_id)
