import gate_api
from gate_api import Order
from decimal import Decimal
import yaml
import time
from logger import setup_logger

class MomentumTrader:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = yaml.safe_load(f)

        self.logger = setup_logger()

        self.api_key = self.config['api_key']
        self.api_secret = self.config['api_secret']
        self.symbol = self.config['symbol']
        self.trade_amount = Decimal(str(self.config['trade_amount']))
        self.buy_threshold = Decimal(str(self.config['buy_threshold']))
        self.sell_threshold = Decimal(str(self.config['sell_threshold']))
        self.check_interval = self.config['check_interval']
        self.min_usdt_balance = Decimal(str(self.config['min_usdt_balance']))
        self.min_trade_usdt = Decimal(str(self.config['min_trade_usdt']))

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

    def get_recent_change(self):
        candles = self.spot_api.list_candlesticks(currency_pair=self.symbol, interval="1m", limit=2)
        previous_close = Decimal(candles[0][2])
        current_close = Decimal(candles[1][2])
        change = (current_close - previous_close) / previous_close
        return change, current_close

    def place_market_buy(self, usdt_to_use):
        price = self.get_current_price()
        amount = (usdt_to_use / price).quantize(Decimal('0.0001'))
        trade_value = amount * price

        if trade_value < self.min_trade_usdt:
            self.logger.warning("Trade size below exchange minimum, skipping.")
            return

        buy_order = Order(
            currency_pair=self.symbol,
            side='buy',
            amount=str(amount),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(buy_order)
        self.logger.info(f"BUY: {amount} XRP at {price}")

    def place_market_sell(self):
        balance = self.get_balance('XRP')
        if balance <= Decimal('0.01'):
            self.logger.warning("No XRP to sell.")
            return

        sell_order = Order(
            currency_pair=self.symbol,
            side='sell',
            amount=str(balance.quantize(Decimal('0.0001'))),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(sell_order)
        self.logger.info(f"SELL: {balance} XRP")

    def get_current_price(self):
        ticker = self.spot_api.list_tickers(currency_pair=self.symbol)
        return Decimal(ticker[0].last)

    def run(self):
        while True:
            try:
                change, current_price = self.get_recent_change()
                self.logger.info(f"1min change: {change*100:.2f}% | Price: {current_price}")

                if change >= self.sell_threshold:
                    self.logger.info("Signal: SELL")
                    self.place_market_sell()

                elif change <= self.buy_threshold:
                    self.logger.info("Signal: BUY")
                    usdt_balance = self.get_balance('USDT')
                    if usdt_balance > (self.trade_amount + self.min_usdt_balance):
                        self.place_market_buy(self.trade_amount)
                    else:
                        self.logger.warning("Insufficient USDT balance to buy.")

                else:
                    self.logger.info("No trade signal.")

            except Exception as e:
                self.logger.error(f"Error: {e}")

            time.sleep(self.check_interval)
