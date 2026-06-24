import os
import certifi
import asyncio

os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, Text
from mcrcon import MCRcon

load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_VK_ID"))

RCON_PASSWORD = os.getenv("RCON_PASSWORD")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
bot = Bot(VK_TOKEN)

users = {}
pending = {}
deny_buffer = {}


def swl_add(nick: str):
    with MCRcon(
        host=RCON_HOST,
        password=RCON_PASSWORD,
        port=RCON_PORT
    ) as mcr:
        return mcr.command(f"swl add {nick}")


@bot.on.message(text=["Начать", "начать", "/start"])
async def start(message: Message):

    users[message.from_id] = {
        "step": "nick"
    }

    await message.answer(
        "📝 Анкета на сервер\n\n"
        "🎮 Введите ваш Minecraft ник:"
    )


import traceback

@bot.on.message(text="✔️ Одобрить <nick>")
async def approve(message: Message, nick: str):
    try:
        print("APPROVE START")
        print("NICK =", nick)
        print("PENDING =", pending)

        swl_add(nick)

        print("RCON OK")

        await bot.api.messages.send(
            peer_id=pending[nick]["user_id"],
            message=f"✅ Ваша заявка одобрена!\nНик: {nick}",
            random_id=0
        )

        print("USER MSG OK")

        await message.answer(
            f"✔️ Игрок {nick} добавлен в whitelist"
        )

        print("ADMIN MSG OK")

    except Exception:
        traceback.print_exc()


@bot.on.message(text="❌ Отказать <nick>")
async def deny(message: Message, nick: str):

    print("DENY COMMAND")
    print("NICK =", nick)

    deny_buffer[message.from_id] = nick

    print("BUFFER =", deny_buffer)

    await message.answer(
        f"Введите причину отказа для {nick}:"
    )


@bot.on.message()
async def form(message: Message):

    user_id = message.from_id

    print("MESSAGE:", message.text)
    print("FROM_ID:", user_id)
    print("ADMIN_ID:", ADMIN_ID)
    print("DENY_BUFFER:", deny_buffer)

    # ==========================
    # Ввод причины отказа админом
    # ==========================
    if user_id in deny_buffer:

        print("DENY DETECTED")

        nick = deny_buffer[user_id]
        reason = message.text

        print("NICK =", nick)
        print("REASON =", reason)

        if nick in pending:

            target_user = pending[nick]["user_id"]

            try:

                await bot.api.messages.send(
                    peer_id=target_user,
                    random_id=0,
                    message=(
                        "❌ Ваша заявка отклонена.\n\n"
                        f"Причина:\n{reason}"
                    )
                )

                await message.answer(
                    f"❌ Игрок {nick} отклонён"
                )

                pending.pop(nick, None)

            except Exception as e:

                await message.answer(
                    f"Ошибка отправки отказа:\n{e}"
                )

        deny_buffer.pop(user_id, None)
        return

    # ==========================
    # Обычная анкета игрока
    # ==========================
    if user_id not in users:
        return

    step = users[user_id]["step"]

    if step == "nick":

        users[user_id]["nick"] = message.text.strip()
        users[user_id]["step"] = "age"

        await message.answer(
            "🎂 Укажите ваш возраст:"
        )
        return

    if step == "age":

        users[user_id]["age"] = message.text.strip()
        users[user_id]["step"] = "source"

        await message.answer(
            "📢 Откуда вы узнали о сервере?"
        )
        return

    if step == "source":

        users[user_id]["source"] = message.text.strip()
        users[user_id]["step"] = "goal"

        await message.answer(
            "🎯 Какая ваша цель на сервере?"
        )
        return

    if step == "goal":

        users[user_id]["goal"] = message.text.strip()

        data = users[user_id]

        pending[data["nick"]] = {
            "user_id": user_id,
            "age": data["age"],
            "source": data["source"],
            "goal": data["goal"]
        }

        keyboard = (
            Keyboard(inline=True)
            .add(Text(f"✔️ Одобрить {data['nick']}"))
            .add(Text(f"❌ Отказать {data['nick']}"))
        )

        await bot.api.messages.send(
            user_id=ADMIN_ID,
            random_id=0,
            message=(
                "📥 НОВАЯ ЗАЯВКА\n\n"
                f"👤 Ник: {data['nick']}\n"
                f"🎂 Возраст: {data['age']}\n"
                f"📢 Откуда узнал: {data['source']}\n"
                f"🎯 Цель: {data['goal']}"
            ),
            keyboard=keyboard.get_json()
        )

        await message.answer(
            "✅ Ваша заявка отправлена администрации.\n"
            "Ожидайте решения."
        )

        users.pop(user_id, None)

async def main():
    print("VK бот запущен")
    await bot.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
