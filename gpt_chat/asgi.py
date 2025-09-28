import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Установите настройки окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpt_chat.settings')

# Настройка Django (должно быть выполнено до любых импортов, зависящих от приложений)
django.setup()

# После этого можно импортировать роуты и другие компоненты, зависящие от инициализации приложений
from chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
