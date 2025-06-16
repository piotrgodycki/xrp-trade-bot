import gate_api
from gate_api import Order
from decimal import Decimal
import time

class SymbolTrader:
    def __init__(self, api_key, api_secret, symbol_cfg, shared_cfg, logger):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol_cfg['symbol']
        self.trade_percent = Decimal(str(symbol_cfg['trade_percent']))
        self.atr_period = int(symbol_cfg.get('atr_period', 10))
        self.atr_multiplier = Decimal(str(symbol_cfg.get('atr_multiplier', 0.7)))
        self.ma_period = int(symbol_cfg.get('ma_period', 20))
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

    def get_recent_candles(self):
        candles = self.spot_api.list_candlesticks(currency_pair=self.symbol, interval="1m", limit=self.atr_period + 1)
        candles = [(Decimal(c[2]), Decimal(c[3])) for c in candles]  # high, low
        return candles

    def calculate_atr(self):
        candles = self.get_recent_candles()
        tr_values = [h - l for h, l in candles]
        atr = sum(tr_values) / len(tr_values)
        return atr

    def calculate_ma(self):
        prices = self.spot_api.list_candlesticks(currency_pair=self.symbol, interval="1m", limit=self.ma_period)
        closes = [Decimal(c[2]) for c in prices]
        return sum(closes) / len(closes)

    def get_current_price(self):
        ticker = self.spot_api.list_tickers(currency_pair=self.symbol)
        return Decimal(ticker[0].last)

    def place_market_buy(self):
        usdt_balance = self.get_balance('USDT')
        available_for_trade = usdt_balance - self.min_usdt_balance
        if available_for_trade <= 0:
            self.logger.log(self.symbol, "WARNING", "No USDT available")
            return

        dynamic_usdt_to_use = (available_for_trade * self.trade_percent / Decimal('100')).quantize(Decimal('0.01'))

        if dynamic_usdt_to_use < self.min_trade_usdt:
            self.logger.log(self.symbol, "WARNING", f"BUY skipped — below min trade value: {dynamic_usdt_to_use}")
            return

        price = self.get_current_price()
        amount = (dynamic_usdt_to_use / price).quantize(Decimal('0.0001'))
        trade_value = amount * price

        # ✅ Log full BUY signal calculation
        # self.logger.log(self.symbol, "INFO", f"******************** BUY SIGNAL ********************")
        self.logger.log(self.symbol, "INFO", f"BUY AMOUNT SIGNAL — Buying {amount} {self.symbol.split('_')[0]} worth {trade_value} USDT")

        order = Order(
            currency_pair=self.symbol,
            side='buy',
            amount=str(amount),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(order)
        self.logger.log(self.symbol, "INFO", f"BUY EXECUTED {amount} at {price}")

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
        self.logger.log(self.symbol, "INFO", f"******************** SELL SIGNAL ********************")
        self.logger.log(self.symbol, "INFO", f"SELL EXECUTED {balance} {token}")

    def run(self):
        while True:
            try:
                price = self.get_current_price()
                atr = self.calculate_atr()
                ma = self.calculate_ma()

                buy_threshold = -(atr * self.atr_multiplier)
                sell_threshold = (atr * self.atr_multiplier)

                change = (price - ma) / ma

                self.logger.log(self.symbol, "INFO", f"Price: {price}, MA: {ma}, ATR: {atr}, ΔMA%: {change*100:.2f}%")

                token = self.symbol.split("_")[0]
                balance = self.get_balance(token)

                if change >= sell_threshold and balance > Decimal('0.01'):
                    self.place_market_sell()

                elif change <= buy_threshold:
                    self.place_market_buy()

                else:
                    self.logger.log(self.symbol, "INFO", "No signal")

            except Exception as e:
                self.logger.log(self.symbol, "ERROR", f"Error: {e}")

            time.sleep(self.check_interval)
