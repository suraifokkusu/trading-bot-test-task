# src/bot/data_handler.py

import os
import json
import csv
import logging

class DataHandler:
    """
    Класс для работы с историей сделок.
    """

    def __init__(self, file_path='trading_history.json', file_format='json'):
        self.file_path = file_path
        self.file_format = file_format.lower()
        self.trading_history = []
        self.logger = logging.getLogger(__name__)
        self.load_trading_history()

    def load_trading_history(self):
        """
        Загружает историю сделок из файла.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as file:
                    if self.file_format == 'json':
                        self.trading_history = json.load(file)
                    elif self.file_format == 'csv':
                        reader = csv.DictReader(file)
                        self.trading_history = list(reader)
                    else:
                        self.logger.error("Неподдерживаемый формат файла.")
                self.logger.info("История сделок загружена.")
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке истории сделок: {e}")
                self.trading_history = []
        else:
            self.logger.info("Файл истории сделок не найден. Начинаем с пустой истории.")

    def save_trading_history(self, trade_data):
        """
        Сохраняет данные о сделке в файл.
        """
        self.trading_history.append(trade_data)
        try:
            with open(self.file_path, 'w') as file:
                if self.file_format == 'json':
                    json.dump(self.trading_history, file, indent=4)
                elif self.file_format == 'csv':
                    writer = csv.DictWriter(file, fieldnames=trade_data.keys())
                    writer.writeheader()
                    writer.writerows(self.trading_history)
                else:
                    self.logger.error("Неподдерживаемый формат файла.")
            self.logger.info("История сделок сохранена.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении истории сделок: {e}")

    def get_trading_history(self):
        """
        Возвращает всю историю сделок.
        """
        return self.trading_history

    def get_statistics(self):
        """
        Вычисляет и возвращает статистику по сделкам.
        """
        total_buys = sum(1 for trade in self.trading_history if trade.get('operation_type') == 'buy')
        total_sells = sum(1 for trade in self.trading_history if trade.get('operation_type') == 'sell')
        average_buy_price = (
            sum(float(trade['price']) for trade in self.trading_history if trade.get('operation_type') == 'buy') / total_buys
            if total_buys > 0 else 0
        )
        average_sell_price = (
            sum(float(trade['price']) for trade in self.trading_history if trade.get('operation_type') == 'sell') / total_sells
            if total_sells > 0 else 0
        )

        self.logger.info("Статистика по сделкам вычислена.")

        return {
            'total_buys': total_buys,
            'total_sells': total_sells,
            'average_buy_price': average_buy_price,
            'average_sell_price': average_sell_price
        }
