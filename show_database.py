import sqlite3
from contextlib import contextmanager

DATABASE_NAME = "restaurant.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute('PRAGMA foreign_keys = ON')
    try:
        yield conn
    finally:
        conn.close()

def show_all_tables():
    with get_db_connection() as conn:
        # Get all tables in the database
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n=== DATABASE TABLES ===")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * (len(table_name) + 7))
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Get all data from the table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            print(f"\nData ({len(rows)} rows):")
            if rows:
                # Print column headers
                print("  " + " | ".join(col[1] for col in columns))
                print("  " + "-" * (sum(len(col[1]) for col in columns) + 3 * (len(columns) - 1)))
                
                # Print data rows
                for row in rows:
                    print("  " + " | ".join(str(value) for value in row))
            else:
                print("  (No data)")
            print("\n" + "="*50)

if __name__ == "__main__":
    try:
        show_all_tables()
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")