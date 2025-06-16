import os
import threading
import datetime
import sys

class LogColors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[95m"
    GRAY = "\033[90m"

symbol_colors = {
    "XRP": LogColors.BLUE,
    "XRP5L": LogColors.YELLOW,
    "XRP5S": LogColors.CYAN,
    "ZBAI": LogColors.GRAY,
    "CALCIFY": LogColors.PURPLE,
}

class LoggerController:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_symbol = None
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.color_enabled = self.supports_color()

    def supports_color(self):
        return sys.stdout.isatty()

    def log(self, symbol, level, message):
        with self.lock:
            if self.last_symbol != symbol:
                print("\n" + "-" * 80, flush=True)
                self.last_symbol = symbol

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} [{level}] [{symbol}] {message}"

            upper_msg = message.upper()

            # Priority BUY / SELL banners
            if "SELL" in upper_msg:
                color = LogColors.RED
                decorated_msg = f"{color}{'*' * 10} SELL SIGNAL {message} {'*' * 10}{LogColors.RESET}"
            elif "BUY" in upper_msg:
                color = LogColors.GREEN
                decorated_msg = f"{color}{'*' * 10} BUY SIGNAL {message} {'*' * 10}{LogColors.RESET}"
            elif level == "WARNING":
                color = LogColors.ORANGE
                decorated_msg = f"{color}{log_entry}{LogColors.RESET}"
            elif level == "ERROR":
                color = LogColors.RED
                decorated_msg = f"{color}{log_entry}{LogColors.RESET}"
            else:
                color = symbol_colors.get(symbol.split("_")[0], LogColors.RESET)
                decorated_msg = f"{color}{log_entry}{LogColors.RESET}"

            if self.color_enabled:
                print(decorated_msg, flush=True)
            else:
                print(log_entry, flush=True)

            log_file = os.path.join(self.log_dir, f"{symbol}.log")
            with open(log_file, "a") as f:
                f.write(log_entry + "\n")
