from datetime import datetime, timedelta
import sqlite3
import os

# Global variables for database connection
conn = None
cursor = None

def init_db():
    """Initialize the database with the correct schema."""
    global conn, cursor
    
    # Create a new database connection
    conn = sqlite3.connect('trading_logs.db')
    cursor = conn.cursor()

    # Drop the existing table if it exists
    cursor.execute('DROP TABLE IF EXISTS trading_logs')

    # Create the table with the new schema
    cursor.execute('''
    CREATE TABLE trading_logs (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        decision TEXT,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn, cursor

# Initialize database connection
def initialize_connection():
    global conn, cursor
    try:
        conn = sqlite3.connect('trading_logs.db')
        cursor = conn.cursor()
        # Try to get table info
        cursor.execute("PRAGMA table_info(trading_logs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Check if we have the correct schema
        if 'amount' not in columns:
            conn.close()
            # Backup the old database if it exists
            if os.path.exists('trading_logs.db'):
                os.rename('trading_logs.db', f'trading_logs_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            conn, cursor = init_db()
    except sqlite3.Error:
        conn, cursor = init_db()

def log_trade_to_db(symbol, decision, amount):
    """
    Log a trade to the database with amount in USD.
    
    Args:
        symbol (str): The stock symbol
        decision (str): The trade decision (buy/sell)
        amount (float): The dollar amount of the trade
    """
    global conn, cursor
    try:
        cursor.execute('''
        INSERT INTO trading_logs (symbol, decision, amount)
        VALUES (?, ?, ?)
        ''', (symbol, decision, float(amount)))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # If we get an error about missing column, try to reinitialize the database
        if "no column named amount" in str(e):
            conn, cursor = init_db()
            # Try the insert again
            cursor.execute('''
            INSERT INTO trading_logs (symbol, decision, amount)
            VALUES (?, ?, ?)
            ''', (symbol, decision, float(amount)))
            conn.commit()

def get_stocks_from_db_under_day_trade_limit():
    """
    Get list of stocks that have been traded more than 3 times in the past 5 trading days.
    """
    global conn, cursor
    now = datetime.now()
    five_days_ago = now - timedelta(days=7)  # Using 7 calendar days to cover 5 trading days
    try:
        cursor.execute('''
        SELECT symbol, COUNT(*) as day_trade_count
        FROM trading_logs
        WHERE timestamp > ?
        AND strftime('%w', timestamp) NOT IN ('0', '6')  # Exclude weekends
        GROUP BY symbol
        HAVING day_trade_count >= 3
        ''', (five_days_ago,))
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []

# Initialize the database connection when the module is imported
initialize_connection()

# Ensure the connection is closed when the program exits
def cleanup():
    global conn
    if conn:
        conn.close()

import atexit
atexit.register(cleanup)
