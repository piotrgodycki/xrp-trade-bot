import gate_api
from gate_api import Order
from decimal import Decimal
import yaml
import time
from database import OrderDB
from logger import setup_logger

class GridTrader:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = yaml.safe_load(f)

        self.logger = setup_logger()

        self.api_key = self.config['api_key']
        self.api_secret = self.config['api_secret']
        self.symbol = self.config['symbol']
        self.buy_amount = Decimal(str(self.config['buy_amount']))
        self.profit_margin = Decimal(str(self.config['profit_margin']))
        self.max_exposure = Decimal(str(self.config['max_exposure']))
        self.max_buy_price = Decimal(str(self.config['max_buy_price']))
        self.moving_average_candles = int(self.config['moving_average_candles'])
        self.sell_ma_threshold = Decimal(str(self.config['sell_ma_threshold']))
        self.check_interval = self.config['check_interval']
        self.min_usdt_balance = Decimal(str(self.config['min_usdt_balance']))
        self.min_trade_usdt = Decimal(str(self.config['min_trade_usdt']))

        self.db = OrderDB(self.config['database_file'])
        self.setup_api()

    def setup_api(self):
        client = gate_api.ApiClient(gate_api.Configuration(key=self.api_key, secret=self.api_secret))
        self.spot_api = gate_api.SpotApi(client)

    def get_balance(self, currency):
        balances = self.spot_api.list_spot_accounts()
        for b in balances:
            if b.currency == currency:
                return Decimal(str(b.available))
        return Decimal('0')

    def get_current_price(self):
        ticker = self.spot_api.list_tickers(currency_pair=self.symbol)
        return Decimal(ticker[0].last)

    def get_moving_average(self):
        candles = self.spot_api.list_candlesticks(
            currency_pair=self.symbol, interval="5m", limit=self.moving_average_candles)
        closes = [Decimal(candle[2]) for candle in candles]  # candle[2] is close price
        return sum(closes) / len(closes)

    def place_buy_order(self, usdt_to_use):
        price = self.get_current_price()
        amount = (usdt_to_use / price).quantize(Decimal('0.0001'))

        # Double-check trade value against min trade USDT
        if (amount * price) < self.min_trade_usdt:
            self.logger.warning(f"Buy order below min trade size: {amount} XRP ({amount * price} USDT)")
            return None, None

        self.logger.info(f"Placing market BUY: {amount} XRP at {price}")

        buy_order = Order(
            currency_pair=self.symbol,
            side='buy',
            amount=str(amount),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        result = self.spot_api.create_order(buy_order)
        time.sleep(1)
        actual_trade = self.spot_api.list_user_trades(self.symbol, order_id=result.id)[0]
        executed_price = Decimal(actual_trade.price)
        return executed_price, Decimal(actual_trade.amount)

    def place_sell_order(self, sell_price, amount):
        sell_price = sell_price.quantize(Decimal('0.0001'))
        self.logger.info(f"Placing limit SELL: {amount} XRP at {sell_price}")

        sell_order = Order(
            currency_pair=self.symbol,
            side='sell',
            amount=str(amount),
            price=str(sell_price),
            type='limit'
        )
        result = self.spot_api.create_order(sell_order)
        return sell_price, result.id

    def check_filled_orders(self):
        open_orders = self.db.get_open_orders()
        for order_id in open_orders:
            try:
                order = self.spot_api.get_order(self.symbol, order_id)
                if order.status == 'closed':
                    self.logger.info(f"Order {order_id} sold!")
                    self.db.update_order_status(order_id, 'closed')
            except Exception as e:
                self.logger.warning(f"Error checking order {order_id}: {e}")

    def run(self):
        while True:
            try:
                self.check_filled_orders()
                exposure = Decimal(str(self.db.get_open_exposure()))
                self.logger.info(f"Current exposure: {exposure} / {self.max_exposure}")

                usdt_balance = self.get_balance('USDT')
                self.logger.info(f"Available USDT balance: {usdt_balance}")

                current_price = self.get_current_price()

                # BUY LOGIC
                if current_price <= self.max_buy_price and exposure < self.max_exposure and usdt_balance > self.min_usdt_balance:
                    available_for_trade = min(self.buy_amount, usdt_balance - self.min_usdt_balance)
                    if available_for_trade >= self.min_trade_usdt:
                        buy_price, amount_bought = self.place_buy_order(available_for_trade)
                        if buy_price is not None:
                            # SELL LOGIC - dynamic sell price
                            ma_price = self.get_moving_average()
                            smart_sell_price = buy_price * self.profit_margin
                            if current_price >= ma_price * self.sell_ma_threshold:
                                smart_sell_price = current_price

                            sell_price, sell_order_id = self.place_sell_order(smart_sell_price, amount_bought)
                            self.db.record_order(float(buy_price), float(amount_bought), float(sell_price), sell_order_id)
                        else:
                            self.logger.info("Skipped due to trade below minimum size.")
                    else:
                        self.logger.info("Not enough free USDT to place minimum trade.")
                else:
                    self.logger.info("Buy conditions not met. Waiting...")

            except Exception as e:
                self.logger.error(f"Main loop error: {e}")

            time.sleep(self.check_interval)
