import os
import secrets
import string

import pymysql
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import BadRequest

# Initialize Flask app with custom template and static folder paths
app = Flask(__name__, template_folder="templates", static_folder="templates/static")

# this is the secret key for session management
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# Set permanent session lifetime (30 days for remember me)
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# this is the database configuration
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "parking_slots"),
    "cursorclass": pymysql.cursors.DictCursor,  
    "autocommit": False, 
}


# this is used to get the database connection
def get_db_connection():
    """Create and return a MySQL database connection using MYSQL_CONFIG."""
    return pymysql.connect(**MYSQL_CONFIG)


# this is used to initialize the database
def init_db():
    """
    Initialize database schema and seed initial data.
    Creates tables (users, parking_slots, bookings) if they don't exist,
    seeds parking slots A1-A10 if table is empty,
    and creates default admin user (12345/admin123) if missing.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create users table - stores student authentication information
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                    username VARCHAR(50) NOT NULL,
                    full_name VARCHAR(150) NOT NULL,
                    email VARCHAR(255) NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('user', 'admin') DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id),
                    UNIQUE KEY uniq_username (username)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )

            # Check and add full_name column if missing
            cursor.execute(
                """
                SELECT COUNT(*) AS col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = 'full_name';
                """,
                (MYSQL_CONFIG["database"],),
            )
            if cursor.fetchone()["col_exists"] == 0:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN full_name VARCHAR(150) NOT NULL DEFAULT 'Unnamed User';"
                )

            # Check and add role column if missing
            cursor.execute(
                """
                SELECT COUNT(*) AS col_exists
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = 'role';
                """,
                (MYSQL_CONFIG["database"],),
            )
            if cursor.fetchone()["col_exists"] == 0:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN role ENUM('user', 'admin') DEFAULT 'user' AFTER password_hash;"
                )

            # Create parking_slots table - stores available parking spaces
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS parking_slots (
                    slot_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                    slot_name VARCHAR(10) NOT NULL,
                    is_available TINYINT(1) DEFAULT 1,
                    location VARCHAR(150) DEFAULT 'Nwssu Calbayog City, Samar, Philippines',
                    PRIMARY KEY (slot_id),
                    UNIQUE KEY uniq_slot_name (slot_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )

            # Create bookings table - links users to parking slots with time information
            # Foreign keys ensure referential integrity (cascade on delete/update)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                    user_id INT UNSIGNED NOT NULL,
                    slot_id INT UNSIGNED NOT NULL,
                    entry_date DATE NOT NULL,
                    entry_time TIME NOT NULL,
                    exit_date DATE NOT NULL,
                    exit_time TIME NOT NULL,
                    status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
                    booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (booking_id),
                    UNIQUE KEY uniq_slot_datetime (slot_id, entry_date, entry_time),
                    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id)
                        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
                    CONSTRAINT fk_bookings_slot FOREIGN KEY (slot_id)
                        REFERENCES parking_slots (slot_id) ON DELETE CASCADE ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
            )

            # Seed initial parking slots (P01 through P10) if table is empty
            cursor.execute("SELECT COUNT(1) AS total FROM parking_slots;")
            existing_slots = cursor.fetchone()["total"]
            if existing_slots == 0:
                # Create slots with specific locations
                slots_with_locations = [
                    ("P01", "CCIS Building - Front Row, Left Side"),
                    ("P02", "CCIS Building - Front Row, Left Center"),
                    ("P03", "CCIS Building - Front Row, Center"),
                    ("P04", "CCIS Building - Front Row, Right Center"),
                    ("P05", "CCIS Building - Front Row, Right Side"),
                    ("P06", "CCIS Building - Back Row, Left Side"),
                    ("P07", "CCIS Building - Back Row, Left Center"),
                    ("P08", "CCIS Building - Back Row, Center"),
                    ("P09", "CCIS Building - Back Row, Right Center"),
                    ("P10", "CCIS Building - Back Row, Right Side"),
                ]
                cursor.executemany(
                    "INSERT INTO parking_slots (slot_name, location) VALUES (%s, %s);",
                    slots_with_locations
                )
            else:
                # Update existing slots with specific locations
                locations = {
                    "P01": "CCIS Building - Front Row, Left Side",
                    "P02": "CCIS Building - Front Row, Left Center",
                    "P03": "CCIS Building - Front Row, Center",
                    "P04": "CCIS Building - Front Row, Right Center",
                    "P05": "CCIS Building - Front Row, Right Side",
                    "P06": "CCIS Building - Back Row, Left Side",
                    "P07": "CCIS Building - Back Row, Left Center",
                    "P08": "CCIS Building - Back Row, Center",
                    "P09": "CCIS Building - Back Row, Right Center",
                    "P10": "CCIS Building - Back Row, Right Side",
                }
                for slot_name, location in locations.items():
                    cursor.execute(
                        "UPDATE parking_slots SET location = %s WHERE slot_name = %s",
                        (location, slot_name)
                    )
                    # Also handle old format P1-P10
                    old_name = slot_name.lstrip("0").replace("P0", "P")
                    if old_name != slot_name:
                        cursor.execute(
                            "UPDATE parking_slots SET slot_name = %s, location = %s WHERE slot_name = %s",
                            (slot_name, location, old_name)
                        )

            # Create default admin user if it doesn't exist
            # Default credentials: username=admin, password=admin123
            cursor.execute(
                "SELECT 1 FROM users WHERE username = %s;", ("admin",)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO users (username, full_name, password_hash, role)
                    VALUES (%s, %s, %s, %s);
                    """,
                    (
                        "admin",
                        "System Administrator",
                        generate_password_hash("admin123"),
                        "admin",
                    ),
                )

        conn.commit()
    finally:
        conn.close()


def convert_to_12hour(time_str):
    """Convert 24-hour time string (HH:MM) to 12-hour format with AM/PM."""
    if not time_str:
        return ''
    
    try:
        from datetime import datetime
        time_obj = datetime.strptime(str(time_str), '%H:%M:%S' if len(str(time_str)) > 5 else '%H:%M')
        return time_obj.strftime('%I:%M %p')
    except:
        return str(time_str)


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a cryptographically secure password with mixed character classes.
    Ensures password contains at least one lowercase, uppercase, digit, and special character.
    Uses secrets module for secure random generation (cryptographically safe).
    """
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
    specials = "!@#$%^&*()-_=+"
    full_pool = alphabet + specials

    # Keep generating until password meets all requirements
    while True:
        password = "".join(secrets.choice(full_pool) for _ in range(length))
        # Verify password contains all required character types
        checks = (
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(c in specials for c in password),
        )
        if all(checks):
            return password


# Initialize database on application startup
init_db()


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login route - handles user authentication.
    GET: Displays login form (with remembered username if available)
    POST: Validates credentials and creates session if successful
    """
    error = None
    remembered_username = request.cookies.get('remembered_username', '')
    
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        remember_me = request.form.get("remember")

        # Query database for user with matching username
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id, password_hash, full_name, role FROM users WHERE username = %s",
                    (username,),
                )
                user = cursor.fetchone()
        finally:
            conn.close()

        # Verify password using secure hash comparison
        if user and check_password_hash(user["password_hash"], password):
            # Create session to track logged-in user
            session["user_id"] = user["user_id"]
            session["username"] = username
            session["full_name"] = user["full_name"]
            session["role"] = user.get("role", "user")
            
            # Set session to be permanent if remember me is checked
            if remember_me:
                session.permanent = True
            
            # Redirect based on role
            if session["role"] == "admin":
                response = redirect(url_for("dashboard"))
            else:
                response = redirect(url_for("booking"))
            
            # Set or clear remember me cookie
            if remember_me:
                response.set_cookie('remembered_username', username, max_age=30*24*60*60)  # 30 days
            else:
                response.set_cookie('remembered_username', '', max_age=0)  # Clear cookie
            
            return response

        error = "Invalid username or password!"

    return render_template("login.html", error=error, remembered_username=remembered_username)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    User registration route (for regular users/students only).
    GET: Displays signup form
    POST: Creates new user account
    - If password provided, uses it; otherwise generates secure password
    - Checks for duplicate student numbers before insertion
    """
    message = None
    message_type = None
    generated_password = None
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        provided_password = request.form.get("password", "").strip()
        # Use provided password or generate a secure one automatically
        plain_password = provided_password or generate_secure_password()
        password_hash = generate_password_hash(plain_password)

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if username already exists
                cursor.execute(
                    "SELECT 1 FROM users WHERE username = %s", (username,)
                )
                existing = cursor.fetchone()
                
                # Check if email already exists
                cursor.execute(
                    "SELECT 1 FROM users WHERE email = %s", (email,)
                )
                existing_email = cursor.fetchone()

                if not full_name:
                    message = "Name is required!"
                    message_type = "error"
                elif not email:
                    message = "Email is required!"
                    message_type = "error"
                elif provided_password and len(provided_password) < 6:
                    message = "Password must be at least 6 characters!"
                    message_type = "error"
                elif existing:
                    message = "Username already exists!"
                    message_type = "error"
                elif existing_email:
                    message = "Email already exists!"
                    message_type = "error"
                else:
                    # Insert new user with hashed password (role defaults to 'user')
                    cursor.execute(
                        "INSERT INTO users (username, full_name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
                        (username, full_name, email, password_hash, "user"),
                    )
                    conn.commit()
                    message = (
                        "Account created successfully!"
                    )
                    message_type = "success"
                    generated_password = plain_password
        finally:
            conn.close()
    
    return render_template(
        "signup.html",
        message=message,
        message_type=message_type,
        generated_password=generated_password,
    )


@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    """
    Admin registration route (requires existing admin authentication).
    Only admins can create new admin accounts.
    """
    # Check if user is logged in and is an admin
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    message = None
    message_type = None
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        admin_username = request.form["admin_username"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()

        if not all([full_name, admin_username, password, confirm_password]):
            message = "All fields are required!"
            message_type = "error"
        elif password != confirm_password:
            message = "Passwords do not match!"
            message_type = "error"
        elif len(password) < 8:
            message = "Password must be at least 8 characters!"
            message_type = "error"
        else:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # Check if username already exists
                    cursor.execute(
                        "SELECT 1 FROM users WHERE username = %s", (admin_username,)
                    )
                    existing = cursor.fetchone()

                    if existing:
                        message = "Username already exists!"
                        message_type = "error"
                    else:
                        # Insert new admin user
                        cursor.execute(
                            "INSERT INTO users (username, full_name, password_hash, role) VALUES (%s, %s, %s, %s)",
                            (admin_username, full_name, generate_password_hash(password), "admin"),
                        )
                        conn.commit()
                        message = "Admin account created successfully!"
                        message_type = "success"
            finally:
                conn.close()
    
    return render_template(
        "admin_signup.html",
        message=message,
        message_type=message_type,
    )


@app.route("/api/dashboard/users")
def api_dashboard_users():
    """
    Admin endpoint to get list of all users.
    Returns user information for admin dashboard.
    """
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    user_id,
                    username,
                    full_name,
                    role,
                    created_at
                FROM users
                WHERE role = 'user'
                ORDER BY created_at DESC
                LIMIT 50
                """
            )
            users = cursor.fetchall()
            
            # Convert datetime to string for JSON serialization
            for user in users:
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M')
            
            return jsonify({"users": users})
    finally:
        conn.close()


@app.route("/api/dashboard/users/<username>", methods=["DELETE"])
def api_delete_user(username):
    """
    Admin endpoint to delete a user.
    Only allows deletion of regular users, not admins.
    """
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First check if user exists and is not an admin
            cursor.execute(
                "SELECT user_id, role FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            if user['role'] == 'admin':
                return jsonify({"error": "Cannot delete admin users"}), 403
            
            # Delete user's bookings first (foreign key constraint)
            cursor.execute(
                "DELETE FROM bookings WHERE user_id = %s",
                (user['user_id'],)
            )
            
            # Delete the user
            cursor.execute(
                "DELETE FROM users WHERE user_id = %s",
                (user['user_id'],)
            )
            
            conn.commit()
            return jsonify({"message": "User deleted successfully"}), 200
            
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/change-password", methods=["POST"])
def change_password():
    """Change user password"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify current password
            cursor.execute(
                "SELECT password_hash FROM users WHERE user_id = %s",
                (session["user_id"],)
            )
            user = cursor.fetchone()
            
            if not user or not check_password_hash(user["password_hash"], current_password):
                return jsonify({"error": "Current password is incorrect"}), 401
            
            # Update password
            new_password_hash = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (new_password_hash, session["user_id"])
            )
            conn.commit()
            
            return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/logout")
def logout():
    """Logout route - clears session and redirects to login."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    """
    Password reset route.
    GET: Displays password reset form
    POST: Verifies old password and updates to new password
    """
    message = None
    message_type = None
    if request.method == "POST":
        username = request.form["username"].strip()
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]
        
        # Validate passwords match
        if new_password != confirm_password:
            message = "New passwords do not match!"
            message_type = "error"
        elif len(new_password) < 6:
            message = "New password must be at least 6 characters!"
            message_type = "error"
        else:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # Verify user exists and get password hash
                    cursor.execute(
                        "SELECT user_id, password_hash FROM users WHERE username = %s",
                        (username,),
                    )
                    user = cursor.fetchone()
                    
                    if user and check_password_hash(user["password_hash"], old_password):
                        # Update password
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE username = %s",
                            (generate_password_hash(new_password), username),
                        )
                        conn.commit()
                        message = "Password reset successfully! You can now login with your new password."
                        message_type = "success"
                    else:
                        message = "Invalid username or old password!"
                        message_type = "error"
            finally:
                conn.close()
    return render_template(
        "forgot.html", message=message, message_type=message_type
    )


@app.route("/user-dashboard")
def user_dashboard():
    """
    User dashboard showing their bookings and statistics.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # Redirect admins to admin dashboard
    if session.get("role") == "admin":
        return redirect(url_for("dashboard"))
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get user's bookings
            cursor.execute(
                """
                SELECT 
                    b.booking_id,
                    ps.slot_name,
                    ps.location,
                    b.entry_date,
                    b.entry_time,
                    b.exit_date,
                    b.exit_time,
                    b.status,
                    b.booked_at
                FROM bookings b
                JOIN parking_slots ps ON b.slot_id = ps.slot_id
                WHERE b.user_id = %s
                ORDER BY b.booked_at DESC
                LIMIT 20
                """,
                (session["user_id"],),
            )
            bookings = cursor.fetchall()
            
            # Calculate statistics (exclude cancelled bookings from total)
            cursor.execute(
                """
                SELECT 
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as total,
                    SUM(CASE WHEN status = 'active' 
                             AND TIMESTAMP(entry_date, entry_time) <= DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                             AND NOW() <= TIMESTAMP(exit_date, exit_time)
                        THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'active' 
                             AND TIMESTAMP(entry_date, entry_time) > DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                        THEN 1 ELSE 0 END) as upcoming
                FROM bookings
                WHERE user_id = %s
                """,
                (session["user_id"],),
            )
            stats = cursor.fetchone()
            
    finally:
        conn.close()
    
    return render_template(
        "user_dashboard.html",
        bookings=bookings,
        stats=stats
    )


@app.route("/booking", methods=["GET", "POST"])
def booking():
    """
    Parking slot booking route - main booking functionality.
    GET: Displays booking form with available slots
    POST: Processes booking request and creates reservation
    
    Security: Requires user to be logged in (session check)
    """
    # Require authentication - redirect to login if not logged in
    if "user_id" not in session:
        return redirect(url_for("login"))

    error = None
    conn = get_db_connection()
    try:
        if request.method == "POST":
            # Extract booking details from form
            entry_date = request.form["entry_date"]
            entry_time = request.form["entry_time"]
            exit_date = request.form["exit_date"]
            exit_time = request.form["exit_time"]
            selected_space = request.form.get("selected_space", "Not Selected")
            booking_type = request.form.get("booking_type", "book")

            # Verify selected slot exists
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT slot_id FROM parking_slots WHERE slot_name = %s",
                    (selected_space,),
                )
                slot = cursor.fetchone()

            if slot is None:
                error = "Selected slot does not exist. Please choose another."
            else:
                # Check for time-based conflicts with existing bookings
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT COUNT(*) as conflict_count
                        FROM bookings
                        WHERE slot_id = %s
                          AND status = 'active'
                          AND (
                            -- New booking overlaps with existing booking
                            (TIMESTAMP(%s, %s) < TIMESTAMP(exit_date, exit_time) 
                             AND TIMESTAMP(%s, %s) > TIMESTAMP(entry_date, entry_time))
                          )
                        """,
                        (
                            slot["slot_id"],
                            entry_date,
                            entry_time,
                            exit_date,
                            exit_time,
                        ),
                    )
                    conflict = cursor.fetchone()

                if conflict and conflict["conflict_count"] > 0:
                    error = "This slot is already booked for the selected time period. Please choose a different time or slot."
                else:
                    try:
                        # Create booking (no need to update is_available - we use time-based checking)
                        with conn.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO bookings (
                                    user_id, slot_id, entry_date, entry_time, exit_date, exit_time
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    session["user_id"],
                                    slot["slot_id"],
                                    entry_date,
                                    entry_time,
                                    exit_date,
                                    exit_time,
                                ),
                            )
                            booking_id = cursor.lastrowid
                            
                            # Get slot location
                            cursor.execute(
                                "SELECT location FROM parking_slots WHERE slot_name = %s",
                                (selected_space,)
                            )
                            slot_info = cursor.fetchone()
                            slot_location = slot_info['location'] if slot_info else "CCIS Building"
                            
                            conn.commit()
                        
                        # Show appropriate confirmation page based on booking type
                        template = "reserved.html" if booking_type == "reserve" else "confirm.html"
                        return render_template(
                            template,
                            booking_id=booking_id,
                            entry_date=entry_date,
                            entry_time=convert_to_12hour(entry_time),
                            exit_date=exit_date,
                            exit_time=convert_to_12hour(exit_time),
                            selected_space=selected_space,
                            slot_location=slot_location,
                        )
                    except pymysql.err.IntegrityError:
                        # Handle duplicate booking attempts (unique constraint violation)
                        error = "Unable to save booking. Please try different details."

        # Fetch all parking slots for display (GET request or after error)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT slot_id, slot_name, is_available FROM parking_slots ORDER BY slot_name"
            )
            slots = cursor.fetchall()
    finally:
        conn.close()

    return render_template("booking.html", slots=slots, error=error)


# ---------------------------
# Admin dashboard + helpers
# ---------------------------
def get_dashboard_data():
    """Collect aggregated dashboard data (slot stats + active bookings + users)."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get slot statistics
            cursor.execute("SELECT COUNT(*) AS total FROM parking_slots")
            total_slots = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS occupied FROM parking_slots WHERE is_available = 0"
            )
            occupied_slots = cursor.fetchone()["occupied"]

            cursor.execute(
                "SELECT slot_id, slot_name, is_available FROM parking_slots ORDER BY slot_name"
            )
            slots = cursor.fetchall()

            # Get active bookings with user details
            cursor.execute(
                """
                SELECT
                    ps.slot_name,
                    ps.slot_id,
                    u.username AS occupant,
                    u.full_name AS occupant_name,
                    b.booking_id,
                    b.entry_date,
                    b.entry_time,
                    b.exit_date,
                    b.exit_time,
                    b.status,
                    b.booked_at
                FROM bookings b
                JOIN parking_slots ps ON b.slot_id = ps.slot_id
                JOIN users u ON b.user_id = u.user_id
                WHERE b.status = 'active'
                ORDER BY b.booked_at DESC
                """
            )
            bookings = cursor.fetchall()
            
            # Convert date/time objects to strings for JSON serialization
            for booking in bookings:
                if booking.get('entry_date'):
                    booking['entry_date'] = str(booking['entry_date'])
                if booking.get('exit_date'):
                    booking['exit_date'] = str(booking['exit_date'])
                if booking.get('entry_time'):
                    booking['entry_time'] = str(booking['entry_time'])
                if booking.get('exit_time'):
                    booking['exit_time'] = str(booking['exit_time'])
                if booking.get('booked_at'):
                    booking['booked_at'] = booking['booked_at'].strftime('%Y-%m-%d %H:%M:%S')

            # Get user statistics
            cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'user'")
            total_users = cursor.fetchone()["total"]
            
            cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role = 'admin'")
            total_admins = cursor.fetchone()["total"]
    finally:
        conn.close()

    available_slots = total_slots - occupied_slots
    return {
        "total_slots": total_slots,
        "occupied_slots": occupied_slots,
        "available_slots": available_slots,
        "slots": slots,
        "bookings": bookings,
        "total_users": total_users,
        "total_admins": total_admins,
    }


@app.route("/dashboard")
def dashboard():
    """Admin dashboard showing realtime slot + booking overview."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    # Check if user is admin
    if session.get("role") != "admin":
        return redirect(url_for("booking"))

    data = get_dashboard_data()
    return render_template("dashboard.html", dashboard_data=data)


# ---------------------------
# Admin Dashboard API Routes
# ---------------------------
@app.route("/api/dashboard/slots")
def api_dashboard_slots():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get current/active bookings (entry time within 15 minutes or already started, and not yet ended)
            cursor.execute(
                """
                SELECT 
                    ps.slot_id,
                    ps.slot_name,
                    u.username AS occupant,
                    u.full_name AS occupant_name,
                    b.booking_id,
                    b.entry_date,
                    b.entry_time,
                    b.exit_date,
                    b.exit_time,
                    b.status
                FROM bookings b
                JOIN parking_slots ps ON b.slot_id = ps.slot_id
                JOIN users u ON b.user_id = u.user_id
                WHERE b.status = 'active'
                  AND TIMESTAMP(b.entry_date, b.entry_time) <= DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                  AND NOW() <= TIMESTAMP(b.exit_date, b.exit_time)
                """
            )
            current = cursor.fetchall()
            current_map = {c["slot_name"]: c for c in current}

            # Get upcoming/reserved bookings (entry time more than 15 minutes in the future)
            cursor.execute(
                """
                SELECT 
                    ps.slot_id,
                    ps.slot_name,
                    u.username AS occupant,
                    u.full_name AS occupant_name,
                    b.booking_id,
                    b.entry_date,
                    b.entry_time,
                    b.exit_date,
                    b.exit_time,
                    b.status
                FROM bookings b
                JOIN parking_slots ps ON b.slot_id = ps.slot_id
                JOIN users u ON b.user_id = u.user_id
                WHERE b.status = 'active'
                  AND TIMESTAMP(b.entry_date, b.entry_time) > DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                ORDER BY b.entry_date, b.entry_time
                """
            )
            upcoming = cursor.fetchall()
            # Group by slot_name, keep only the earliest booking per slot
            upcoming_map = {}
            for u in upcoming:
                slot_name = u["slot_name"]
                if slot_name not in upcoming_map:
                    upcoming_map[slot_name] = u

            cursor.execute(
                "SELECT slot_id, slot_name, is_available FROM parking_slots ORDER BY slot_name"
            )
            all_slots = cursor.fetchall()
    finally:
        conn.close()

    def _s(v):
        return (None if v is None else str(v))

    slots = []
    for s in all_slots:
        cur = current_map.get(s["slot_name"]) or {}
        upc = upcoming_map.get(s["slot_name"]) or {}
        state = "available"
        src = None
        if cur:
            state = "occupied"
            src = cur
        elif upc:
            state = "reserved"
            src = upc
        # If no time-based booking found, slot is truly available
        slots.append(
            {
                "slot_name": s["slot_name"],
                "slot_id": s.get("slot_id"),
                "occupied": state == "occupied",
                "state": state,
                "username": (src or {}).get("occupant", ""),
                "occupant_name": (src or {}).get("occupant_name"),
                "entry_date": _s((src or {}).get("entry_date")),
                "entry_time": _s((src or {}).get("entry_time")),
                "exit_date": _s((src or {}).get("exit_date")),
                "exit_time": _s((src or {}).get("exit_time")),
                "status": (src or {}).get("status"),
                "booking_id": (src or {}).get("booking_id"),
                "is_available": s.get("is_available", 1),
            }
        )

    total = len(all_slots)
    occupied = sum(1 for s in slots if s["state"] == "occupied")
    reserved = sum(1 for s in slots if s["state"] == "reserved")
    available = total - occupied - reserved
    payload = {"kpis": {"total": total, "occupied": occupied, "reserved": reserved, "available": available}, "slots": slots}
    return jsonify(payload)


@app.route("/api/dashboard/bookings", methods=["POST"])
def api_dashboard_add_booking():
    """
    Admin endpoint to create bookings programmatically.
    
    Expected JSON payload:
        {
            "username": "12345",
            "slot_name": "P1",
            "entry_date": "2024-12-01",
            "entry_time": "08:00",
            "exit_date": "2024-12-01",
            "exit_time": "10:00"
        }
    
    Returns:
        JSON response with status or error message
    """
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    payload = request.get_json(silent=True) or {}
    required_fields = [
        "username",
        "slot_name",
        "entry_date",
        "entry_time",
        "exit_date",
        "exit_time",
    ]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        raise BadRequest(f"Missing required fields: {', '.join(missing)}")

    username = payload["username"].strip()
    slot_name = payload["slot_name"].strip()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify user exists
            cursor.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (username,),
            )
            user = cursor.fetchone()
            if not user:
                raise BadRequest("Username not found.")

            # Check slot availability using real-time logic
            cursor.execute(
                """
                SELECT ps.slot_id, ps.slot_name,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM bookings b
                            WHERE b.slot_id = ps.slot_id
                            AND b.status = 'active'
                            AND (
                                (b.entry_date < %s OR (b.entry_date = %s AND b.entry_time < %s))
                                AND (b.exit_date > %s OR (b.exit_date = %s AND b.exit_time > %s))
                            )
                        ) THEN 0
                        ELSE 1
                    END AS is_available
                FROM parking_slots ps
                WHERE ps.slot_name = %s
                """,
                (
                    payload["exit_date"],
                    payload["exit_date"],
                    payload["exit_time"],
                    payload["entry_date"],
                    payload["entry_date"],
                    payload["entry_time"],
                    slot_name,
                ),
            )
            slot = cursor.fetchone()
            
            if slot is None:
                raise BadRequest("Slot does not exist.")
            if not slot["is_available"]:
                raise BadRequest("Slot already occupied for this time period.")

            try:
                # Create booking
                cursor.execute(
                    """
                    INSERT INTO bookings (
                        user_id, slot_id, entry_date, entry_time, exit_date, exit_time
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user["user_id"],
                        slot["slot_id"],
                        payload["entry_date"],
                        payload["entry_time"],
                        payload["exit_date"],
                        payload["exit_time"],
                    ),
                )
                conn.commit()
            except pymysql.err.IntegrityError:
                conn.rollback()
                raise BadRequest("Booking conflicts with an existing reservation.")
    finally:
        conn.close()

    return jsonify({"status": "ok", "message": "Booking created successfully"})


@app.route("/api/dashboard/bookings/<int:booking_id>", methods=["DELETE"])
def api_dashboard_delete_booking(booking_id):
    """
    Admin endpoint to cancel/delete a booking.
    
    Args:
        booking_id: The ID of the booking to cancel
    
    Returns:
        JSON response with status
    """
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT booking_id, slot_id FROM bookings WHERE booking_id = %s",
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                return jsonify({"error": "Booking not found"}), 404
            cursor.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
                (booking_id,),
            )
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"status": "ok", "message": "Booking cancelled successfully"})


@app.route("/api/dashboard/bookings/<int:booking_id>/cancel", methods=["POST"]) 
def api_dashboard_cancel_booking(booking_id):
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT booking_id, slot_id FROM bookings WHERE booking_id = %s",
                (booking_id,),
            )
            booking = cursor.fetchone()
            if not booking:
                return jsonify({"error": "Booking not found"}), 404
            cursor.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
                (booking_id,),
            )
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"status": "ok", "message": "Booking cancelled successfully"})


@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
def cancel_user_booking(booking_id):
    """
    User endpoint to cancel their own booking.
    Users can only cancel their own bookings.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized - Please login"}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify booking exists and belongs to the user
            cursor.execute(
                "SELECT booking_id, user_id, slot_id FROM bookings WHERE booking_id = %s",
                (booking_id,),
            )
            booking = cursor.fetchone()
            
            if not booking:
                return jsonify({"error": "Booking not found"}), 404
            
            # Check if booking belongs to the logged-in user
            if booking["user_id"] != session["user_id"]:
                return jsonify({"error": "You can only cancel your own bookings"}), 403
            
            # Cancel the booking
            cursor.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
                (booking_id,),
            )
            conn.commit()
            
            return jsonify({"status": "ok", "message": "Booking cancelled successfully"})
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/check-availability", methods=["POST"])
def api_check_availability():
    """
    Check real-time availability of parking slots for a given time period.
    Returns list of slots with their availability status.
    """
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    entry_date = data.get("entry_date")
    entry_time = data.get("entry_time")
    exit_date = data.get("exit_date")
    exit_time = data.get("exit_time")

    if not all([entry_date, entry_time, exit_date, exit_time]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Get all slots with their booking status for the requested time period
            cursor.execute(
                """
                SELECT 
                    ps.slot_id,
                    ps.slot_name,
                    ps.is_available,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM bookings b
                            WHERE b.slot_id = ps.slot_id
                              AND b.status = 'active'
                              AND (
                                -- Check for time overlap
                                (TIMESTAMP(%s, %s) < TIMESTAMP(b.exit_date, b.exit_time) 
                                 AND TIMESTAMP(%s, %s) > TIMESTAMP(b.entry_date, b.entry_time))
                              )
                        ) THEN 0
                        ELSE 1
                    END as available_for_period,
                    (
                        SELECT CASE
                            WHEN TIMESTAMP(b.entry_date, b.entry_time) <= DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                                 AND NOW() <= TIMESTAMP(b.exit_date, b.exit_time)
                            THEN 'occupied'
                            WHEN TIMESTAMP(b.entry_date, b.entry_time) > DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                            THEN 'reserved'
                            ELSE NULL
                        END
                        FROM bookings b
                        WHERE b.slot_id = ps.slot_id
                          AND b.status = 'active'
                          AND (
                            (TIMESTAMP(b.entry_date, b.entry_time) <= DATE_ADD(NOW(), INTERVAL 15 MINUTE)
                             AND NOW() <= TIMESTAMP(b.exit_date, b.exit_time))
                            OR
                            (TIMESTAMP(b.entry_date, b.entry_time) > DATE_ADD(NOW(), INTERVAL 15 MINUTE))
                          )
                        ORDER BY b.entry_date, b.entry_time
                        LIMIT 1
                    ) as current_state
                FROM parking_slots ps
                ORDER BY ps.slot_name
                """,
                (entry_date, entry_time, exit_date, exit_time),
            )
            slots = cursor.fetchall()

            # Format response based on availability for the REQUESTED period
            slot_list = []
            for s in slots:
                # The state should reflect availability for the requested time period
                # NOT the current state
                if s["available_for_period"]:
                    state = "available"  # Available for the requested period
                else:
                    state = "occupied"  # Not available (conflict with requested period)

                slot_list.append(
                    {
                        "slot_id": s["slot_id"],
                        "slot_name": s["slot_name"],
                        "is_available": s["available_for_period"],
                        "state": state,
                    }
                )

            # Calculate KPIs
            total = len(slot_list)
            available = sum(1 for s in slot_list if s["state"] == "available")
            occupied = sum(1 for s in slot_list if s["state"] == "occupied")
            reserved = sum(1 for s in slot_list if s["state"] == "reserved")

            return jsonify(
                {
                    "slots": slot_list,
                    "kpis": {
                        "total": total,
                        "available": available,
                        "occupied": occupied,
                        "reserved": reserved,
                    },
                }
            )
    finally:
        conn.close()


# Run Flask development server when script is executed directly
# debug=True enables auto-reload and detailed error pages (disable in production)
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


# Utility admin endpoint to rename slots from A1-A10 to P1-P10
@app.route("/api/admin/slots/rename_A_to_P", methods=["POST"]) 
def api_admin_rename_slots_A_to_P():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized - Admin access required"}), 401

    conn = get_db_connection()
    renamed = []
    try:
        with conn.cursor() as cursor:
            for i in range(1, 11):
                old = f"A{i}"
                new = f"P{i}"
                cursor.execute("SELECT slot_id FROM parking_slots WHERE slot_name = %s", (old,))
                row = cursor.fetchone()
                if not row:
                    continue
                # Skip if target exists to avoid unique conflict
                cursor.execute("SELECT 1 FROM parking_slots WHERE slot_name = %s", (new,))
                if cursor.fetchone():
                    continue
                cursor.execute("UPDATE parking_slots SET slot_name = %s WHERE slot_id = %s", (new, row["slot_id"]))
                renamed.append({"from": old, "to": new})
            conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"status": "ok", "renamed": renamed})



