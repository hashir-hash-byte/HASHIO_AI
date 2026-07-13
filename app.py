def init_db():
    conn = sqlite3.connect("hashio_data.db")
    c = conn.cursor()
    # 1. Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
    ''')
    # 2. Create History Table safely
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            input_type TEXT,
            summary TEXT
        )
    ''')
    
    # 3. SCHEMA MIGRATION: Forcefully add username column to old tables if missing
    try:
        c.execute("ALTER TABLE history ADD COLUMN username TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        # If the column already exists, SQLite throws an error, which we safely ignore here
        pass
        
    conn.commit()
    conn.close()
