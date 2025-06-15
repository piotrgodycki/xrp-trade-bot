import os
import threading
import datetime

class LogColors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

symbol_colors = {
    "XRP": LogColors.GREEN,
    "XRP5L": LogColors.BLUE,
    "XRP5S": LogColors.RED
}

class LoggerController:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_symbol = None
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

    def log(self, symbol, level, message):
        with self.lock:
            # Detect symbol change
            if self.last_symbol != symbol:
                print("-" * 80)
                self.last_symbol = symbol

            # Get color
            color = symbol_colors.get(symbol.split("_")[0], LogColors.RESET)

            # Format message
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} [{level}] [{symbol}] {message}"

            # Print to console (with color)
            print(f"{color}{log_entry}{LogColors.RESET}")

            # Write to symbol file
            with open(f"{self.log_dir}/{symbol}.log", "a") as f:
                f.write(log_entry + "\n")
