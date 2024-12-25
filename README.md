# AI-Powered Trading Bot

## ⚡ TL;DR
This trading bot combines the power of OpenAI's intelligence with Alpaca's trading capabilities and yfinance's market data. Once configured with your API keys, the bot can run in three modes:
- **Auto Mode**: Automatically analyzes your portfolio and watchlist stocks, makes trading decisions, and executes them
- **Manual Mode**: Same analysis but asks for your confirmation before each trade
- **Demo Mode**: Simulates trades without actually executing them

The bot uses yfinance to fetch real-time market data and calculate moving averages, OpenAI to make intelligent trading decisions, and Alpaca's API to execute trades.

## 🌟 Features
- **AI-Powered Trading**: Uses OpenAI's GPT models to analyze market data and make trading decisions
- **Real-Time Market Data**: Fetches current prices and calculates technical indicators using yfinance
- **Portfolio Management**: Integrates with Alpaca to manage your portfolio and execute trades
- **Multiple Trading Modes**: Auto, Manual, and Demo modes for different levels of automation
- **Customizable Parameters**: Set trading limits, portfolio size, and other trading conditions
- **Trading Exceptions**: Exclude specific stocks from trading
- **Pattern Day Trading Protection**: Optional PDT rule compliance checking
- **Market Hours Awareness**: Operates only during market hours (configurable)
- **Detailed Logging**: Tracks all bot activities and trading history

## 🔧 How It Works
1. **Market Data Collection**:
   - Fetches real-time stock prices from yfinance
   - Calculates 50-day and 200-day moving averages
   - Retrieves portfolio positions from Alpaca

2. **Portfolio Analysis**:
   - Monitors your existing Alpaca portfolio positions
   - Tracks stocks from your configured watchlists
   - Analyzes technical indicators and price movements

3. **AI Decision Making**:
   - Sends market data to OpenAI
   - Receives trading decisions (buy, sell, or hold)
   - Includes quantity recommendations for each trade

4. **Trade Execution**:
   - Executes trades through Alpaca's API
   - Handles both paper trading and live trading
   - Supports fractional shares

## 📦 Installation

1. Clone the repository:
```sh
git clone <repository-url>
cd ai-trading-bot
```

2. Install required packages:
```sh
pip install alpaca-trade-api openai yfinance pandas pytz
```

## ⚙️ Configuration

1. Copy the example config:
```sh
cp config.py.example config.py
```

2. Configure your API keys in `config.py`:
```python
# OpenAI API Key
OPENAI_API_KEY = "your-openai-key"

# Alpaca API Keys
ALPACA_API_KEY = "your-alpaca-key"
ALPACA_SECRET_KEY = "your-alpaca-secret"

# Trading Configuration
PAPER_TRADING = True  # Set to False for live trading
MODE = "demo"         # "demo", "manual", or "auto"
```

3. Configure your watchlists in `watchlist.json`:
```json
{
  "Primary": [
    { "symbol": "AAPL" },
    { "symbol": "MSFT" }
  ],
  "AIStocks": [
    { "symbol": "NVDA" },
    { "symbol": "AI" }
  ]
}
```

## 🚀 Usage

Run the bot:
```sh
python main.py
```

The bot will:
1. Connect to your Alpaca account
2. Start monitoring your portfolio and watchlist
3. Use yfinance to gather market data
4. Make trading decisions using OpenAI
5. Execute trades according to your chosen mode

## ⚠️ Important Notes

- **Paper Trading**: Always test with paper trading first
- **API Keys**: Keep your API keys secure and never share them
- **Market Hours**: Bot operates during market hours by default
- **Trading Limits**: Configure appropriate limits to manage risk
- **Costs**: Be aware of OpenAI API usage costs and trading fees

## 📊 Trading Strategy

The bot's strategy combines:
1. Technical Analysis (via yfinance):
   - Moving averages (50-day and 200-day)
   - Price momentum and trends

2. AI Analysis (via OpenAI):
   - Pattern recognition
   - Market sentiment analysis
   - Risk management

3. Execution (via Alpaca):
   - Market orders
   - Position sizing
   - Portfolio balancing

## ⚠️ Disclaimer

This bot is for educational purposes only. Trading stocks involves risk, and you should only trade with money you can afford to lose. The authors are not responsible for any financial losses incurred while using this bot.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues and pull requests.

## 📧 Contact

For questions or feedback, please open an issue in the repository.
