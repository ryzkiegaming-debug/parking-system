import pymysql

# Database configuration
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "parking_slots",
}

def fix_slot_order():
    """Rename slots to have proper ordering (P01, P02, etc.)"""
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            # Get all existing slots
            cursor.execute("SELECT slot_id, slot_name FROM parking_slots ORDER BY slot_id")
            slots = cursor.fetchall()
            
            print("Current slots:")
            for slot in slots:
                print(f"  ID: {slot[0]}, Name: {slot[1]}")
            
            # Rename slots to have zero-padded numbers (P01, P02, ..., P20)
            print("\nRenaming slots...")
            for i in range(1, 21):
                old_name = f"P{i}"
                new_name = f"P{i:02d}"  # Zero-padded (P01, P02, etc.)
                
                cursor.execute(
                    "UPDATE parking_slots SET slot_name = %s WHERE slot_name = %s",
                    (new_name, old_name)
                )
                print(f"  {old_name} -> {new_name}")
            
            conn.commit()
            
            # Show final result
            print("\nFinal slots (ordered):")
            cursor.execute("SELECT slot_id, slot_name FROM parking_slots ORDER BY slot_name")
            slots = cursor.fetchall()
            for slot in slots:
                print(f"  ID: {slot[0]}, Name: {slot[1]}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    fix_slot_order()
