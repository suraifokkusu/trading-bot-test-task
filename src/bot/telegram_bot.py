import logging
import os
import sys
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
from bot.exchange_api import ExchangeAPI  # импорт API
from bot.strategy import GridTradingStrategy  # импорт стратегии
from config.settings import available_assets

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Токен телеграм бота из переменных окружения
TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Инициализация бота
bot = Bot(token=TOKEN)

# Инициализация API и стратегии
base_url = os.getenv('EXCHANGE_URL', 'https://api.bybit.com')  # URL для Bybit API
api = ExchangeAPI(base_url=base_url)
strategy = GridTradingStrategy(initial_capital=1000, grid_step=100, price_drop_percent=5, price_increase_percent=5)

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот, который поможет с торговлей.")

# Команда /trade для выбора актива
async def trade(update: Update, context: CallbackContext) -> None:
    assets_str = ', '.join(available_assets)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Доступные активы для торговли: {assets_str}. \n Напиши название актива, чтобы узнать его текущую цену.')

# Обработчик сообщений с выбором актива
async def asset_price(update: Update, context: CallbackContext) -> None:
    chosen_asset = update.message.text.upper()  # выбранный пользователем актив
    if chosen_asset in available_assets:
        current_price = api.get_current_price(chosen_asset)
        if current_price:
            # Выполняем торговую операцию через стратегию
            action = strategy.execute_trade(current_price)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Текущая цена {chosen_asset}: {current_price} USD\nРезультат: {action}')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Не удалось получить цену актива.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Некорректный выбор актива. Попробуйте ещё раз.")

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    # Добавляем команды /start и /trade
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trade", trade))

    # Добавляем обработчик сообщений для получения цены выбранного актива
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, asset_price))

    # Запускаем бота
    application.run_polling()
