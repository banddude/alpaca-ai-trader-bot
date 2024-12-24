import json
from datetime import datetime
from pytz import timezone
import yfinance as yf
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from config import (
    PAPER_TRADING, ALPACA_API_KEY, ALPACA_SECRET_KEY, WATCHLIST_FILE,
    MIN_BUYING_AMOUNT_USD, MAX_BUYING_AMOUNT_USD,
    MIN_SELLING_AMOUNT_USD, MAX_SELLING_AMOUNT_USD
)
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")


# Initialize the Alpaca Trading Client
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_TRADING)

###############################################################################
# PRICE + MOVING AVERAGES
###############################################################################
def get_current_price(symbol):
    """
    Simple helper that grabs the latest close from yfinance.
    """
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])

def calculate_moving_averages(symbol, short_window=50, long_window=200):
    """
    Get short and long moving averages from yfinance.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1y")
    if hist.empty:
        return None, None
    prices = hist["Close"]
    short_mavg = prices.rolling(window=short_window).mean().iloc[-1]
    long_mavg = prices.rolling(window=long_window).mean().iloc[-1]
    return round(short_mavg, 2), round(long_mavg, 2)

###############################################################################
# MARKET + ACCOUNT INFO
###############################################################################
def is_market_open():
    """
    Basic check if it's between 9:30 AM and 4:00 PM Eastern on a weekday.
    """
    eastern = timezone("US/Eastern")
    now = datetime.now(eastern)
    if now.weekday() >= 5:  # Market closed on weekends
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close

def get_buying_power():
    """
    Return the account's buying power, rounded to two decimals.
    """
    account_info = get_account_info()
    return account_info["buying_power"]

###############################################################################
# PORTFOLIO + WATCHLIST
###############################################################################
def get_portfolio_stocks():
    """
    Get all positions from Alpaca and include current prices from yfinance.
    Also includes current open orders for each position.
    """
    positions = trading_client.get_all_positions()
    portfolio = {}
    
    # Get current open orders
    open_orders = get_open_orders()
    
    for position in positions:
        symbol = position.symbol
        current_price = get_current_price(symbol)
        
        # Calculate total position value
        quantity = float(position.qty)
        current_value = quantity * (current_price or float(position.current_price))
        
        portfolio[symbol] = {
            "price": round(current_price, 2) if current_price else 0,
            "quantity": round(quantity, 6),
            "average_buy_price": round(float(position.avg_entry_price), 2),
            "current_value": round(current_value, 2),
            "unrealized_pl": round(float(position.unrealized_pl), 2),
            "unrealized_plpc": round(float(position.unrealized_plpc) * 100, 2),  # Convert to percentage
            "open_orders": open_orders.get(symbol, None)  # Add any open orders for this symbol
        }
    
    # Also include any open orders for symbols not in portfolio
    for symbol, order in open_orders.items():
        if symbol not in portfolio:
            current_price = get_current_price(symbol)
            portfolio[symbol] = {
                "price": round(current_price, 2) if current_price else 0,
                "quantity": 0,
                "average_buy_price": 0,
                "current_value": 0,
                "unrealized_pl": 0,
                "unrealized_plpc": 0,
                "open_orders": order
            }
    
    return portfolio

def get_watchlist_stocks(name):
    """
    Loads watchlist data from local JSON, which might contain multiple watchlists.
    """
    with open(WATCHLIST_FILE, "r") as file:
        watchlists = json.load(file)
    if name not in watchlists:
        raise Exception(f"Watchlist '{name}' not found in {WATCHLIST_FILE}")
    
    # Add current prices to watchlist stocks
    watchlist_stocks = watchlists[name]
    for stock in watchlist_stocks:
        current_price = get_current_price(stock['symbol'])
        stock['price'] = round(current_price, 2) if current_price else 0
    
    return watchlist_stocks

###############################################################################
# EXTRACT + ENRICH HELPERS
###############################################################################
def extract_my_stocks_data(stock_data):
    """
    Returns an enhanced dictionary of stock data including price, quantity, P/L,
    and any open orders for the AI to consider in its decision making.
    """
    data = {
        "price": round(stock_data.get("price", 0), 2),
        "quantity": round(stock_data.get("quantity", 0), 6),
        "average_buy_price": round(stock_data.get("average_buy_price", 0), 2),
        "current_value": round(stock_data.get("current_value", 0), 2),
        "unrealized_pl": round(stock_data.get("unrealized_pl", 0), 2),
        "unrealized_plpc": round(stock_data.get("unrealized_plpc", 0), 2),
    }
    
    # Add open order information if it exists
    if stock_data.get("open_orders"):
        order = stock_data["open_orders"]
        data["open_orders"] = {
            "side": order["side"],
            "notional": order["notional"],
            "status": order["status"],
            "submitted_at": str(order["submitted_at"]),  # Convert datetime to string for JSON
        }
    
    return data

def extract_watchlist_data(stock_data):
    """
    For watchlist stocks, we store the price if provided.
    """
    return {
        "price": round(stock_data.get("price", 0), 2),
    }

def enrich_with_moving_averages(stock_data, symbol):
    """
    Adds 50- and 200-day moving averages using yfinance data.
    """
    short_mavg, long_mavg = calculate_moving_averages(symbol)
    if short_mavg:
        stock_data["50_day_mavg_price"] = short_mavg
    if long_mavg:
        stock_data["200_day_mavg_price"] = long_mavg
    return stock_data

def get_ratings(symbol):
    """
    Placeholder for analyst ratings - returns empty structure.
    """
    return {
        "ratings": [],
        "summary": {
            "num_buy_ratings": 0,
            "num_hold_ratings": 0,
            "num_sell_ratings": 0
        }
    }

def enrich_with_analyst_ratings(stock_data, symbol):
    """
    Adds placeholder analyst ratings data.
    """
    ratings = get_ratings(symbol)
    
    if 'summary' in ratings:
        summary = ratings['summary']
        total_ratings = (
            summary['num_buy_ratings']
            + summary['num_hold_ratings']
            + summary['num_sell_ratings']
        )
        if total_ratings > 0:
            buy_percent = (summary['num_buy_ratings'] / total_ratings) * 100
            sell_percent = (summary['num_sell_ratings'] / total_ratings) * 100
            hold_percent = (summary['num_hold_ratings'] / total_ratings) * 100
            stock_data["robinhood_analyst_summary_distribution"] = (
                f"sell: {sell_percent:.0f}%, buy: {buy_percent:.0f}%, hold: {hold_percent:.0f}%"
            )
    return stock_data

###############################################################################
# ORDERING
###############################################################################
def buy_stock(symbol, amount):
    """
    Places a market buy order via Alpaca using dollar amount (notional).
    Respects MIN_BUYING_AMOUNT_USD and MAX_BUYING_AMOUNT_USD settings.
    """
    # Apply min/max limits if configured
    if MIN_BUYING_AMOUNT_USD is not False:
        amount = max(amount, MIN_BUYING_AMOUNT_USD)
    if MAX_BUYING_AMOUNT_USD is not False:
        amount = min(amount, MAX_BUYING_AMOUNT_USD)
    
    # Round to 2 decimal places for dollar amounts
    amount = round(amount, 2)
    
    order_data = MarketOrderRequest(
        symbol=symbol,
        notional=amount,  # Use notional for dollar-based orders
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    
    order_response = trading_client.submit_order(order_data=order_data)
    
    return {
        "id": order_response.id,
        "quantity": float(order_response.qty) if order_response.qty else amount/float(order_response.filled_avg_price or get_current_price(symbol)),
        "price": float(order_response.filled_avg_price) if order_response.filled_avg_price else None,
    }

def sell_stock(symbol, amount):
    """
    Places a market sell order via Alpaca using dollar amount (notional).
    Respects MIN_SELLING_AMOUNT_USD and MAX_SELLING_AMOUNT_USD settings.
    Checks available quantity first and adjusts amount if necessary.
    """
    try:
        # Get current position
        position = None
        try:
            position = trading_client.get_open_position(symbol)
        except Exception as e:
            if "position does not exist" in str(e).lower():
                return {"error": f"No position exists for {symbol}"}
            raise e

        # Get current price
        current_price = float(position.current_price)
        
        # Get open orders for this symbol
        open_orders = get_open_orders()
        pending_sell_value = 0
        if symbol in open_orders and open_orders[symbol]["side"] == "sell":
            pending_sell_value = open_orders[symbol]["notional"]

        # Calculate available quantity and value
        total_shares = float(position.qty)
        total_value = total_shares * current_price
        pending_value = pending_sell_value
        available_value = total_value - pending_value

        # If requested amount is more than available, adjust it
        if amount > available_value:
            amount = available_value
            if amount < MIN_SELLING_AMOUNT_USD:
                return {"error": f"Available position value (${amount:.2f}) is below minimum selling amount"}

        # Apply min/max limits if configured
        if MIN_SELLING_AMOUNT_USD is not False:
            amount = max(amount, MIN_SELLING_AMOUNT_USD)
        if MAX_SELLING_AMOUNT_USD is not False:
            amount = min(amount, MAX_SELLING_AMOUNT_USD)
        
        # Round to 2 decimal places for dollar amounts
        amount = round(amount, 2)
        
        # If amount is too small, skip the trade
        if amount <= 0:
            return {"error": "Sell amount too small"}
        
        # Calculate shares to sell based on dollar amount
        shares_to_sell = amount / current_price
        if shares_to_sell > total_shares:
            return {"error": f"Insufficient shares available. Have: {total_shares:.6f}, Need: {shares_to_sell:.6f}"}
        
        order_data = MarketOrderRequest(
            symbol=symbol,
            notional=amount,  # Use notional for dollar-based orders
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        order_response = trading_client.submit_order(order_data=order_data)
        
        return {
            "id": order_response.id,
            "quantity": float(order_response.qty) if order_response.qty else shares_to_sell,
            "price": float(order_response.filled_avg_price) if order_response.filled_avg_price else current_price,
        }
    except Exception as e:
        return {"error": str(e)}

###############################################################################
# ORDER RESPONSE EXTRACTION
###############################################################################
def extract_sell_response_data(sell_resp):
    """
    Extracts relevant data from a sell order response.
    """
    return {
        "quantity": sell_resp.get("quantity"),
        "price": sell_resp.get("price"),
    }

def extract_buy_response_data(buy_resp):
    """
    Extracts relevant data from a buy order response.
    """
    return {
        "quantity": buy_resp.get("quantity"),
        "price": buy_resp.get("price"),
    }

def get_open_orders():
    """
    Get all open orders with their current status.
    Returns a dictionary of orders by symbol with their details.
    """
    try:
        # Get all open orders
        orders = trading_client.get_orders(filter=GetOrdersRequest(status=QueryOrderStatus.OPEN))
        orders_dict = {}
        for order in orders:
            # Calculate filled notional from filled qty and filled avg price
            filled_notional = 0
            if order.filled_qty and order.filled_avg_price:
                filled_notional = float(order.filled_qty) * float(order.filled_avg_price)

            orders_dict[order.symbol] = {
                "id": order.id,
                "side": order.side.value,
                "type": order.type,
                "notional": float(order.notional) if order.notional else 0,
                "filled_notional": filled_notional,
                "status": order.status.value,
                "submitted_at": order.submitted_at,
                "filled_at": order.filled_at,
                "expired_at": order.expired_at,
                "canceled_at": order.canceled_at,
                "failed_at": order.failed_at,
                "replaced_at": order.replaced_at,
                "replaced_by": order.replaced_by,
            }
        return orders_dict
    except Exception as e:
        print(f"Error getting open orders: {e}")
        return {}

def get_account_info():
    """
    Get detailed account information including buying power, portfolio value,
    and current open orders.
    """
    try:
        account = trading_client.get_account()
        open_orders = get_open_orders()
        
        return {
            "buying_power": round(float(account.buying_power), 2),
            "portfolio_value": round(float(account.portfolio_value), 2),
            "cash": round(float(account.cash), 2),
            "open_orders_count": len(open_orders),
            "open_orders": open_orders,
            "daytrade_count": int(account.daytrade_count),
            "last_equity": round(float(account.last_equity), 2),
            "initial_margin": round(float(account.initial_margin), 2),
            "maintenance_margin": round(float(account.maintenance_margin), 2),
            "pattern_day_trader": account.pattern_day_trader,
        }
    except Exception as e:
        print(f"Error getting account info: {e}")
        return {
            "buying_power": 0,
            "portfolio_value": 0,
            "cash": 0,
            "open_orders_count": 0,
            "open_orders": {},
            "daytrade_count": 0,
            "last_equity": 0,
            "initial_margin": 0,
            "maintenance_margin": 0,
            "pattern_day_trader": False,
        }
