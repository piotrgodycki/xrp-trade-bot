import gate_api
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
        self.check_interval = self.config['check_interval']
        self.min_usdt_balance = Decimal(str(self.config['min_usdt_balance']))

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

    def place_buy_order(self, usdt_to_use):
        price = self.get_current_price()
        amount = (usdt_to_use / price).quantize(Decimal('0.0001'))
        self.logger.info(f"Placing market BUY: {amount} XRP at {price}")
        buy_order = self.spot_api.create_order(self.symbol, 'buy', amount=str(amount), price=None, type='market')
        time.sleep(1)
        actual_trade = self.spot_api.list_user_trades(self.symbol, order_id=buy_order.id)[0]
        executed_price = Decimal(actual_trade.price)
        return executed_price, Decimal(actual_trade.amount)

    def place_sell_order(self, buy_price, amount):
        sell_price = (buy_price * self.profit_margin).quantize(Decimal('0.0001'))
        self.logger.info(f"Placing limit SELL: {amount} XRP at {sell_price}")
        sell_order = self.spot_api.create_order(self.symbol, 'sell', amount=str(amount), price=str(sell_price), type='limit')
        return sell_price, sell_order.id

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

                if exposure < self.max_exposure and usdt_balance > self.min_usdt_balance:
                    available_for_trade = min(self.buy_amount, usdt_balance - self.min_usdt_balance)
                    if available_for_trade >= Decimal('5'):
                        buy_price, amount_bought = self.place_buy_order(available_for_trade)
                        sell_price, sell_order_id = self.place_sell_order(buy_price, amount_bought)
                        self.db.record_order(float(buy_price), float(amount_bought), float(sell_price), sell_order_id)
                    else:
                        self.logger.info("Not enough free USDT to place even minimum order.")
                else:
                    self.logger.info("Max exposure reached or insufficient balance, waiting...")

            except Exception as e:
                self.logger.error(f"Main loop error: {e}")

            time.sleep(self.check_interval)
