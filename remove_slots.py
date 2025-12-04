import pymysql

# Database configuration
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "parking_slots",
}

def remove_extra_slots():
    """Remove parking slots P11 through P20."""
    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            # Show current slots
            cursor.execute("SELECT slot_name FROM parking_slots ORDER BY slot_name")
            slots = [row[0] for row in cursor.fetchall()]
            print(f"Current slots: {slots}")
            print(f"Total: {len(slots)}")
            
            # Delete slots P11-P20
            deleted = 0
            for i in range(11, 21):
                slot_name = f"P{i}"
                cursor.execute("DELETE FROM parking_slots WHERE slot_name = %s", (slot_name,))
                if cursor.rowcount > 0:
                    print(f"Deleted: {slot_name}")
                    deleted += 1
            
            conn.commit()
            print(f"\nTotal slots deleted: {deleted}")
            
            # Show remaining slots
            cursor.execute("SELECT slot_name FROM parking_slots ORDER BY slot_name")
            remaining = [row[0] for row in cursor.fetchall()]
            print(f"\nRemaining slots: {remaining}")
            print(f"Total: {len(remaining)}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    remove_extra_slots()
