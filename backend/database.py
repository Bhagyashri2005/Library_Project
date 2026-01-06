import mysql.connector

def get_db_connection():
    print("\n🔌 Connecting to MySQL...")
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="2005",
            database="library_access",
            connection_timeout=5,
            auth_plugin="mysql_native_password",
            use_pure=True
        )
        print("✅ MySQL Connected Successfully")
        return conn
    except mysql.connector.Error as e:
        print("❌ MySQL Connection Error:", e)
        return None


