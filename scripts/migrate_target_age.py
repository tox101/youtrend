import sqlite3
import os

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "youtube.db"))
print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if target_age column already exists
    cursor.execute("PRAGMA table_info(videos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "target_age" not in columns:
        print("Adding 'target_age' column to 'videos' table...")
        cursor.execute("ALTER TABLE videos ADD COLUMN target_age VARCHAR(20) DEFAULT 'all'")
        conn.commit()
        print("Successfully added target_age column.")
    else:
        print("'target_age' column already exists in 'videos' table.")
        
    # Verify by printing schema
    cursor.execute("PRAGMA table_info(videos)")
    print("Current videos table columns:", [col[1] for col in cursor.fetchall()])
    
except Exception as e:
    print("Error during migration:", e)
finally:
    conn.close()
