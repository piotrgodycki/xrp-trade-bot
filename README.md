# XRP Grid Trading Bot V3.0 (Capital Reuse Edition)

This is your fully automated XRP grid trading bot for Gate.io — designed for long-term trading, capital reuse, crash recovery, and smart exposure control.

---

## ✅ Features

- Fully automated XRP trading
- Buys XRP and sells at 5% profit (configurable)
- Dynamically adjusts trade size based on available balance
- Maximum exposure control
- Capital reuse: reinvests profits automatically
- Crash-safe with persistent order tracking via SQLite
- Detailed logs to both file and console

---

## 🚀 Installation Instructions

### 1️⃣ Prerequisites

- Install Python 3.10 or later
- Create your Gate.io API Key

**API permissions:**

- ✅ Read permissions
- ✅ Spot trading permissions
- ❌ DO NOT enable withdrawal permissions (for safety)

---

### 2️⃣ Clone or copy your files

You should have the following files:

- `config.yaml`  
- `database.py`  
- `logger.py`  
- `trader.py` *(already in your canvas)*  
- `main.py`  
- `requirements.txt`

---

### 3️⃣ Install required Python libraries

```bash
pip install -r requirements.txt
