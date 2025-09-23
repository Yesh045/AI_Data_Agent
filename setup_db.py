import sqlite3

# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect('sales.db')
cursor = conn.cursor()

# --- Create Tables ---
# Products table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    cost REAL NOT NULL
)
''')

# Sales table
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity_sold INTEGER NOT NULL,
    sale_price REAL NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products (product_id)
)
''')

# --- Clear existing data to prevent duplicates on re-run ---
cursor.execute("DELETE FROM sales")
cursor.execute("DELETE FROM products")


# --- Insert Sample Data ---
products_data = [
    ('P001', 'Electronics', 'Laptop', 800.00),
    ('P002', 'Electronics', 'Smartphone', 550.00),
    ('P003', 'Office Supplies', 'Ergonomic Chair', 250.00),
    ('P004', 'Books', 'Python for Data Analysis', 45.50),
    ('P005', 'Office Supplies', 'Wireless Keyboard', 75.00)
]

sales_data = [
    ('2024-01-15', 'P001', 5, 950.00),
    ('2024-01-16', 'P002', 10, 600.00),
    ('2024-02-10', 'P003', 3, 300.00),
    ('2024-02-12', 'P005', 8, 85.00),
    ('2024-03-05', 'P001', 3, 920.00),
    ('2024-03-20', 'P004', 20, 45.50),
    ('2024-04-01', 'P002', 7, 580.00),
    ('2024-04-02', 'P005', 12, 82.00)
]

cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products_data)
cursor.executemany("INSERT INTO sales (sale_date, product_id, quantity_sold, sale_price) VALUES (?, ?, ?, ?)", sales_data)


# Commit changes and close connection
conn.commit()
conn.close()

print("Database 'sales.db' created and populated successfully.")

