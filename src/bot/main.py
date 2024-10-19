# src/bot/main.py

import os
import sys
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext  # Добавили этот импорт
)

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.bot.exchange_api import ExchangeAPI
from src.bot.strategy import GridTradingStrategy
from src.config.settings import (
    available_assets,
    TELEGRAM_API_TOKEN,
    API_KEY,
    SECRET_KEY,
    EXCHANGE_URL
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TELEGRAM_API_TOKEN)

# Глобальные данные пользователей
user_data = {}

# Состояния для ConversationHandler
PARAMETERS = 1

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, который поможет с торговлей.")
    await update.message.reply_text("Введите команду /trade, чтобы начать торговлю.")

# Команда /trade
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assets_str = ', '.join(available_assets)
    await update.message.reply_text(
        f'Доступные активы для торговли: {assets_str}. \nНапишите название актива, чтобы выбрать его.'
    )

# Обработчик выбора актива
async def choose_asset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen_asset = update.message.text.upper()
    if chosen_asset in available_assets:
        context.user_data['chosen_asset'] = chosen_asset
        await update.message.reply_text(f"Вы выбрали {chosen_asset}.")
        await update.message.reply_text("Введите команду /start_monitoring, чтобы начать мониторинг цен.")
    else:
        await update.message.reply_text("Некорректный выбор актива. Попробуйте ещё раз.")

# Команда /set_parameters
async def set_parameters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите параметры стратегии в формате:\n"
        "<начальный капитал> <шаг сетки> <процент падения цены> <процент роста цены>\n"
        "Например: 1000 100 0.1 0.1"
    )
    return PARAMETERS

# Обработчик ввода параметров
async def receive_parameters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        params = update.message.text.split()
        if len(params) != 4:
            raise ValueError("Неверное количество параметров.")

        initial_capital = float(params[0])
        grid_step = float(params[1])
        price_drop_percent = float(params[2])
        price_increase_percent = float(params[3])

        context.user_data['strategy_params'] = {
            'initial_capital': initial_capital,
            'grid_step': grid_step,
            'price_drop_percent': price_drop_percent,
            'price_increase_percent': price_increase_percent
        }

        await update.message.reply_text("Параметры стратегии установлены.")
        return ConversationHandler.END

    except ValueError as e:
        await update.message.reply_text(f"Ошибка: {e}\nПопробуйте снова.")
        return PARAMETERS

# Команда /start_monitoring
async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'chosen_asset' not in context.user_data:
        await update.message.reply_text("Сначала выберите актив с помощью команды /trade.")
        return

    strategy_params = context.user_data.get('strategy_params', {
        'initial_capital': 1000,
        'grid_step': 100,
        'price_drop_percent': 0.1,
        'price_increase_percent': 0.1
    })

    context.user_data['strategy'] = GridTradingStrategy(
        initial_capital=strategy_params['initial_capital'],
        grid_step=strategy_params['grid_step'],
        price_drop_percent=strategy_params['price_drop_percent'],
        price_increase_percent=strategy_params['price_increase_percent']
    )

    context.user_data['api'] = ExchangeAPI(api_key=API_KEY, secret_key=SECRET_KEY, base_url=EXCHANGE_URL)

    chat_id = update.effective_chat.id
    job = context.job_queue.run_repeating(
        periodic_price_check,
        interval=60,
        first=0,
        chat_id=chat_id,
        name=str(chat_id),
        data=context.user_data
    )
    context.user_data['job'] = job

    await update.message.reply_text("Мониторинг цен запущен. Бот будет автоматически проверять цены каждые 60 секунд.")

# Функция периодической проверки цен
async def periodic_price_check(context: CallbackContext):
    job = context.job
    chat_id = job.chat_id
    bot = context.bot
    user_data = job.data

    chosen_asset = user_data.get('chosen_asset')
    strategy = user_data.get('strategy')
    api = user_data.get('api')

    if not all([chosen_asset, strategy, api]):
        await bot.send_message(chat_id=chat_id, text="Ошибка: Данные стратегии отсутствуют.")
        return

    current_price = api.get_current_price(chosen_asset)
    if current_price:
        action = strategy.execute_trade(current_price)
        message = f'Текущая цена {chosen_asset}: {current_price} USD\nРезультат: {action}'
        await bot.send_message(chat_id=chat_id, text=message)

        if action.startswith("Покупка") or action.startswith("Продажа"):
            await bot.send_message(chat_id=chat_id, text=f"Совершено действие: {action}")

        if strategy.remaining_capital < strategy.grid_step:
            await bot.send_message(chat_id=chat_id, text="Капитал исчерпан. Мониторинг остановлен.")
            job.schedule_removal()
    else:
        await bot.send_message(chat_id=chat_id, text="Не удалось получить цену актива.")

# Команда /stop_monitoring
async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'job' in context.user_data:
        context.user_data['job'].schedule_removal()
        del context.user_data['job']
        await update.message.reply_text("Мониторинг цен остановлен.")
    else:
        await update.message.reply_text("Мониторинг не запущен.")

# Команда /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    strategy = context.user_data.get('strategy')
    if strategy:
        message = (
            f"Текущий баланс: {strategy.remaining_capital}\n"
            f"Открытые позиции: {strategy.purchase_prices}"
        )
    else:
        message = "Стратегия не запущена."
    await update.message.reply_text(message)

def main():
    application = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('set_parameters', set_parameters)],
        states={
            PARAMETERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_parameters)],
        },
        fallbacks=[],
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trade", trade))
    application.add_handler(CommandHandler("start_monitoring", start_monitoring))
    application.add_handler(CommandHandler("stop_monitoring", stop_monitoring))
    application.add_handler(CommandHandler("status", status))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choose_asset))

    application.run_polling()

if __name__ == '__main__':
    main()
