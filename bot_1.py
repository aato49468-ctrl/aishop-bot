import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ══════════════════════════════════════════
#  НАСТРОЙКИ
# ══════════════════════════════════════════
TOKEN = "8013963072:AAEzxuWWMPzgRKb79ZD5cX4hlDI-KVukoJk"
ADMIN_ID = 6739433421

KEYS = {
    "base": [],
    "standard": [],
    "full": ["Aato", "SoriWer"],
}

CARD = "2200 1516 6166 6938"
OWNER = "Альберт Шукуров"
BANK = "Альфа Банк"

PRICES = {
    "base":     ("Базовый",       "299₽",  "50+ ИИ, 1 устройство"),
    "standard": ("Стандарт",      "699₽",  "200+ ИИ, 3 устройства"),
    "full":     ("Всё включено",  "1290₽", "390+ ИИ, безлимит"),
}

# ══════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pending = {}
sold = []


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


async def restart_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Главное меню:", reply_markup=main_menu())


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_sales = [s for s in sold if s["user_id"] == user_id]
    if user_sales:
        last = user_sales[-1]
        plan_name = PRICES.get(last["plan"], (last["plan"],))[0]
        await update.message.reply_text(
            f"👤 *Ваш профиль*\n\n"
            f"📦 Тариф: {plan_name}\n"
            f"🔑 Ключ: `{last['key']}`\n\n"
            f"Сайт: https://starlit-clafoutis-732c22.netlify.app",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ У вас нет активной подписки.\n\nНажмите /start чтобы купить!",
            reply_markup=main_menu()
        )


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа.")
        return

    total = len(sold)
    plan_counts = {}
    for s in sold:
        p = s["plan"]
        plan_counts[p] = plan_counts.get(p, 0) + 1

    plan_stats = ""
    for plan, count in plan_counts.items():
        plan_name = PRICES.get(plan, (plan,))[0]
        plan_stats += f"  • {plan_name}: {count} продаж\n"

    if not plan_stats:
        plan_stats = "  Пока нет продаж"

    await update.message.reply_text(
        f"📊 *Админ-панель*\n\n"
        f"💰 Всего продаж: {total}\n\n"
        f"По тарифам:\n{plan_stats}\n"
        f"🔑 Ключи:\n"
        f"  • Базовый: {len(KEYS['base'])}\n"
        f"  • Стандарт: {len(KEYS['standard'])}\n"
        f"  • Всё включено: {len(KEYS['full'])} — {', '.join(KEYS['full'])}",
        parse_mode="Markdown"
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
        keyboard = [
            [InlineKeyboardButton("✅ Я оплатил, вот скриншот", callback_data=f"paid_{plan}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="buy")]
        ]
        await query.edit_message_text(
            f"💳 *Оплата — {name}*\n\n"
            f"Сумма: *{price}*\n"
            f"Включено: {desc}\n\n"
            f"Переведите на карту:\n`{CARD}`\n"
            f"Банк: {BANK}\nПолучатель: {OWNER}\n\n"
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
            "*Это легально?*\nДа, всё официально.\n\n"
            "*Как получить доступ?*\nОплатите → скриншот → ключ за 5-10 минут.\n\n"
            "*Возврат?*\nДа, в течение 24 часов если ключ не активирован.\n\n"
            "*Сколько устройств?*\n1 / 3 / безлимит по тарифу.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="back")]])
        )

    elif data == "back":
        await query.edit_message_text("Главное меню:", reply_markup=main_menu())

    elif data.startswith("sendkey_"):
        parts = data.replace("sendkey_", "").split("_")
        buyer_id = int(parts[0])
        key_index = int(parts[1])
        plan = pending.get(buyer_id, {}).get("plan", "full")
        username = pending.get(buyer_id, {}).get("username", "Unknown")

        if plan in KEYS and key_index < len(KEYS[plan]):
            key = KEYS[plan][key_index]
            try:
                await context.bot.send_message(
                    buyer_id,
                    f"✅ *Оплата подтверждена!*\n\n"
                    f"Ваш ключ доступа:\n`{key}`\n\n"
                    f"Сайт: https://starlit-clafoutis-732c22.netlify.app\n"
                    f"Прямой доступ: https://Arena.ai\n"
                    f"Спасибо за покупку! 🎉",
                    parse_mode="Markdown"
                )
                sold.append({"user_id": buyer_id, "username": username, "plan": plan, "key": key})
                await query.edit_message_text(
                    f"✅ Ключ `{key}` отправлен @{username}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Ошибка: {e}")
        else:
            await query.edit_message_text("❌ Ключ не найден!")

    elif data.startswith("reject_"):
        buyer_id = int(data.replace("reject_", ""))
        try:
            await context.bot.send_message(
                buyer_id,
                "❌ Скриншот оплаты не подтверждён.\nСвяжитесь с поддержкой: @SoriWerr"
            )
            await query.edit_message_text("Заявка отклонена.")
        except Exception as e:
            await query.edit_message_text(f"Ошибка: {e}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message

    if msg.photo and user.id in pending and pending[user.id].get("waiting_screenshot"):
        plan_key = pending[user.id]["plan"]
        plan_name = PRICES[plan_key][0]
        price = PRICES[plan_key][1]
        username = pending[user.id]["username"]

        keyboard = []
        if plan_key in KEYS and KEYS[plan_key]:
            for i, key in enumerate(KEYS[plan_key]):
                keyboard.append([InlineKeyboardButton(f"🔑 Отправить: {key}", callback_data=f"sendkey_{user.id}_{i}")])
        else:
            keyboard.append([InlineKeyboardButton("⚠️ Нет ключей", callback_data="none")])
        keyboard.append([InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user.id}")])

        await context.bot.forward_message(ADMIN_ID, msg.chat_id, msg.message_id)
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 *Новая заявка!*\n\n"
            f"👤 @{username} (`{user.id}`)\n"
            f"📦 Тариф: {plan_name}\n"
            f"💰 Сумма: {price}\n\n"
            f"Выберите ключ для отправки:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        pending[user.id]["waiting_screenshot"] = False
        await msg.reply_text(
            "📬 Скриншот получен! Проверяем оплату.\n"
            "Ключ придёт в течение нескольких минут. ⏱"
        )

    elif context.user_data.get("waiting_key"):
        context.user_data["waiting_key"] = False
        await msg.reply_text(
            "🔑 Ключ нужно вводить на сайте!\n\n"
            "Зайдите на сайт и нажмите «🔑 Ввести ключ».",
            reply_markup=main_menu()
        )

    else:
        await msg.reply_text("Выберите действие:", reply_markup=main_menu())


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", restart_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL, message_handler))
    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
