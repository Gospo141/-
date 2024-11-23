import asyncio
import logging
import requests
import nest_asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

nest_asyncio.apply()

# Логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Токен бота та API ключ
TOKEN = '7540012321:AAEq6OkqrlEEEZEEtY6_E4_GlcOMgJq3w8k'
NEWS_API_KEY = '92d5b5293bea437281d886c00ffbf842'

# Список для гри
game_statements = [
    {
        "text": "Генерали в Україні повинні бути в окопах. Генерал, який не був в окопі, для мене — НЕ генерал",
        "is_true": True
    },
    {
        "text": "Маніпуляція: Валерій Залужний у Британії «порадив українським військовим не боятися смерті, бо шансів на виживання у них все одно немає)",
        "is_true": False
    }
]

# Список істинних тверджень
truth_sentences = [
    "чоловік, який працював на зс рф під час окупації правобережжя херсонщини, після деокупації пішов у тцк одеської області, — гбр",
    "чиновниця львівської обласної мсек виявила прихований мільйонний стан, — гбр"
]

# Стани розмови
ASK_TEXT = 1
ASK_NEWS_QUERY = 2
ASK_RATING = 3
ASK_GAME = 4  # Створюємо новий стан для гри

# Створення меню
def get_main_menu():
    keyboard = [
        [KeyboardButton("✅ Перевірка фактів"), KeyboardButton("📰 Отримання новин")],
        [KeyboardButton("📚 Інструкції"), KeyboardButton("🛡️ Рекомендації")],
        [KeyboardButton("ℹ️ Інформація про бота"), KeyboardButton("⭐️ Оцінити бота")],
        [KeyboardButton("🎮 Гра на протидію дезінформації"), KeyboardButton("🔗 Приєднатися до спільноти")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Кнопка повернення
def get_back_to_menu_button():
    keyboard = [[KeyboardButton("🔙 Повернутися до меню")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Кнопки оцінки
def get_rating_buttons():
    keyboard = [
        [KeyboardButton("1"), KeyboardButton("2"), KeyboardButton("3")],
        [KeyboardButton("4"), KeyboardButton("5")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Кнопки гри
def get_game_buttons():
    keyboard = [
        [KeyboardButton("Правда"), KeyboardButton("Фейк")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функція для старту
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '👋 Привіт! Я бот для отримання новин та перевірки фактів. Виберіть дію:',
        reply_markup=get_main_menu()
    )

# Обробка текстових повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()

    if text == "✅ Перевірка фактів":
        await update.message.reply_text("📝 Відправте текст для перевірки фактів:", reply_markup=get_back_to_menu_button())
        context.user_data['state'] = ASK_TEXT
    elif text == "📰 Отримання новин":
        await update.message.reply_text("🔍 Введіть запит для пошуку новин:", reply_markup=get_back_to_menu_button())
        context.user_data['state'] = ASK_NEWS_QUERY
    elif text == "📚 Інструкції":
        await show_instructions(update)
    elif text == "🛡️ Рекомендації":
        await show_recommendations(update)
    elif text == "ℹ️ Інформація про бота":
        await update.message.reply_text(
            "*Цей бот дозволяє отримувати новини та перевіряти факти.*\n\n"
            "_Перевіряйте правдивість інформації та не діліться фейками!_",
            reply_markup=get_back_to_menu_button(),
            parse_mode="Markdown"
        )
    elif text == "⭐️ Оцінити бота":
        await update.message.reply_text("⭐️ Оцініть бота від 1 до 5", reply_markup=get_rating_buttons())
        context.user_data['state'] = ASK_RATING
    elif text == "🎮 Гра на протидію дезінформації":
        await start_game(update, context)
    elif text == "🔗 Приєднатися до спільноти":
        await update.message.reply_text(
            "Приєднатися до нашої спільноти: [Telegram](https://t.me/+a66JcCA4uRQ3NjRi)",
            parse_mode="Markdown", reply_markup=get_back_to_menu_button()
        )
    elif text == "🔙 Повернутися до меню":
        await clear_chat(update, context)
    else:
        # Перевірка стану гри
        user_state = context.user_data.get('state')
        if user_state == ASK_GAME:
            await process_game_answer(update, context)
        else:
            await process_user_input(update, context)

# Старт гри на протидію дезінформації
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = ASK_GAME  # Встановлюємо стан гри
    context.user_data['game_index'] = 0  # Індекс поточної гри
    await show_next_game_statement(update, context)

# Показати наступне твердження в грі
async def show_next_game_statement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_index = context.user_data.get('game_index', 0)
    if game_index < len(game_statements):
        statement = game_statements[game_index]['text']
        await update.message.reply_text(
            f"🤔 Чи це правда чи фейк?\n\n{statement}",
            reply_markup=get_game_buttons()
        )
    else:
        # Виводимо повідомлення про завершення гри і кнопки повернення
        await update.message.reply_text(
            "🎉 Вітаємо! Ви завершили гру. Можете повернутися до меню.",
            reply_markup=get_back_to_menu_button()
        )

# Обробка вибору користувача в грі
async def process_game_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_answer = update.message.text.strip()
    game_index = context.user_data.get('game_index', 0)
    statement = game_statements[game_index]

    # Перевірка відповіді
    if (user_answer == "Правда" and statement['is_true']) or (user_answer == "Фейк" and not statement['is_true']):
        await update.message.reply_text("✅ Молодець! Ви вгадали.")
    else:
        await update.message.reply_text(
            f"❌ Ви не вгадали. Це було {'правда' if statement['is_true'] else 'фейк'}.",
        )

    # Збільшуємо індекс і відправляємо наступне твердження
    context.user_data['game_index'] += 1
    await show_next_game_statement(update, context)

# Обробка введення користувача
async def process_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_state = context.user_data.get('state')
    if user_state == ASK_TEXT:
        user_text = update.message.text.strip()
        if user_text in truth_sentences:
            await update.message.reply_text("✅ *Це правда!*", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Це фейк!*", parse_mode="Markdown")
    elif user_state == ASK_NEWS_QUERY:
        query = update.message.text.strip()
        await get_news(update, query)
    elif user_state == ASK_RATING:
        rating = update.message.text.strip()
        if rating.isdigit() and 1 <= int(rating) <= 5:
            await update.message.reply_text(f"Дякуємо за вашу оцінку: {rating} з 5!", parse_mode="Markdown")
            await update.message.reply_text("🔙 Повернутися до меню", reply_markup=get_back_to_menu_button())
        else:
            await update.message.reply_text("❌ Введіть число від *1* до *5*.", parse_mode="Markdown")
    context.user_data['state'] = None

# Очищення чату
async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    for i in range(0, 10):  # Видаляємо до 10 останніх повідомлень
        try:
            await context.bot.delete_message(chat_id, message_id - i)
        except Exception:
            pass
    await start(update, context)

# Відображення інструкцій
async def show_instructions(update: Update) -> None:
    instructions = (
        "*📚 Інструкції:*\n"
        "1. Перевіряйте джерела інформації.\n"
        "2. Знайомтеся з фактами, перш ніж ділитися інформацією.\n"
        "3. Використовуйте спеціалізовані платформи для перевірки фактів."
    )
    await update.message.reply_text(instructions, reply_markup=get_back_to_menu_button(), parse_mode="Markdown")

# Відображення рекомендацій
async def show_recommendations(update: Update) -> None:
    recommendations = (
        "*🛡️ Рекомендації по протидії дезінформації:*\n"
        "1. Перевіряйте джерела інформації.\n"
        "2. Не діліться неперевіреною інформацією.\n"
        "3. Використовуйте фактчекінгові ресурси."
    )
    await update.message.reply_text(recommendations, reply_markup=get_back_to_menu_button(), parse_mode="Markdown")

# Пошук новин
async def get_news(update: Update, query: str) -> None:
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        if articles:
            for article in articles[:3]:
                title = article.get("title", "Немає заголовка")
                description = article.get("description", "Немає опису")
                url = article.get("url", "")
                await update.message.reply_text(
                    f"📌 *{title}*\n\n{description}\n\n[Читати далі]({url})", parse_mode="Markdown"
                )
        else:
            await update.message.reply_text("❌ Новини за вашим запитом не знайдені.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Сталася помилка при отриманні новин.", parse_mode="Markdown")
    await update.message.reply_text("🔙 Повернутися до меню", reply_markup=get_back_to_menu_button())

# Основна функція запуску бота
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
