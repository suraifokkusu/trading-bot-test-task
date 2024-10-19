# src/config/settings.py

import os
from dotenv import load_dotenv
# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем переменные окружения
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
EXCHANGE_URL = os.getenv('EXCHANGE_URL', 'https://api-testnet.bybit.com')
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Проверяем, что необходимые переменные окружения установлены
if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN не установлен в переменных окружения.")

if not API_KEY or not SECRET_KEY:
    raise ValueError("API_KEY и SECRET_KEY должны быть установлены в переменных окружения.")

# Список активов для выбора
available_assets = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'LTCUSDT', 'ADAUSDT',
    'LINKUSDT', 'BNBUSDT', 'DOGEUSDT', 'DOTUSDT', 'SOLUSDT'
]

# Параметры торговой стратегии
INITIAL_CAPITAL = int(os.getenv('INITIAL_CAPITAL', 100000))
GRID_STEP = int(os.getenv('GRID_STEP', 10))

# Настройки логирования
LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/trading_bot.log')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
