# XRP Grid Trading Bot V3.0 (Capital Reuse Edition)

This is your fully automated XRP grid trading bot for Gate.io — designed for long-term trading, capital reuse, crash recovery, and smart exposure control.

## ✨ Key Features

- 🤖 Fully automated XRP trading
- 📈 Configurable profit targets (default: 5%)
- 💰 Dynamic trade sizing based on available balance
- 🛡️ Maximum exposure control
- 🔄 Automatic profit reinvestment
- 💾 Crash-safe with SQLite order tracking
- 📊 Comprehensive logging system

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or later
- Gate.io account with API access

### Required API Permissions

| Permission | Status | Notes |
|------------|--------|-------|
| Read | Required ✅ | For market data access |
| Spot Trading | Required ✅ | For executing trades |
| Withdrawals | Forbidden ❌ | Security measure |

### Installation Steps

1. **Set up your environment**

```bash
# Clone the repository
git clone https://github.com/yourusername/xrp-bot.git
cd xrp-bot

# Create and activate virtual environment
python3 -m venv gridbot-env
source gridbot-env/bin/activate  # On Windows use: gridbot-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure your bot**

Required files:
- `config.yaml` - Bot configuration and API keys
- `database.py` - Order tracking system
- `logger.py` - Logging configuration
- `trader.py` - Core trading logic
- `main.py` - Bot entry point
- `requirements.txt` - Python dependencies

3. **Launch the bot**

```bash
python main.py
```

## ⚙️ Configuration

Create a `config.yaml` file with your settings:

```yaml
api:
  key: "your_gate_io_api_key"
  secret: "your_gate_io_api_secret"

trading:
  profit_margin: 5.0  # Percentage
  max_exposure: 1000  # Maximum USDT exposure
  min_trade: 10      # Minimum trade size in USDT
```

## 📝 Logging

The bot maintains detailed logs in:
- Console output for real-time monitoring
- `bot.log` file for historical reference

## ⚠️ Risk Disclaimer

Trading cryptocurrencies involves substantial risk. This bot is provided as-is with no guarantees. Always start with small amounts and monitor the bot's performance carefully.