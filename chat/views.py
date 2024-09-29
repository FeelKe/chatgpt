from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Chat, Message

TOKEN_PRICES = {
    'gpt-4o': 0.003,
    'gpt-4o-mini': 0.002,
    'gpt-3.5-turbo': 0.001,
}

def calculate_cost(model_name, tokens_used):
    if model_name in TOKEN_PRICES:
        return tokens_used * TOKEN_PRICES[model_name]
    return 0

@login_required
def index(request, chat_id=None):
    chats = Chat.objects.filter(user=request.user)
    selected_chat = None
    messages = []
    current_model = "gpt-4o"
    tokens_used = 500

    if chat_id is not None:
        selected_chat = get_object_or_404(Chat, id=chat_id, user=request.user)
        messages = selected_chat.messages.all()

    cost_in_rub = calculate_cost(current_model, tokens_used)
    cost_in_usd = (tokens_used * 0.0001)

    return render(request, 'chat.html', {
        'chats': chats,
        'selected_chat': selected_chat,
        'messages': messages,
        'tokens_used': tokens_used,
        'current_model': current_model,
        'cost_in_rub': cost_in_rub,
        'cost_in_usd': cost_in_usd,
    })

@login_required
def create_chat(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        chat = Chat(user=request.user, title=title)
        chat.save()
        return redirect('chat:index')
    return redirect('chat:index')

@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    chat.delete()
    return redirect('chat:index')

@login_required
def rename_chat(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    if request.method == 'POST':
        new_title = request.POST.get('title')
        if new_title:
            chat.title = new_title
            chat.save()
    return redirect('chat:index_with_chat', chat_id=chat_id)
