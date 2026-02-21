import sqlite3

conn = sqlite3.connect("database.db")
conn.execute("DROP TABLE IF EXISTS users")

conn.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("Users table recreated with email!")