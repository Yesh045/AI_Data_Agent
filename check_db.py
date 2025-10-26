import sqlite3

conn = sqlite3.connect('college.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")

    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])

    # Get sample data
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    sample = cursor.fetchall()
    print("Sample data:", sample)

conn.close()
