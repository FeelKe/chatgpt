import json
import os
import aiohttp
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

ASSISTANT_ID = "asst_OHU8Mdo32o8c0coIxSogPMJB"

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        print(f"WebSocket connection attempt for chat_id: {self.chat_id}")
        self.group_name = f'chat_{self.chat_id}'

        thread_id = cache.get(f'thread_id_{self.chat_id}')
        if not thread_id:
            thread_id = await self.create_thread()
            cache.set(f'thread_id_{self.chat_id}', thread_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_chat_history()
        self.ping_task = asyncio.create_task(self.send_ping())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        self.ping_task.cancel()

    async def receive(self, text_data):
        print(f"[receive] Получено сообщение: {text_data}")
        if text_data == 'ping':
            return

        data = json.loads(text_data)
        message = data.get('message', '')
        print(f"[receive] Сообщение пользователя: {message}")

        thread_id = cache.get(f'thread_id_{self.chat_id}')
        print(f"[receive] thread_id: {thread_id}")

        if not thread_id:
            await self.send(json.dumps({'error': 'Поток не найден'}))
            return

        try:
            await self.send_message_to_thread(thread_id, message)
            run_id = await self.run_assistant(thread_id)
            result = await self.poll_run_status(thread_id, run_id)
            print(f"[receive] Ответ ассистента: {result}")
            if result:
                timestamp = timezone.now().isoformat()
                await self.save_message_to_cache(self.chat_id,
                                                 {"role": "user", "content": message, "timestamp": timestamp})
                await self.save_message_to_cache(self.chat_id,
                                                 {"role": "assistant", "content": result, "timestamp": timestamp})
                await self.send(json.dumps({
                    'response': result,
                    'timestamp': timestamp
                }))
        except Exception as e:
            print(f"[receive] Ошибка: {e}")
            await self.send(json.dumps({'error': str(e)}))

    async def create_thread(self):
        url = "https://api.openai.com/v1/threads"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "assistants=v2",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Привет!"  # можно любое placeholder сообщение
                }
            ]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['id']
                else:
                    text = await response.text()
                    raise Exception(f"Ошибка создания потока: {text}")

    async def send_message_to_thread(self, thread_id, content):
        url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "assistants=v2",
            "Content-Type": "application/json"
        }
        payload = {
            "role": "user",
            "content": content
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(await response.text())

    async def run_assistant(self, thread_id):
        url = f"https://api.openai.com/v1/threads/{thread_id}/runs"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "assistants=v2",
            "Content-Type": "application/json"
        }
        payload = {
            "assistant_id": ASSISTANT_ID  # обязательно!
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['id']
                raise Exception(await response.text())

    async def poll_run_status(self, thread_id, run_id):
        url = f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "assistants=v2"
        }
        for _ in range(20):
            await asyncio.sleep(1)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    if data['status'] == 'completed':
                        return await self.get_last_assistant_message(thread_id, run_id)
                    elif data['status'] in ['failed', 'cancelled']:
                        raise Exception("Запуск ассистента завершился ошибкой.")
        raise Exception("Ассистент не ответил вовремя.")

    async def get_last_assistant_message(self, thread_id, run_id):
        url = f"https://api.openai.com/v1/threads/{thread_id}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "assistants=v2"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                for msg in reversed(data['data']):
                    if msg['role'] == 'assistant' and msg['run_id'] == run_id:
                        return msg['content'][0]['text']['value']
        raise Exception("Ответ ассистента не найден.")

    async def send_chat_history(self):
        messages = await self.get_chat_history_from_cache(self.chat_id)
        if messages:
            await self.send(json.dumps({'chat_history': messages}))

    async def get_chat_history_from_cache(self, chat_id):
        return cache.get(f'chat_history_{chat_id}', [])

    async def save_message_to_cache(self, chat_id, message):
        history = await self.get_chat_history_from_cache(chat_id)
        history.append(message)
        cache.set(f'chat_history_{chat_id}', history)

    async def send_ping(self):
        while True:
            await asyncio.sleep(30)
            await self.send(json.dumps({'type': 'ping'}))
