import pymysql

# Database configuration
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "parking_slots",
}

def add_missing_slots():
    """Add parking slots P11 through P20 if they don't exist."""
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            # Check existing slots
            cursor.execute("SELECT slot_name FROM parking_slots ORDER BY slot_name")
            existing = [row[0] for row in cursor.fetchall()]
            print(f"Existing slots: {existing}")
            
            # Add missing slots P11-P20
            added = 0
            for i in range(11, 21):
                slot_name = f"P{i}"
                if slot_name not in existing:
                    cursor.execute(
                        "INSERT INTO parking_slots (slot_name, is_available) VALUES (%s, 1)",
                        (slot_name,)
                    )
                    print(f"Added slot: {slot_name}")
                    added += 1
                else:
                    print(f"Slot {slot_name} already exists")
            
            conn.commit()
            print(f"\nTotal slots added: {added}")
            
            # Show final count
            cursor.execute("SELECT COUNT(*) FROM parking_slots")
            total = cursor.fetchone()[0]
            print(f"Total parking slots in database: {total}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_slots()
