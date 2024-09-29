import json
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import OpenAI
import markdown2
from .models import Chat, Message

client = OpenAI(api_key="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")

TOKEN_PRICES = {
    'gpt-4o-mini': 0.002,
    'gpt-4o': 0.003,
    'gpt-3.5-turbo': 0.001,
}

USD_TO_RUB = 100

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        model_name = "gpt-4o-mini"

        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message}
            ]
        )

        response_message = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens

        # Сохранение сообщения в БД
        chat = await Chat.objects.get(id=self.chat_id)
        Message.objects.create(chat=chat, sender='User', content=message)
        Message.objects.create(chat=chat, sender='GPT', content=response_message)

        response_html = markdown2.markdown(response_message)

        await self.send(text_data=json.dumps({
            'response': response_html,
            'tokens_used': tokens_used,
        }))
