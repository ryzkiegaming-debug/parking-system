from app import get_db_connection

conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        cursor.execute("SELECT username, full_name, role FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        print("Admin accounts found:")
        for admin in admins:
            print(f"  - Username: {admin['username']}, Name: {admin['full_name']}, Role: {admin['role']}")
        
        if not admins:
            print("No admin accounts found!")
finally:
    conn.close()
