from yfinance_functions import get_comprehensive_stock_data
from log_utils.log import log_error

def extract_my_stocks_data(stock_data):
    """
    Returns an enhanced dictionary of stock data including price, quantity, P/L,
    and any open orders for the AI to consider in its decision making.
    """
    symbol = stock_data.get('symbol')
    if not symbol:
        return None
        
    # Get fresh data directly
    comprehensive_data = get_comprehensive_stock_data(symbol)
    ticker_info = comprehensive_data.get('ticker_info', {})
    
    data = {
        "price": round(stock_data.get("price", 0), 2),
        "quantity": round(stock_data.get("quantity", 0), 6),
        "average_buy_price": round(stock_data.get("average_buy_price", 0), 2),
        "current_value": round(stock_data.get("current_value", 0), 2),
        "unrealized_pl": round(stock_data.get("unrealized_pl", 0), 2),
        "unrealized_plpc": round(stock_data.get("unrealized_plpc", 0), 2),
        "technical_indicators": {
            "moving_averages": {
                "sma_50": ticker_info.get('fiftyDayAverage'),
                "sma_200": ticker_info.get('twoHundredDayAverage')
            },
            "price_momentum": {
                "52w_high": ticker_info.get('fiftyTwoWeekHigh'),
                "52w_low": ticker_info.get('fiftyTwoWeekLow'),
                "52w_change": ticker_info.get('52WeekChange')
            }
        },
        "financials": comprehensive_data.get('financials', {}),
        "market_data": comprehensive_data.get('market_data', {}),
        "analyst_ratings": {
            "price_targets": comprehensive_data.get('analyst_data', {}).get('price_targets', {}),
            "recommendation_trends": comprehensive_data.get('analyst_data', {}).get('recommendation_trends', {})
        },
        "news_data": {
            "articles": comprehensive_data.get('news_results', []),
            "sentiment": comprehensive_data.get('sentiment_summary', {})
        }
    }
    
    # Add open order information if it exists
    if stock_data.get("open_orders"):
        order = stock_data["open_orders"]
        data["open_orders"] = {
            "side": order["side"],
            "notional": order["notional"],
            "status": order["status"],
            "submitted_at": str(order["submitted_at"]),
        }
    
    return data

def extract_watchlist_data(stock_data):
    """
    For watchlist stocks, we include price and all enriched data.
    """
    symbol = stock_data.get('symbol')
    if not symbol:
        return None
        
    # Get fresh data directly
    comprehensive_data = get_comprehensive_stock_data(symbol)
    ticker_info = comprehensive_data.get('ticker_info', {})
    
    return {
        "price": round(stock_data.get("price", 0), 2),
        "quantity": 0,
        "average_buy_price": 0,
        "current_value": 0,
        "unrealized_pl": 0,
        "unrealized_plpc": 0,
        "technical_indicators": {
            "moving_averages": {
                "sma_50": ticker_info.get('fiftyDayAverage'),
                "sma_200": ticker_info.get('twoHundredDayAverage')
            },
            "price_momentum": {
                "52w_high": ticker_info.get('fiftyTwoWeekHigh'),
                "52w_low": ticker_info.get('fiftyTwoWeekLow'),
                "52w_change": ticker_info.get('52WeekChange')
            }
        },
        "financials": comprehensive_data.get('financials', {}),
        "market_data": comprehensive_data.get('market_data', {}),
        "analyst_ratings": {
            "price_targets": comprehensive_data.get('analyst_data', {}).get('price_targets', {}),
            "recommendation_trends": comprehensive_data.get('analyst_data', {}).get('recommendation_trends', {})
        },
        "news_data": {
            "articles": comprehensive_data.get('news_results', []),
            "sentiment": comprehensive_data.get('sentiment_summary', {})
        }
    }

def get_watchlist_data():
    """Get watchlist data."""
    try:
        from config import WATCHLIST
        watchlist_data = {}
        
        for symbol in WATCHLIST:
            print(f"\nEnriching watchlist data for {symbol}...")
            
            # Get fresh data directly
            comprehensive_data = get_comprehensive_stock_data(symbol)
            ticker_info = comprehensive_data.get('ticker_info', {})
            
            if comprehensive_data.get('success'):
                stock_data = {
                    'symbol': symbol,
                    'exchange': comprehensive_data.get('exchange'),
                    'price': comprehensive_data.get('market_data', {}).get('price', 0),
                    'market_status': comprehensive_data.get('market_status', 'unknown'),
                    'technical_indicators': {
                        "moving_averages": {
                            "sma_50": ticker_info.get('fiftyDayAverage'),
                            "sma_200": ticker_info.get('twoHundredDayAverage')
                        },
                        "price_momentum": {
                            "52w_high": ticker_info.get('fiftyTwoWeekHigh'),
                            "52w_low": ticker_info.get('fiftyTwoWeekLow'),
                            "52w_change": ticker_info.get('52WeekChange')
                        }
                    },
                    'financials': comprehensive_data.get('financials', {}),
                    'market_data': comprehensive_data.get('market_data', {}),
                    'analyst_ratings': {
                        'price_targets': comprehensive_data.get('analyst_data', {}).get('price_targets', {}),
                        'recommendation_trends': comprehensive_data.get('analyst_data', {}).get('recommendation_trends', {})
                    }
                }
                
                watchlist_data[symbol] = stock_data
            else:
                print(f"Failed to get data for {symbol}: {comprehensive_data.get('error')}")
        
        return watchlist_data
    except Exception as e:
        log_error(f"Error getting watchlist data: {e}")
        return {}

