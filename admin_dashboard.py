from dataclasses import dataclass
from typing import Callable, Dict, List

from flask import jsonify, request
from werkzeug.exceptions import BadRequest
import pymysql


@dataclass
class DashboardRouteDeps:
    """Container for dependency injection when registering admin routes."""

    get_dashboard_data: Callable[[], Dict]
    get_db_connection: Callable[[], pymysql.connections.Connection]


def register_admin_routes(app, deps: DashboardRouteDeps):
    """
    Attach admin dashboard API endpoints to the main Flask app.

    The old standalone `admin_dashboard.py` (SQLite) has been replaced with routes that
    reuse the MySQL data + helpers already configured in `app.py`.
    """

    @app.route("/api/dashboard/slots")
    def api_dashboard_slots():
        """Return slot + KPI data in JSON (used by dashboard widgets)."""
        data = deps.get_dashboard_data()
        booking_map = {b["slot_name"]: b for b in data["bookings"]}
        slots: List[Dict] = []
        for slot in data["slots"]:
            booking = booking_map.get(slot["slot_name"])
            slots.append(
                {
                    "slot_name": slot["slot_name"],
                    "slot_id": slot.get("slot_id"),
                    "occupied": slot["is_available"] == 0,
                    "username": (booking or {}).get("occupant", ""),
                    "occupant_name": (booking or {}).get("occupant_name"),
                    "entry_date": (booking or {}).get("entry_date"),
                    "entry_time": (booking or {}).get("entry_time"),
                    "exit_date": (booking or {}).get("exit_date"),
                    "exit_time": (booking or {}).get("exit_time"),
                    "status": (booking or {}).get("status"),
                }
            )

        payload = {
            "kpis": {
                "total": data["total_slots"],
                "occupied": data["occupied_slots"],
                "available": data["available_slots"],
            },
            "slots": slots,
        }
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
        """

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

        conn = deps.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE username = %s",
                    (username,),
                )
                user = cursor.fetchone()
                if not user:
                    raise BadRequest("Username not found.")

                cursor.execute(
                    "SELECT slot_id FROM parking_slots WHERE slot_name = %s",
                    (slot_name,),
                )
                slot = cursor.fetchone()
                if slot is None:
                    raise BadRequest("Slot does not exist.")

                # Check for time-based conflicts
                cursor.execute(
                    """
                    SELECT COUNT(*) as conflict_count
                    FROM bookings
                    WHERE slot_id = %s
                      AND status = 'active'
                      AND (
                        (TIMESTAMP(%s, %s) < TIMESTAMP(exit_date, exit_time) 
                         AND TIMESTAMP(%s, %s) > TIMESTAMP(entry_date, entry_time))
                      )
                    """,
                    (
                        slot["slot_id"],
                        payload["entry_date"],
                        payload["entry_time"],
                        payload["exit_date"],
                        payload["exit_time"],
                    ),
                )
                conflict = cursor.fetchone()
                if conflict and conflict["conflict_count"] > 0:
                    raise BadRequest("Slot is already booked for the selected time period.")

                try:
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

        return jsonify({"status": "ok"})

