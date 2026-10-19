import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

load_dotenv(os.path.expanduser("~/bot_analyzer.env"))

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_B64 = os.getenv("SESSION_B64")

TARGET_CHAT = -5277014022

# Строгий список названий групп
TARGET_GROUPS = [
    "Вейп барахолка Беларусь",
    "Вейп барахолка Минск",
    "Вейп Барахолка Минск",
    "Барахолка вейп Минск"
]

# Триггерные слова (убрал "под", чтобы не ловить мусор)
TRIGGER_WORDS = [
    "куплю", "ищу", "нужен", "нужна", "нужно", "продайте", "подскажите где",
    "жижу", "жижа", "жидкость", "подик", "картридж", "карик", "испаритель",
    "одноразку", "одноразка", "вейп", "вейпы", "снюс", "шайбы"
]

client = TelegramClient(StringSession(SESSION_B64), API_ID, API_HASH)

# Флаг для первого запуска (чтобы не спамило старыми сообщениями)
first_run = True

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global first_run
    
    # Пропускаем старые сообщения при первом запуске
    if first_run:
        return

    if event.out or event.sender.bot:
        return
    if event.is_private:
        return

    chat = await event.get_chat()
    chat_title = getattr(chat, 'title', '')

    # Проверка, что это одна из наших групп
    if not any(group in chat_title for group in TARGET_GROUPS):
        return

    text = event.raw_text.lower()
    if not text:
        return

    if any(word in text for word in TRIGGER_WORDS):
        try:
            sender = await event.get_sender()
            sender_name = getattr(sender, 'first_name', 'Без имени')
            
            # Делаем ссылку на профиль (юзернейм или ID)
            if getattr(sender, 'username', None):
                sender_link = f"@{sender.username}"
            else:
                sender_link = f"[{sender_name}](tg://user?id={sender.id})"

            forward_text = (
                f"🛒 **НАШЁЛ ПОКУПАТЕЛЯ**\n\n"
                f"💬 Текст: {event.raw_text}\n\n"
                f"👤 Кто: {sender_link}\n"
                f"📍 Где: {chat_title}\n"
            )

            # parse_mode='md' нужен, чтобы ссылка на профиль работала
            await client.send_message(TARGET_CHAT, forward_text, parse_mode='md', link_preview=False)
            print(f"✅ Переслано: {event.raw_text[:50]}...")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

async def main():
    global first_run
    await client.start()
    me = await client.get_me()
    print(f"🤖 Парсер запущен от @{me.username}")
    print(f"📩 Пересылаю в чат: {TARGET_CHAT}")
    print(f"📂 Слежу за группами: {', '.join(TARGET_GROUPS)}")
    
    # Ждем 2 секунды, чтобы прогрузились старые сообщения (игнорируем их)
    await asyncio.sleep(2)
    first_run = False
    print("✅ Парсер готов ловить НОВЫЕ сообщения!")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
