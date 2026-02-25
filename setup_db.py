import sys
import mysql.connector
from mysql.connector import Error
from db_config import DB_CFG

def create_database(cursor):
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CFG['database']}")
    cursor.execute(f"USE {DB_CFG['database']}")
    print(f"  ✔ Database '{DB_CFG['database']}' ready")

def create_student_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            candidate_id   VARCHAR(50)  PRIMARY KEY,
            name           VARCHAR(100) NOT NULL,
            department     VARCHAR(50),
            course         VARCHAR(50),
            exam_year      VARCHAR(10),
            exam_session   VARCHAR(20),
            email          VARCHAR(100),
            phone          VARCHAR(20),
            exam_center    VARCHAR(100),
            photo_path     VARCHAR(255),
            face_embedding LONGBLOB,
            created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✔ Table 'student' ready")

def create_verification_log_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_log (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            candidate_id  VARCHAR(50),
            name          VARCHAR(100),
            status        VARCHAR(20),
            timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✔ Table 'verification_log' ready")

def main():
    print("=" * 50)
    print("  Face Recognition System — Database Setup")
    print("=" * 50)
    print()
    try:
        conn = mysql.connector.connect(
            host=DB_CFG["host"],
            user=DB_CFG["user"],
            password=DB_CFG["password"]
        )
        print("  ✔ Connected to MySQL server")
    except Error as e:
        print(f"\n  ✘ Could not connect to MySQL: {e}")
        print("\n  Make sure:")
        print("    1. MySQL server is running")
        print("    2. Username and password in setup_db.py are correct")
        sys.exit(1)
    cursor = conn.cursor()
    try:
        create_database(cursor)
        create_student_table(cursor)
        create_verification_log_table(cursor)
        conn.commit()
        print()
        print("=" * 50)
        print("  Setup complete! You can now run main.py")
        print("=" * 50)
    except Error as e:
        print(f"\n  ✘ Error during setup: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()