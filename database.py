import sqlite3
from pathlib import Path
from datetime import datetime

# === Database Configuration ===
DB_PATH = Path("engagement.db")

# === Database Functions ===

def init_db():
    """Initialize the database and create necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            score INTEGER DEFAULT 5,
            total_score INTEGER DEFAULT 5
        )
    ''')
    
    # Instagram links table with auto-incrementing link_id
    c.execute('''
        CREATE TABLE IF NOT EXISTS instagram_links (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            link TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    
    # User likes table
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_likes (
        user_id INTEGER,
        link_id INTEGER,
        PRIMARY KEY (user_id, link_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (link_id) REFERENCES instagram_links (id)
    )
    ''')


    conn.commit()
    conn.close()



def increment_score(user_id: int, username: str):
    """Increment the score for a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if the user exists
    c.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()

    if result:
        # User exists, increment score and total_score
        c.execute('UPDATE users SET score = score + 1, total_score = total_score + 1 WHERE user_id = ?', (user_id,))
    else:
        # User doesn't exist, insert a new user with score and total_score
        c.execute('''
            INSERT INTO users (user_id, username, score, total_score)
            VALUES (?, ?, 1, 1)
        ''', (user_id, username))
    
    conn.commit()
    conn.close()

def decrement_score(user_id: int):
    """Decrement the score for a user (only decreases score, not total_score)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if the user exists
    c.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()

    if result:
        # User exists, decrement score
        new_score = result[0] - 1
        # Ensure the score doesn't go below 0
        new_score = max(new_score, 0)
        c.execute('UPDATE users SET score = ? WHERE user_id = ?', (new_score, user_id))
    else:
        # User doesn't exist
        print("User not found.")
    
    conn.commit()
    conn.close()

def get_user_score(user_id: int):
    """Get the score of a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT score FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_username(user_id: int):
    """Get the score of a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT get_username FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0




def get_total_score(user_id: int):
    """Get the score of a user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT total_score FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0



def get_leaderboard(limit=5):
    """Get the leaderboard (top users based on total_score)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, total_score FROM users ORDER BY total_score DESC LIMIT ?', (limit,))
    results = c.fetchall()
    conn.close()
    return results




def save_link(user_id: int, link: str):
    """Save Instagram link to the database."""
    timestamp = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO instagram_links (user_id, link, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, link, timestamp))
    conn.commit()
    conn.close()

def save_user_like(user_id: int, link_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO user_likes (user_id, link_id) VALUES (?, ?)', (user_id, link_id))
    conn.commit()
    conn.close()

def has_liked(user_id: int, link_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT 1 FROM user_likes WHERE user_id = ? AND link_id = ?', (user_id, link_id))
    result = c.fetchone()
    conn.close()
    return bool(result)

def get_link_by_id(link_id: int):
    """Retrieve a link by its ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT link FROM instagram_links WHERE link_id = ?', (link_id,))  # Change id to link_id
    result = c.fetchone()
    conn.close()
    return {"link": result[0]} if result else None

def load_links(user_id: int):
    """Load the last 7 Instagram links the user hasn't liked yet, excluding their own links."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT link_id, link FROM instagram_links
        WHERE user_id != ? AND link_id NOT IN (
            SELECT link_id FROM user_likes WHERE user_id = ?
        )
        ORDER BY timestamp DESC LIMIT 7
    ''', (user_id, user_id))
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "link": row[1]} for row in rows]



def set_username(user_id: int, username: str):
    """Save the Instagram username of the user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Only insert user_id and username. score and total_score will use their default values
    c.execute('''
        INSERT OR REPLACE INTO users (user_id, username)
        VALUES (?, ?)
    ''', (user_id, username))
    
    conn.commit()
    conn.close()

def get_username(user_id: int):
    """Get the Instagram username of the user."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None






