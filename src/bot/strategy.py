# src/bot/strategy.py

import logging

class GridTradingStrategy:
    """
    Класс для реализации сеточной торговой стратегии.
    """

    def __init__(self, initial_capital, grid_step, price_drop_percent, price_increase_percent):
        self.initial_capital = initial_capital
        self.grid_step = grid_step
        self.price_drop_percent = price_drop_percent
        self.price_increase_percent = price_increase_percent
        self.purchase_prices = []
        self.remaining_capital = initial_capital
        self.logger = logging.getLogger(__name__)

    def execute_trade(self, current_price):
        """
        Выполняет торговую операцию на основе текущей цены.
        """
        self.logger.info(f"Текущая цена: {current_price}")
        self.logger.info(f"Цены покупок: {self.purchase_prices}")
        self.logger.info(f"Оставшийся капитал: {self.remaining_capital}")

        if self.should_buy(current_price):
            if self.remaining_capital >= self.grid_step:
                self.purchase_prices.append(current_price)
                self.remaining_capital -= self.grid_step
                self.logger.info(f"Покупка по цене: {current_price}")
                return f"Покупка по цене: {current_price}"
            else:
                self.logger.info("Недостаточно капитала для покупки.")
                return "Недостаточно капитала для покупки."

        if self.should_sell(current_price):
            if self.purchase_prices:
                purchase_price = self.purchase_prices.pop(0)
                self.remaining_capital += self.grid_step
                self.logger.info(f"Продажа по цене: {current_price}")
                return f"Продажа по цене: {current_price}"
            else:
                self.logger.info("Нет позиций для продажи.")
                return "Нет позиций для продажи."

        return "Ожидание."

    def should_buy(self, current_price):
        """
        Определяет, следует ли совершить покупку.
        """
        if not self.purchase_prices:
            reference_price = current_price
        else:
            reference_price = min(self.purchase_prices)

        return current_price <= reference_price * (1 - self.price_drop_percent / 100)

    def should_sell(self, current_price):
        """
        Определяет, следует ли совершить продажу.
        """
        if not self.purchase_prices:
            return False

        reference_price = max(self.purchase_prices)
        return current_price >= reference_price * (1 + self.price_increase_percent / 100)
