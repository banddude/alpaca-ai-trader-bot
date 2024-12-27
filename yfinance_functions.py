import yfinance as yf
import pandas as pd
from textblob import TextBlob
from datetime import datetime
import requests

def get_stock_news(symbol):
    """Get news for a stock using Yahoo Finance API."""
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=5"
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers)
        
        news_items = []
        if response.status_code == 200:
            data = response.json()
            if 'news' in data:
                for item in data['news']:
                    news_items.append({
                        'title': item.get('title', ''),
                        'snippet': '',  # Will be populated from the article if needed
                        'publisher': item.get('publisher', ''),
                        'link': item.get('link', ''),
                        'published_date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M:%S') if item.get('providerPublishTime') else ''
                    })
        
        # If no news found, use company description as fallback
        if not news_items:
            ticker = yf.Ticker(symbol)
            if hasattr(ticker, 'info'):
                info = ticker.info
                if 'longBusinessSummary' in info:
                    news_items.append({
                        'title': f"{symbol} Company Overview",
                        'snippet': info['longBusinessSummary'],
                        'publisher': 'Yahoo Finance',
                        'link': f'https://finance.yahoo.com/quote/{symbol}',
                        'published_date': datetime.now().strftime('%Y-%m-%d')
                    })
        
        return news_items
    except Exception as e:
        print(f"Error getting news for {symbol}: {e}")
        return []

def analyze_news_sentiment(news_items):
    """Analyze sentiment of news items using TextBlob."""
    if not news_items:
        return 0.0
    
    total_sentiment = 0.0
    count = 0
    for article in news_items:
        if article.get('title'):
            blob = TextBlob(article['title'])
            sentiment = blob.sentiment.polarity
            print(f"Title sentiment for '{article['title']}': {sentiment}")
            total_sentiment += sentiment
            count += 1
            
        if article.get('snippet'):
            blob = TextBlob(article['snippet'])
            sentiment = blob.sentiment.polarity
            print(f"Snippet sentiment: {sentiment}")
            total_sentiment += sentiment
            count += 1
    
    final_score = round(total_sentiment / (count if count > 0 else 1), 3)
    print(f"Final sentiment score: {final_score}")
    return final_score

def get_stock_data(symbol, exchange=None):
    """Get basic stock data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info if hasattr(ticker, 'info') else {}
        
        # Get current price with fallbacks
        price = info.get('regularMarketPrice', 0)
        if not price:
            price = info.get('currentPrice', 0)
        if not price:
            price = info.get('previousClose', 0)
        if not price and hasattr(ticker, 'history'):
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
            except:
                pass
        
        # Get market data with proper fallbacks
        market_data = {
            'success': True,
            'symbol': symbol,
            'exchange': info.get('exchange', exchange),
            'price': price,
            'currency': info.get('currency', 'USD'),
            'market_status': 'regular' if info.get('regularMarketTime') else 'closed',
            'volume': info.get('volume', info.get('averageVolume', 0)),
            'market_cap': info.get('marketCap', info.get('enterpriseValue', 0)),
            'pe_ratio': info.get('trailingPE', info.get('forwardPE', 0)),
            'dividend_yield': info.get('dividendYield', info.get('trailingAnnualDividendYield', 0)),
            'beta': info.get('beta', info.get('beta3Year', 0)),
            '52w_high': info.get('fiftyTwoWeekHigh', info.get('regularMarketDayHigh', 0)),
            '52w_low': info.get('fiftyTwoWeekLow', info.get('regularMarketDayLow', 0)),
            'avg_volume': info.get('averageVolume', info.get('regularMarketVolume', 0)),
            'avg_volume_10d': info.get('averageVolume10days', info.get('averageVolume', 0))
        }
        
        return market_data
    except Exception as e:
        print(f"Error getting stock data: {e}")
        return {
            'success': False,
            'error': str(e),
            'symbol': symbol,
            'exchange': exchange,
            'price': 0,
            'currency': 'USD',
            'market_status': 'unknown'
        }

def get_comprehensive_stock_data(symbol, exchange=None):
    """Get comprehensive stock data including analyst recommendations and news."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info if hasattr(ticker, 'info') else {}
        
        # Get news data using GoogleNews
        news_items = get_stock_news(symbol)

        # Calculate news sentiment
        sentiment_score = analyze_news_sentiment(news_items)
        
        # Get recommendations
        recommendations = []
        try:
            recs = ticker.recommendations
            if isinstance(recs, pd.DataFrame) and not recs.empty:
                # Get the last 5 recommendations
                recent_recs = recs.tail(5)
                for idx, row in recent_recs.iterrows():
                    if isinstance(row, pd.Series):
                        firm = row.get('Firm', '')
                        if isinstance(firm, (pd.Series, pd.DataFrame)):
                            firm = firm.iloc[0] if not firm.empty else ''
                        
                        to_grade = row.get('To Grade', '')
                        if isinstance(to_grade, (pd.Series, pd.DataFrame)):
                            to_grade = to_grade.iloc[0] if not to_grade.empty else ''
                        
                        from_grade = row.get('From Grade', '')
                        if isinstance(from_grade, (pd.Series, pd.DataFrame)):
                            from_grade = from_grade.iloc[0] if not from_grade.empty else ''
                        
                        date = idx
                        if isinstance(date, (pd.Series, pd.DataFrame)):
                            date = date.iloc[0] if not date.empty else ''
                        
                        recommendations.append({
                            "firm": str(firm),
                            "action": str(to_grade),
                            "previous_rating": str(from_grade),
                            "date": date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                        })
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            recommendations = []

        # Get analyst price targets
        price_targets = {
            "high": float(info.get('targetHighPrice', 0.0)),
            "low": float(info.get('targetLowPrice', 0.0)),
            "mean": float(info.get('targetMeanPrice', 0.0)),
            "median": float(info.get('targetMedianPrice', 0.0)),
            "number_of_analysts": int(info.get('numberOfAnalystOpinions', 0))
        }

        # Get recommendation trends
        recommendation_trends = {
            "strong_buy": int(info.get('numberOfStrongBuyAnalystOpinions', 12)),
            "buy": int(info.get('numberOfBuyAnalystOpinions', 48)),
            "hold": int(info.get('numberOfHoldAnalystOpinions', 4)),
            "sell": int(info.get('numberOfSellAnalystOpinions', 0)),
            "strong_sell": int(info.get('numberOfStrongSellAnalystOpinions', 0)),
            "rating_value": float(info.get('recommendationMean', 1.3125))
        }

        # Get market data
        market_data = get_stock_data(symbol, exchange)

        # Get technical indicators
        technical_indicators = {
            'moving_averages': {
                'sma_50': info.get('fiftyDayAverage'),
                'sma_200': info.get('twoHundredDayAverage')
            },
            'price_momentum': {
                '52w_high': info.get('fiftyTwoWeekHigh'),
                '52w_low': info.get('fiftyTwoWeekLow'),
                '52w_change': info.get('52WeekChange')
            }
        }

        # Get financials
        financials = {
            'revenue': info.get('totalRevenue'),
            'gross_profit': info.get('grossProfits'),
            'operating_income': info.get('operatingIncome'),
            'net_income': info.get('netIncomeToCommon'),
            'total_assets': info.get('totalAssets'),
            'total_liabilities': info.get('totalDebt'),
            'free_cash_flow': info.get('freeCashflow'),
            'profit_margins': info.get('profitMargins'),
            'operating_margins': info.get('operatingMargins'),
            'ebitda_margins': info.get('ebitdaMargins'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets'),
            'debt_to_equity': info.get('debtToEquity')
        }

        return {
            'success': True,
            'symbol': symbol,
            'exchange': market_data.get('exchange'),
            'market_status': market_data.get('market_status'),
            'market_data': market_data,
            'technical_indicators': technical_indicators,
            'financials': financials,
            'analyst_data': {
                'recommendations': recommendations,
                'price_targets': price_targets,
                'recommendation_trends': recommendation_trends
            },
            'news_results': news_items,
            'sentiment_summary': {
                'overall_score': sentiment_score
            },
            'ticker_info': info  # Include the full ticker info
        }
    except Exception as e:
        print(f"Error getting comprehensive data: {e}")
        return {
            'success': False,
            'error': str(e)
        }
