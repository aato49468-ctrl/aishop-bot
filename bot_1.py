import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ══════════════════════════════════════════
#  НАСТРОЙКИ — заполни сам
# ══════════════════════════════════════════  
TOKEN = "8013963072:AAEzxuWWMPzgRKb79ZD5cX4hlDI-KVukoJk"
ADMIN_ID = 6739433421

# Ключи для каждого тарифа: ключ -> URL
KEYS = {
    "base": [
        # Добавь ключи для базового тарифа
        # "ключ1",
        # "ключ2",
    ],
    "standard": [
        # Добавь ключи для стандарта
    ],
    "full": [
        # Добавь ключи для "всё включено"
        "Aato",  # пример
    ],
}

# Реквизиты оплаты
CARD = "2200 1516 6166 6938"
OWNER = "Альберт Шукуров"
BANK = "Альфа Банк"

# Цены
PRICES = {
    "base":     ("Базовый",       "299₽",  "50+ ИИ, 1 устройство"),
    "standard": ("Стандарт",      "699₽",  "200+ ИИ, 3 устройства"),
    "full":     ("Всё включено",  "1290₽", "390+ ИИ, безлимит"),
}

# ══════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище заявок: {user_id: {"plan": ..., "username": ...}}
pending = {}


def main_menu():
    keyboard = [
        [InlineKeyboardButton("🛒 Купить доступ", callback_data="buy")],
        [InlineKeyboardButton("🔑 У меня есть ключ", callback_data="haskey")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
    ]
    return InlineKeyboardMarkup(keyboard)


def plans_menu():
    keyboard = [
        [InlineKeyboardButton("🔹 Базовый — 299₽", callback_data="plan_base")],
        [InlineKeyboardButton("🔸 Стандарт — 699₽", callback_data="plan_standard")],
        [InlineKeyboardButton("👑 Всё включено — 1290₽", callback_data="plan_full")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в *AI Shop*!\n\n"
        "Здесь вы можете получить доступ к *390+ ИИ-сервисам* в одном месте.\n"
        "ChatGPT, Claude, Gemini, Midjourney и многие другие.\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    if data == "buy":
        await query.edit_message_text(
            "🛒 *Выберите тариф:*\n\n"
            "🔹 *Базовый — 299₽* навсегда\n50+ ИИ, 1 устройство\n\n"
            "🔸 *Стандарт — 699₽* навсегда\n200+ ИИ, 3 устройства\n\n"
            "👑 *Всё включено — 1290₽* навсегда\n390+ ИИ, безлимит устройств",
            parse_mode="Markdown",
            reply_markup=plans_menu()
        )

    elif data.startswith("plan_"):
        plan = data.replace("plan_", "")
        name, price, desc = PRICES[plan]
        pending[user.id] = {"plan": plan, "username": user.username or user.first_name}

        keyboard = [[InlineKeyboardButton("✅ Я оплатил, вот скриншот", callback_data=f"paid_{plan}")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="buy")]]

        await query.edit_message_text(
            f"💳 *Оплата — {name}*\n\n"
            f"Сумма: *{price}*\n"
            f"Включено: {desc}\n\n"
            f"Переведите на карту:\n"
            f"`{CARD}`\n"
            f"Банк: {BANK}\n"
            f"Получатель: {OWNER}\n\n"
            f"⚠️ *Важно:* переводите *без комментария!*\n"
            f"После оплаты нажмите кнопку ниже и отправьте скриншот.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("paid_"):
        plan = data.replace("paid_", "")
        pending[user.id] = {"plan": plan, "username": user.username or user.first_name, "waiting_screenshot": True}
        await query.edit_message_text(
            "📸 Отлично! Теперь отправьте *скриншот оплаты* в этот чат.\n\n"
            "После проверки вы получите ключ в течение нескольких минут.",
            parse_mode="Markdown"
        )

    elif data == "haskey":
        await query.edit_message_text(
            "🔑 Введите ваш ключ доступа:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )
        context.user_data["waiting_key"] = True

    elif data == "support":
        await query.edit_message_text(
            "💬 *Поддержка*\n\nПишите: @SoriWerr\n\nОтвечаем быстро, помогаем с любым вопросом!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )

    elif data == "faq":
        await query.edit_message_text(
            "❓ *Частые вопросы*\n\n"
            "*Это легально?*\nДа, всё официально. Никаких взломов.\n\n"
            "*Как получить доступ?*\nОплатите → пришлите скриншот → получите ключ за 5-10 минут.\n\n"
            "*Возврат?*\nДа, в течение 24 часов если ключ не активирован.\n\n"
            "*Сколько устройств?*\nЗависит от тарифа: 1 / 3 / безлимит.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )

    elif data == "back":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=main_menu()
        )

    # Админ подтверждает оплату
    elif data.startswith("approve_"):
        buyer_id = int(data.replace("approve_", ""))
        plan = pending.get(buyer_id, {}).get("plan", "full")

        if KEYS.get(plan):
            key = KEYS[plan].pop(0)
            try:
                await context.bot.send_message(
                    buyer_id,
                    f"✅ *Оплата подтверждена!*\n\n"
                    f"Ваш ключ доступа:\n`{key}`\n\n"
                    f"Введите его на сайте в разделе «🔑 Ввести ключ».\n"
                    f"Спасибо за покупку! 🎉",
                    parse_mode="Markdown"
                )
                await query.edit_message_text(f"✅ Ключ отправлен покупателю {buyer_id}.")
            except Exception as e:
                await query.edit_message_text(f"Ошибка отправки: {e}")
        else:
            await query.edit_message_text("❌ Ключи для этого тарифа закончились! Добавь новые в bot.py")

    elif data.startswith("reject_"):
        buyer_id = int(data.replace("reject_", ""))
        try:
            await context.bot.send_message(
                buyer_id,
                "❌ К сожалению, скриншот оплаты не подтверждён.\n"
                "Пожалуйста, свяжитесь с поддержкой: @SoriWerr"
            )
            await query.edit_message_text("Заявка отклонена.")
        except Exception as e:
            await query.edit_message_text(f"Ошибка: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    # Пользователь прислал скриншот
    if msg.photo and user.id in pending and pending[user.id].get("waiting_screenshot"):
        plan_key = pending[user.id]["plan"]
        plan_name = PRICES[plan_key][0]
        price = PRICES[plan_key][1]
        username = pending[user.id]["username"]

        keyboard = [
            [InlineKeyboardButton("✅ Подтвердить и выдать ключ", callback_data=f"approve_{user.id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")],
        ]

        await context.bot.forward_message(ADMIN_ID, msg.chat_id, msg.message_id)
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 *Новая заявка на оплату!*\n\n"
            f"👤 Пользователь: @{username} (`{user.id}`)\n"
            f"📦 Тариф: {plan_name}\n"
            f"💰 Сумма: {price}\n\n"
            f"Подтвердите оплату:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        pending[user.id]["waiting_screenshot"] = False
        await msg.reply_text(
            "📬 Скриншот получен! Проверяем оплату.\n"
            "Ключ придёт в течение нескольких минут. ⏱"
        )

    # Пользователь вводит ключ
    elif context.user_data.get("waiting_key"):
        context.user_data["waiting_key"] = False
        await msg.reply_text(
            "🔑 Ключ нужно вводить на сайте!\n\n"
            "Зайдите на сайт и нажмите кнопку «🔑 Ввести ключ».",
            reply_markup=main_menu()
        )

    else:
        await msg.reply_text("Выберите действие:", reply_markup=main_menu())


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, message_handler))
    print("Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
