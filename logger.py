import os
import threading
import datetime

class LogColors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

symbol_colors = {
    "XRP": LogColors.BLUE,
    "XRP5L": LogColors.YELLOW,
    "XRP5S": LogColors.BLUE  # or different if you want
}

class LoggerController:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_symbol = None
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

    def log(self, symbol, level, message):
        with self.lock:
            # Insert separator when symbol changes
            if self.last_symbol != symbol:
                print("\n" + "-" * 80)
                self.last_symbol = symbol

            # Timestamp formatting
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} [{level}] [{symbol}] {message}"

            # Detect buy/sell log
            upper_msg = message.upper()
            if "SELL" in upper_msg:
                color = LogColors.RED
                console_entry = f"{color}{'*' * 10} SELL SIGNAL {message} {'*' * 10}{LogColors.RESET}"
            elif "BUY" in upper_msg:
                color = LogColors.GREEN
                console_entry = f"{color}{'*' * 10} BUY SIGNAL {message} {'*' * 10}{LogColors.RESET}"
            else:
                # Default color per symbol
                color = symbol_colors.get(symbol.split("_")[0], LogColors.RESET)
                console_entry = f"{color}{log_entry}{LogColors.RESET}"

            # Print to console
            print(console_entry)

            # Write raw to file (without color or decorations)
            log_file = os.path.join(self.log_dir, f"{symbol}.log")
            with open(log_file, "a") as f:
                f.write(log_entry + "\n")
