import yaml
import threading
from trader import SymbolTrader
from follower import FollowerBot
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

    # Start grid bots
    for symbol_cfg in config['symbols']:
        bot = SymbolTrader(api_key, api_secret, symbol_cfg, shared_cfg, logger_controller)
        thread = threading.Thread(target=bot.run)
        thread.start()
        bots.append(thread)

    # Start follower bot if enabled in config
    if config.get("enable_follower", False):
        follower_bot = FollowerBot(api_key, api_secret, logger_controller)
        thread = threading.Thread(target=follower_bot.run)
        thread.start()
        bots.append(thread)

    for thread in bots:
        thread.join()
