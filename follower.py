import json
import os
import time
from decimal import Decimal
import gate_api
from gate_api import Order

class FollowerBot:
    def __init__(self, api_key, api_secret, logger):
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logger
        self.signal_file = "signals.json"
        self.enable_file = "follower.enabled"

        client = gate_api.ApiClient(gate_api.Configuration(key=self.api_key, secret=self.api_secret))
        self.spot_api = gate_api.SpotApi(client)

    def execute_order(self, symbol, side, usdt_amount):
        price = self.get_current_price(symbol)
        amount = (Decimal(usdt_amount) / price).quantize(Decimal('0.0001'))
        trade_value = amount * price

        order = Order(
            currency_pair=symbol,
            side=side,
            amount=str(amount),
            price=None,
            type='market',
            time_in_force='ioc'
        )
        self.spot_api.create_order(order)
        self.logger.log(symbol, "INFO", f"FOLLOWER executed {side.upper()} {amount} {symbol} at {price} (value {trade_value})")

    def get_current_price(self, symbol):
        ticker = self.spot_api.list_tickers(currency_pair=symbol)
        return Decimal(ticker[0].last)

    def run(self):
        processed_signals = set()

        while True:
            try:
                # Check dynamic toggle file
                if not os.path.exists(self.enable_file):
                    self.logger.log("FOLLOWER", "INFO", "Follower paused (waiting for follower.enabled file)")
                    time.sleep(5)
                    continue

                if os.path.exists(self.signal_file):
                    with open(self.signal_file) as f:
                        data = json.load(f)

                        signals = data if isinstance(data, list) else [data]

                        for signal in signals:
                            signal_id = signal.get("time")

                            if signal_id and signal_id not in processed_signals:
                                self.logger.log(signal["symbol"], "INFO", f"NEW SIGNAL: {signal}")

                                self.execute_order(
                                    signal["symbol"],
                                    signal["side"],
                                    Decimal('20')  # fixed 20 USDT trade amount for follower bot
                                )

                                processed_signals.add(signal_id)
                else:
                    self.logger.log("FOLLOWER", "WARNING", "No signals.json found")

            except Exception as e:
                self.logger.log("FOLLOWER", "ERROR", str(e))

            time.sleep(5)
