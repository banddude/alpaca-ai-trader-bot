from datetime import datetime
import sqlite3
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'trading_logs.db')

# Database settings
BACKUP_ENABLED = True
BACKUP_INTERVAL_HOURS = 24

def init_db():
    """Initialize the database with the correct schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trading_logs (
        id INTEGER PRIMARY KEY,
        symbol TEXT,
        decision TEXT,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn, cursor

def backup_db():
    """Create a backup of the database if enabled."""
    if not BACKUP_ENABLED:
        return
        
    try:
        # Check if we need to create a backup
        backup_path = f"{DB_PATH}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Only create backup if original exists
        if os.path.exists(DB_PATH):
            import shutil
            shutil.copy2(DB_PATH, backup_path)
            
            # Clean up old backups
            backup_files = [f for f in os.listdir(SCRIPT_DIR) if f.startswith(os.path.basename(DB_PATH) + '_backup_')]
            backup_files.sort(reverse=True)
            
            # Keep only the most recent backups based on interval
            current_time = datetime.now()
            for backup_file in backup_files[1:]:  # Skip the most recent backup
                backup_time_str = backup_file.split('_')[-2] + '_' + backup_file.split('_')[-1]
                backup_time = datetime.strptime(backup_time_str, '%Y%m%d_%H%M%S')
                
                # If backup is older than interval, delete it
                if (current_time - backup_time).total_seconds() > BACKUP_INTERVAL_HOURS * 3600:
                    os.remove(os.path.join(SCRIPT_DIR, backup_file))
                    
    except Exception as e:
        print(f"Error creating database backup: {e}")

def log_trade_to_db(symbol, decision, amount):
    """
    Log a trade to the database with amount in USD.
    
    Args:
        symbol (str): The stock symbol
        decision (str): The trade decision (buy/sell)
        amount (float): The dollar amount of the trade
    """
    try:
        # Create a backup before logging new trade
        backup_db()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO trading_logs (symbol, decision, amount)
        VALUES (?, ?, ?)
        ''', (symbol, decision, float(amount)))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Create the database and table if they don't exist
init_db()
