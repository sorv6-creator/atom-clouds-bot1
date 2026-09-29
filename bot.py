"""
Telegram-бот Atom Clouds — приём заказов из Mini App.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


# ═══════════════════════════════════════════════
# ЗАГРУЗКА .env
# ═══════════════════════════════════════════════

load_dotenv()

BOT_TOKEN   = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID    = int(os.getenv("ADMIN_ID", "0") or 0)
MINIAPP_URL = os.getenv("MINIAPP_URL", "").strip()
MANAGER_URL = os.getenv("MANAGER_URL", "https://t.me/prodazavpn").strip()
OWNER_URL   = os.getenv("OWNER_URL", "https://t.me/gipardd").strip()


# ═══════════════════════════════════════════════
# ПРОВЕРКА НАСТРОЕК
# ═══════════════════════════════════════════════

if not BOT_TOKEN:
    raise SystemExit(
        "❌ BOT_TOKEN не найден в .env\n\n"
        "Проверь:\n"
        "1. Файл называется ровно '.env' (не .env.txt)\n"
        "2. Лежит рядом с bot.py\n"
        "3. Строка выглядит так: BOT_TOKEN=8814140181:AAE...\n"
    )

if len(BOT_TOKEN) < 40:
    raise SystemExit(
        f"❌ BOT_TOKEN слишком короткий ({len(BOT_TOKEN)} символов).\n"
        f"Правильный токен ~46 символов."
    )

if not ADMIN_ID:
    raise SystemExit("❌ ADMIN_ID не найден в .env")

print(f"✅ Токен загружен (длина: {len(BOT_TOKEN)})")
print(f"✅ Админ ID: {ADMIN_ID}")
print(f"✅ Mini App: {MINIAPP_URL}")


# ═══════════════════════════════════════════════
# БОТ
# ═══════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍 Открыть магазин",
            web_app=WebAppInfo(url=MINIAPP_URL),
        )],
        [InlineKeyboardButton(
            text="💬 Менеджер",
            url=MANAGER_URL,
        )],
        [InlineKeyboardButton(
            text="👤 Владелец",
            url=OWNER_URL,
        )],
    ])


# ═══════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в <b>Atom Clouds</b> ☁️\n\n"
        "🔞 Продукция только для лиц старше 18 лет.\n"
        "Никотин вызывает зависимость.\n\n"
        "Нажми кнопку ниже, чтобы открыть каталог 👇",
        reply_markup=main_kb(),
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Помощь</b>\n\n"
        "/start — открыть магазин\n"
        "/help — эта справка\n"
        "/myid — узнать свой Telegram ID\n\n"
        f"💬 Менеджер: {MANAGER_URL}\n"
        f"👤 Владелец: {OWNER_URL}"
    )


@dp.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(
        f"🆔 Твой Telegram ID:\n<code>{message.from_user.id}</code>\n\n"
        "Скопируй его и вставь в ADMIN_ID в .env, если это твой бот."
    )


# ═══════════════════════════════════════════════
# ПРИЁМ ЗАКАЗА ИЗ MINI APP
# ═══════════════════════════════════════════════

@dp.message(F.web_app_data)
async def handle_order(message: Message):
    """Принимает заказ из Mini App и шлёт админу."""
    try:
        data = json.loads(message.web_app_data.data)
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        await message.answer("❌ Ошибка обработки заказа")
        return

    if data.get("action") != "order":
        await message.answer("❓ Неизвестное действие")
        return

    items    = data.get("items", [])
    total    = data.get("total", 0)
    customer = data.get("customer", {})
    order_id = data.get("orderId", int(datetime.now().timestamp()) % 100000)
    user     = message.from_user

    if not items:
        await message.answer("❌ Корзина пуста")
        return

    # Формируем текст заказа
    items_text = "\n".join(
        f"• {i.get('name', '?')} × {i.get('qty', 1)} = "
        f"{i.get('price', 0) * i.get('qty', 1)} ₽"
        for i in items
    )

    customer_lines = [
        f"👤 <b>Имя:</b> {customer.get('name', 'не указано')}"
    ]
    if customer.get("phone"):
        customer_lines.append(f"📞 <b>Телефон:</b> {customer['phone']}")
    if customer.get("note"):
        customer_lines.append(f"💬 <b>Комментарий:</b> {customer['note']}")
    customer_lines.append(
        f"✈️ <b>Telegram:</b> {user.first_name}"
        + (f" (@{user.username})" if user.username else "")
    )
    customer_lines.append(f"🆔 <code>{user.id}</code>")

    order_text = (
        f"🛒 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n"
        f"<b>Atom Clouds</b> ☁️\n"
        f"{'━' * 22}\n\n"
        f"<b>Товары:</b>\n{items_text}\n\n"
        f"💰 <b>ИТОГО: {total} ₽</b>\n\n"
        f"{'━' * 22}\n"
        f"<b>Покупатель:</b>\n"
        + "\n".join(customer_lines)
        + f"\n\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # Кнопки для админа
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Написать покупателю",
            url=f"tg://user?id={user.id}",
        )],
    ])

    # Отправка админу
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=order_text,
            reply_markup=kb,
        )
        logger.info(f"✅ Заказ #{order_id} отправлен админу {ADMIN_ID}")
    except Exception as e:
        logger.error(f"❌ Не удалось отправить админу: {e}")

    # Ответ покупателю
    try:
        await message.answer(
            f"✅ <b>Заказ #{order_id} принят!</b>\n\n"
            f"{items_text}\n\n"
            f"💰 Итого: <b>{total} ₽</b>\n\n"
            "Менеджер свяжется с тобой в ближайшее время. 🚀\n\n"
            f"💬 Менеджер: {MANAGER_URL}",
            reply_markup=main_kb(),
        )
    except Exception as e:
        logger.error(f"Не удалось отправить покупателю: {e}")


# ═══════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════

async def main():
    logger.info("═" * 40)
    logger.info("Бот Atom Clouds запущен")
    logger.info(f"Mini App: {MINIAPP_URL}")
    logger.info(f"Админ ID: {ADMIN_ID}")
    logger.info("═" * 40)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())