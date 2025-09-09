import psycopg2
from psycopg2 import sql

def test_connection():
    try:
        # Try to connect to the default postgres database first
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",  # Connect to default postgres DB first
            user="postgres",
            password="postgres"
        )
        conn.autocommit = True
        
        # Check if our database exists
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'sahaayak'")
            exists = cur.fetchone()
            
            if not exists:
                print("Database 'sahaayak' does not exist. Creating it...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier('sahaayak'))
                )
                print("Database 'sahaayak' created successfully.")
            else:
                print("Database 'sahaayak' already exists.")
                
        # Now connect to the sahaayak database
        conn = psycopg2.connect(
            host="localhost",
            database="sahaayai",  # This is intentionally incorrect to test the error handling
            user="postgres",
            password="postgres"
        )
        print("Successfully connected to 'sahaayak' database!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your PostgreSQL username and password")
        print("3. Verify the database name is correct")
        print("4. Check if PostgreSQL is configured to accept connections")
        print("\nYou can start PostgreSQL service using: ")
        print("Windows: 'net start postgresql'")
        print("Linux: 'sudo service postgresql start'")

if __name__ == "__main__":
    test_connection()
