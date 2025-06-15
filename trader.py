import gate_api
from gate_api import Order
from decimal import Decimal
import time

class SymbolTrader:
    def __init__(self, api_key, api_secret, symbol_cfg, shared_cfg, logger):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol_cfg['symbol']
        self.trade_amount = Decimal(str(symbol_cfg['trade_amount']))
        self.buy_threshold = Decimal(str(symbol_cfg['buy_threshold']))
        self.sell_threshold = Decimal(str(symbol_cfg['sell_threshold']))
        self.check_interval = shared_cfg['check_interval']
        self.min_usdt_balance = Decimal(str(shared_cfg['min_usdt_balance']))
        self.min_trade_usdt = Decimal(str(shared_cfg['min_trade_usdt']))
        self.logger = logger

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
        prev_close = Decimal(candles[0][2])
        curr_close = Decimal(candles[1][2])
        change = (curr_close - prev_close) / prev_close
        return change, curr_close

    def place_market_buy(self, usdt_to_use):
        price = self.get_current_price()
        amount = (usdt_to_use / price).quantize(Decimal('0.0001'))
        trade_value = amount * price

        if trade_value < self.min_trade_usdt:
            self.logger.log(self.symbol, "WARNING", "BUY too small")
            return

        order = Order(
            currency_pair=self.symbol,
            side='buy',
            amount=str(amount),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(order)
        self.logger.log(self.symbol, "INFO", f"BUY {amount} at {price}")

    def place_market_sell(self):
        token = self.symbol.split("_")[0]
        balance = self.get_balance(token)
        if balance <= Decimal('0.01'):
            self.logger.log(self.symbol, "WARNING", "Nothing to sell")
            return

        order = Order(
            currency_pair=self.symbol,
            side='sell',
            amount=str(balance.quantize(Decimal('0.0001'))),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(order)
        self.logger.log(self.symbol, "INFO", f"SELL {balance}")

    def get_current_price(self):
        ticker = self.spot_api.list_tickers(currency_pair=self.symbol)
        return Decimal(ticker[0].last)

    def run(self):
        while True:
            try:
                change, current_price = self.get_recent_change()
                self.logger.log(self.symbol, "INFO", f"Δ1m: {change*100:.2f}% | Price: {current_price}")

                if change >= self.sell_threshold:
                    self.logger.log(self.symbol, "INFO", "SELL SIGNAL")
                    self.place_market_sell()

                elif change <= self.buy_threshold:
                    usdt_balance = self.get_balance('USDT')
                    if usdt_balance > (self.trade_amount + self.min_usdt_balance):
                        self.logger.log(self.symbol, "INFO", "BUY SIGNAL")
                        self.place_market_buy(self.trade_amount)
                    else:
                        self.logger.log(self.symbol, "WARNING", "Not enough USDT")
                else:
                    self.logger.log(self.symbol, "INFO", "No signal")

            except Exception as e:
                self.logger.log(self.symbol, "ERROR", f"Error: {e}")

            time.sleep(self.check_interval)
