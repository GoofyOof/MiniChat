import sqlite3

connection = sqlite3.connect("database.db")


# =========================================
# USERS
# =========================================

try:
    connection.execute("""
        ALTER TABLE users
        ADD COLUMN display_name TEXT
    """)
    print("display_name lagt til.")
except sqlite3.OperationalError:
    print("display_name finnes allerede.")


try:
    connection.execute("""
        ALTER TABLE users
        ADD COLUMN bio TEXT DEFAULT ''
    """)
    print("bio lagt til.")
except sqlite3.OperationalError:
    print("bio finnes allerede.")


try:
    connection.execute("""
        ALTER TABLE users
        ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)
    print("created_at lagt til.")
except sqlite3.OperationalError:
    print("created_at finnes allerede.")


connection.commit()
connection.close()

print("Database updated!")