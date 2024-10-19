# src/bot/exchange_api.py

import requests
import logging
import hashlib
import hmac
import time

class ExchangeAPI:
    """
    Класс для взаимодействия с API биржи.
    """

    def __init__(self, api_key, secret_key, base_url="https://api-testnet.bybit.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def get_current_price(self, symbol):
        """
        Получает текущую цену указанного актива.
        """
        endpoint = '/v5/market/tickers'
        params = {
            'symbol': symbol,
            'category': 'spot'
        }
        response = self._send_request('GET', endpoint, params)

        if response and 'result' in response:
            try:
                return float(response['result']['list'][0]['lastPrice'])
            except (ValueError, TypeError, IndexError, KeyError) as e:
                self.logger.error(f"Ошибка при парсинге цены: {e}")
                return None
        else:
            self.logger.error("Не удалось получить цену актива.")
            return None

    def _send_request(self, method, endpoint, params=None):
        """
        Отправляет подписанный запрос к API.
        """
        timestamp = str(int(time.time() * 1000))
        params = params or {}
        params['api_key'] = self.api_key
        params['timestamp'] = timestamp

        # Генерируем подпись
        sign = self._generate_signature(params)
        params['sign'] = sign

        url = self.base_url + endpoint
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=10)
            else:
                response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка при выполнении запроса: {e}")
            return None

    def _generate_signature(self, params):
        """
        Генерирует подпись для аутентификации запроса.
        """
        sorted_params = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
        hash = hmac.new(
            bytes(self.secret_key, 'utf-8'),
            bytes(sorted_params, 'utf-8'),
            hashlib.sha256
        )
        return hash.hexdigest()
