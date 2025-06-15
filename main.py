import yaml
import threading
from trader import SymbolTrader
from logger import LoggerController

if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    api_key = config['api_key']
    api_secret = config['api_secret']
    shared_cfg = {
        "check_interval": config['check_interval'],
        "min_usdt_balance": config['min_usdt_balance'],
        "min_trade_usdt": config['min_trade_usdt'],
    }

    logger_controller = LoggerController()

    bots = []
    for symbol_cfg in config['symbols']:
        bot = SymbolTrader(api_key, api_secret, symbol_cfg, shared_cfg, logger_controller)
        thread = threading.Thread(target=bot.run)
        thread.start()
        bots.append(thread)

    for thread in bots:
        thread.join()
