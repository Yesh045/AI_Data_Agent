import sqlite3
import os

def create_sample_database():
    """Create a sample SQLite database with products and sales data."""
    
    # Remove existing database if it exists
    if os.path.exists('sales.db'):
        os.remove('sales.db')
    
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    # Create products table
    cursor.execute('''
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        cost REAL NOT NULL
    )
    ''')

    # Create sales table
    cursor.execute('''
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_date TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity_sold INTEGER NOT NULL,
        sale_price REAL NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    ''')

    # Insert sample products
    products_data = [
        ('P001', 'Electronics', 'Laptop', 800.00),
        ('P002', 'Electronics', 'Smartphone', 550.00),
        ('P003', 'Office Supplies', 'Ergonomic Chair', 250.00),
        ('P004', 'Books', 'Python for Data Analysis', 45.50),
        ('P005', 'Office Supplies', 'Wireless Keyboard', 75.00),
        ('P006', 'Electronics', 'Tablet', 400.00),
        ('P007', 'Books', 'Machine Learning Guide', 60.00),
        ('P008', 'Office Supplies', 'Standing Desk', 350.00)
    ]

    # Insert sample sales data
    sales_data = [
        ('2024-01-15', 'P001', 5, 950.00), ('2024-01-16', 'P002', 10, 600.00),
        ('2024-01-20', 'P006', 3, 420.00), ('2024-02-10', 'P003', 3, 300.00),
        ('2024-02-12', 'P005', 8, 85.00), ('2024-02-15', 'P008', 2, 380.00),
        ('2024-03-05', 'P001', 3, 920.00), ('2024-03-20', 'P004', 20, 45.50),
        ('2024-03-25', 'P007', 15, 65.00), ('2024-04-01', 'P002', 7, 580.00),
        ('2024-04-02', 'P005', 12, 82.00), ('2024-04-10', 'P006', 6, 410.00),
        ('2024-05-05', 'P001', 4, 940.00), ('2024-05-15', 'P003', 5, 290.00),
        ('2024-05-20', 'P008', 3, 360.00)
    ]

    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products_data)
    cursor.executemany(
        "INSERT INTO sales (sale_date, product_id, quantity_sold, sale_price) VALUES (?, ?, ?, ?)", 
        sales_data
    )

    conn.commit()
    conn.close()
    
    print("Database 'sales.db' created successfully with sample data!")

if __name__ == '__main__':
    create_sample_database()