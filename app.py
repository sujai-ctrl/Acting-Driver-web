from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory
)

import sqlite3
import os
import uuid

from functools import wraps
from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "acting-driver-secret-key-change-later"

DATABASE = "database.db"

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads",
    "driver_documents"
)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "pdf"
}

MAX_FILE_SIZE = 5 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE MIGRATION HELPERS
# =========================================================

def column_exists(
    cursor,
    table_name,
    column_name
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    for column in columns:

        if column["name"] == column_name:

            return True

    return False


def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    column_type
):

    if not column_exists(
        cursor,
        table_name,
        column_name
    ):

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_type}
            """
        )


# =========================================================
# FILE VALIDATION
# =========================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = (
        filename.rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_EXTENSIONS


# =========================================================
# DATABASE CREATION
# =========================================================

def create_database():

    conn = get_db()

    cursor = conn.cursor()


    # =====================================================
    # USERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            phone TEXT,

            password TEXT NOT NULL,

            created_at TEXT

        )
    """)


    add_column_if_missing(
        cursor,
        "users",
        "name",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "phone",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "password",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "users",
        "created_at",
        "TEXT"
    )


    # =====================================================
    # DRIVERS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone TEXT,

            rating REAL DEFAULT 4.8,

            experience INTEGER DEFAULT 5,

            distance REAL DEFAULT 2.0,

            status TEXT DEFAULT 'Available',

            email TEXT,

            password TEXT,

            license_number TEXT,

            license_proof TEXT,

            id_proof TEXT,

            vehicle_type TEXT,

            vehicle_number TEXT,

            verification_status TEXT
                DEFAULT 'Pending Verification'

        )
    """)


    # Existing database migration

    add_column_if_missing(
        cursor,
        "drivers",
        "name",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "phone",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "rating",
        "REAL"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "experience",
        "INTEGER"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "distance",
        "REAL"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "status",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "email",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "password",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "license_number",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "license_proof",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "id_proof",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "vehicle_type",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "vehicle_number",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "drivers",
        "verification_status",
        "TEXT"
    )


    # =====================================================
    # BOOKINGS TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            driver_id INTEGER,

            pickup TEXT NOT NULL,

            destination TEXT NOT NULL,

            date TEXT NOT NULL,

            time TEXT NOT NULL,

            vehicle TEXT NOT NULL,

            status TEXT DEFAULT 'Pending',

            created_at TEXT

        )
    """)


    add_column_if_missing(
        cursor,
        "bookings",
        "user_id",
        "INTEGER"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "driver_id",
        "INTEGER"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "pickup",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "destination",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "date",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "time",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "vehicle",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "status",
        "TEXT"
    )

    add_column_if_missing(
        cursor,
        "bookings",
        "created_at",
        "TEXT"
    )


    # =====================================================
    # EXISTING SAMPLE DRIVERS
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM drivers
    """)

    driver_count = cursor.fetchone()["count"]


    if driver_count == 0:

        drivers = [

            (
                "Arun Kumar",
                "9876543210",
                4.9,
                8,
                2.1,
                "Available"
            ),

            (
                "Karthik Raj",
                "9876543211",
                4.8,
                6,
                3.4,
                "Available"
            ),

            (
                "Vijay Kumar",
                "9876543212",
                4.7,
                5,
                4.2,
                "Available"
            ),

            (
                "Suresh Babu",
                "9876543213",
                4.9,
                10,
                1.8,
                "Available"
            ),

            (
                "Rahul Dev",
                "9876543214",
                4.6,
                4,
                5.1,
                "Available"
            )

        ]


        cursor.executemany("""
            INSERT INTO drivers
            (
                name,
                phone,
                rating,
                experience,
                distance,
                status,
                verification_status
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """, [

            (
                name,
                phone,
                rating,
                experience,
                distance,
                status,
                "Approved"
            )

            for
            name,
            phone,
            rating,
            experience,
            distance,
            status
            in drivers

        ])


    # =====================================================
    # EXISTING SAMPLE DRIVER LOGIN
    # =====================================================

    driver_credentials = {

        "Arun Kumar":
            (
                "arun@actingdriver.com",
                "driver123"
            ),

        "Karthik Raj":
            (
                "karthik@actingdriver.com",
                "driver123"
            ),

        "Vijay Kumar":
            (
                "vijay@actingdriver.com",
                "driver123"
            ),

        "Suresh Babu":
            (
                "suresh@actingdriver.com",
                "driver123"
            ),

        "Rahul Dev":
            (
                "rahul@actingdriver.com",
                "driver123"
            )

    }


    for driver_name, credentials in driver_credentials.items():

        driver_email = credentials[0]

        driver_password = credentials[1]


        cursor.execute("""
            SELECT password
            FROM drivers
            WHERE name = ?
        """, (
            driver_name,
        ))


        driver = cursor.fetchone()


        if driver:

            if not driver["password"]:

                cursor.execute("""
                    UPDATE drivers

                    SET
                        email = ?,
                        password = ?,
                        verification_status = 'Approved'

                    WHERE name = ?

                """, (
                    driver_email,
                    generate_password_hash(
                        driver_password
                    ),
                    driver_name
                ))

            else:

                cursor.execute("""
                    UPDATE drivers

                    SET
                        email = ?,
                        verification_status = 'Approved'

                    WHERE name = ?

                """, (
                    driver_email,
                    driver_name
                ))


    conn.commit()

    conn.close()


# =========================================================
# CUSTOMER LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)

    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# DRIVER LOGIN REQUIRED
# =========================================================

def driver_login_required(function):

    @wraps(function)

    def wrapper(*args, **kwargs):

        if "driver_id" not in session:

            flash(
                "Please login as a driver to continue.",
                "error"
            )

            return redirect(
                url_for("driver_login")
            )

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "driver_id" in session:

        return redirect(
            url_for("driver_dashboard")
        )


    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )


    return redirect(
        url_for("login")
    )


# =========================================================
# CUSTOMER REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        if not name:

            flash(
                "Please enter your full name.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if not email:

            flash(
                "Please enter your email address.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if not password:

            flash(
                "Please enter a password.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "register.html"
            )


        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "register.html"
            )


        conn = get_db()

        cursor = conn.cursor()


        # Check customer

        cursor.execute("""
            SELECT id
            FROM users
            WHERE LOWER(email) = ?
        """, (
            email,
        ))

        existing_user = cursor.fetchone()


        # Check driver also

        cursor.execute("""
            SELECT id
            FROM drivers
            WHERE LOWER(email) = ?
        """, (
            email,
        ))

        existing_driver = cursor.fetchone()


        if existing_user or existing_driver:

            conn.close()

            flash(
                "This email is already registered.",
                "error"
            )

            return render_template(
                "register.html"
            )


        hashed_password = generate_password_hash(
            password
        )


        cursor.execute("""
            INSERT INTO users
            (
                name,
                email,
                phone,
                password,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)

        """, (
            name,
            email,
            phone,
            hashed_password,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))


        conn.commit()


        user_id = cursor.lastrowid


        conn.close()


        session.clear()

        session["user_id"] = user_id

        session["user_name"] = name

        session["user_email"] = email


        return redirect(
            url_for("dashboard")
        )


    return render_template(
        "register.html"
    )


# =========================================================
# CUSTOMER LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        if not email or not password:

            flash(
                "Please enter email and password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        conn = get_db()

        cursor = conn.cursor()


        cursor.execute("""
            SELECT *
            FROM users
            WHERE LOWER(email) = ?
        """, (
            email,
        ))


        user = cursor.fetchone()


        conn.close()


        if not user:

            flash(
                "Invalid email or password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        try:

            password_valid = check_password_hash(
                user["password"],
                password
            )

        except Exception:

            password_valid = (
                user["password"] == password
            )


        if not password_valid:

            flash(
                "Invalid email or password.",
                "error"
            )

            return render_template(
                "login.html"
            )


        session.clear()

        session["user_id"] = user["id"]

        session["user_name"] = user["name"]

        session["user_email"] = user["email"]


        return redirect(
            url_for("dashboard")
        )


    return render_template(
        "login.html"
    )


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    ))


    user = cursor.fetchone()


    cursor.execute("""
        SELECT

            bookings.*,

            drivers.name AS driver_name,

            drivers.rating AS driver_rating

        FROM bookings

        LEFT JOIN drivers
        ON bookings.driver_id = drivers.id

        WHERE bookings.user_id = ?

        ORDER BY bookings.id DESC

        LIMIT 5

    """, (
        session["user_id"],
    ))


    bookings = cursor.fetchall()


    conn.close()


    return render_template(
        "dashboard.html",
        user=user,
        bookings=bookings
    )


# =========================================================
# BOOK DRIVER
# =========================================================

@app.route(
    "/book-driver",
    methods=["GET", "POST"]
)
@login_required
def book_driver():

    if request.method == "POST":

        pickup = request.form.get(
            "pickup",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        date = request.form.get(
            "date",
            ""
        ).strip()

        time = request.form.get(
            "time",
            ""
        ).strip()

        vehicle = request.form.get(
            "vehicle",
            "Car"
        ).strip()


        if not pickup:

            flash(
                "Please enter pickup location.",
                "error"
            )

            return render_template(
                "book-driver.html"
            )


        if not destination:

            flash(
                "Please enter destination.",
                "error"
            )

            return render_template(
                "book-driver.html"
            )


        if not date:

            flash(
                "Please select a date.",
                "error"
            )

            return render_template(
                "book-driver.html"
            )


        if not time:

            flash(
                "Please select a time.",
                "error"
            )

            return render_template(
                "book-driver.html"
            )


        conn = get_db()

        cursor = conn.cursor()


        cursor.execute("""
            INSERT INTO bookings
            (
                user_id,
                driver_id,
                pickup,
                destination,
                date,
                time,
                vehicle,
                status,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (
            session["user_id"],
            None,
            pickup,
            destination,
            date,
            time,
            vehicle,
            "Pending",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))


        conn.commit()


        booking_id = cursor.lastrowid


        conn.close()


        return redirect(
            url_for(
                "available_drivers",
                booking_id=booking_id
            )
        )


    return render_template(
        "book-driver.html"
    )


# =========================================================
# AVAILABLE DRIVERS
# =========================================================

@app.route("/available-drivers")
@login_required
def available_drivers():

    booking_id = request.args.get(
        "booking_id",
        type=int
    )


    if not booking_id:

        flash(
            "Booking information is missing.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM bookings

        WHERE
            id = ?

            AND user_id = ?

    """, (
        booking_id,
        session["user_id"]
    ))


    booking = cursor.fetchone()


    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    # Only approved drivers are shown

    cursor.execute("""
        SELECT *
        FROM drivers

        WHERE
            status = 'Available'

            AND verification_status = 'Approved'

        ORDER BY
            rating DESC,
            distance ASC

    """)


    drivers = cursor.fetchall()


    conn.close()


    return render_template(
        "available-drivers.html",
        booking=booking,
        drivers=drivers
    )


# =========================================================
# CUSTOMER SELECT DRIVER
# =========================================================

@app.route(
    "/select-driver/<int:driver_id>",
    methods=["POST"]
)
@login_required
def select_driver(driver_id):

    booking_id = request.form.get(
        "booking_id",
        type=int
    )


    if not booking_id:

        flash(
            "Booking information is missing.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM drivers

        WHERE id = ?

    """, (
        driver_id,
    ))


    driver = cursor.fetchone()


    if not driver:

        conn.close()

        flash(
            "Driver not found.",
            "error"
        )

        return redirect(
            url_for(
                "available_drivers",
                booking_id=booking_id
            )
        )


    if driver["verification_status"] != "Approved":

        conn.close()

        flash(
            "This driver is not verified.",
            "error"
        )

        return redirect(
            url_for(
                "available_drivers",
                booking_id=booking_id
            )
        )


    cursor.execute("""
        SELECT *
        FROM bookings

        WHERE
            id = ?

            AND user_id = ?

    """, (
        booking_id,
        session["user_id"]
    ))


    booking = cursor.fetchone()


    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    if driver["status"] != "Available":

        conn.close()

        flash(
            "Sorry, this driver is no longer available.",
            "error"
        )

        return redirect(
            url_for(
                "available_drivers",
                booking_id=booking_id
            )
        )


    # Send request to driver

    cursor.execute("""
        UPDATE bookings

        SET
            driver_id = ?,
            status = 'Pending'

        WHERE
            id = ?

            AND user_id = ?

    """, (
        driver_id,
        booking_id,
        session["user_id"]
    ))


    # Driver becomes requested

    cursor.execute("""
        UPDATE drivers

        SET status = 'Requested'

        WHERE id = ?

    """, (
        driver_id,
    ))


    conn.commit()

    conn.close()


    flash(
        "Booking request sent to the driver. Waiting for driver approval.",
        "success"
    )


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# BOOKING CONFIRMATION
# =========================================================

@app.route(
    "/booking-confirmation/<int:booking_id>"
)
@login_required
def booking_confirmation(booking_id):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM bookings

        WHERE
            id = ?

            AND user_id = ?

    """, (
        booking_id,
        session["user_id"]
    ))


    booking = cursor.fetchone()


    if not booking:

        conn.close()

        flash(
            "Booking not found.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )


    driver = None


    if booking["driver_id"]:

        cursor.execute("""
            SELECT *
            FROM drivers

            WHERE id = ?

        """, (
            booking["driver_id"],
        ))


        driver = cursor.fetchone()


    conn.close()


    return render_template(
        "booking-confirmation.html",
        booking=booking,
        driver=driver
    )


# =========================================================
# BOOKING HISTORY
# =========================================================

@app.route("/booking-history")
@login_required
def booking_history():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            bookings.*,

            drivers.name AS driver_name,

            drivers.rating AS driver_rating

        FROM bookings

        LEFT JOIN drivers
        ON bookings.driver_id = drivers.id

        WHERE bookings.user_id = ?

        ORDER BY bookings.id DESC

    """, (
        session["user_id"],
    ))


    bookings = cursor.fetchall()


    conn.close()


    return render_template(
        "booking-history.html",
        bookings=bookings
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
@login_required
def profile():

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM users

        WHERE id = ?

    """, (
        session["user_id"],
    ))


    user = cursor.fetchone()


    conn.close()


    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# DRIVER REGISTER
# =========================================================

@app.route(
    "/driver-register",
    methods=["GET", "POST"]
)
def driver_register():

    if request.method == "POST":

        # -------------------------------------------------
        # FORM DATA
        # -------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        license_number = request.form.get(
            "license_number",
            ""
        ).strip().upper()

        vehicle_type = request.form.get(
            "vehicle_type",
            ""
        ).strip()

        vehicle_number = request.form.get(
            "vehicle_number",
            ""
        ).strip().upper()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # -------------------------------------------------
        # FILES
        # -------------------------------------------------

        license_file = request.files.get(
            "license_proof"
        )

        id_file = request.files.get(
            "id_proof"
        )


        # -------------------------------------------------
        # BASIC VALIDATION
        # -------------------------------------------------

        if not name:

            flash(
                "Please enter your full name.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not email:

            flash(
                "Please enter your email address.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not phone or len(phone) != 10:

            flash(
                "Please enter a valid 10-digit phone number.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not license_number:

            flash(
                "Please enter your driving license number.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not license_file or not license_file.filename:

            flash(
                "Please upload your driving license proof.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not id_file or not id_file.filename:

            flash(
                "Please upload your ID proof.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not allowed_file(
            license_file.filename
        ):

            flash(
                "License proof must be JPG, JPEG, PNG or PDF.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not allowed_file(
            id_file.filename
        ):

            flash(
                "ID proof must be JPG, JPEG, PNG or PDF.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not vehicle_type:

            flash(
                "Please select your vehicle type.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not vehicle_number:

            flash(
                "Please enter your vehicle number.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if not password:

            flash(
                "Please create a password.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        # -------------------------------------------------
        # DATABASE CHECK
        # -------------------------------------------------

        conn = get_db()

        cursor = conn.cursor()


        # Same email cannot be customer

        cursor.execute("""
            SELECT id
            FROM users

            WHERE LOWER(email) = ?

        """, (
            email,
        ))


        existing_user = cursor.fetchone()


        # Same email cannot be driver

        cursor.execute("""
            SELECT id
            FROM drivers

            WHERE LOWER(email) = ?

        """, (
            email,
        ))


        existing_driver = cursor.fetchone()


        # License cannot be registered again

        cursor.execute("""
            SELECT id
            FROM drivers

            WHERE UPPER(license_number) = ?

        """, (
            license_number,
        ))


        existing_license = cursor.fetchone()


        if existing_user:

            conn.close()

            flash(
                "This email is already registered as a customer.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if existing_driver:

            conn.close()

            flash(
                "This email is already registered as a driver.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        if existing_license:

            conn.close()

            flash(
                "This driving license is already registered.",
                "error"
            )

            return render_template(
                "driver-register.html"
            )


        # -------------------------------------------------
        # SAVE FILES
        # -------------------------------------------------

        license_extension = (
            license_file
            .filename
            .rsplit(".", 1)[1]
            .lower()
        )


        id_extension = (
            id_file
            .filename
            .rsplit(".", 1)[1]
            .lower()
        )


        license_filename = (
            "license_"
            + uuid.uuid4().hex
            + "."
            + license_extension
        )


        id_filename = (
            "id_"
            + uuid.uuid4().hex
            + "."
            + id_extension
        )


        license_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            secure_filename(
                license_filename
            )
        )


        id_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            secure_filename(
                id_filename
            )
        )


        license_file.save(
            license_path
        )

        id_file.save(
            id_path
        )


        # -------------------------------------------------
        # CREATE DRIVER ACCOUNT
        # -------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )


        cursor.execute("""
            INSERT INTO drivers
            (
                name,
                phone,
                rating,
                experience,
                distance,
                status,
                email,
                password,
                license_number,
                license_proof,
                id_proof,
                vehicle_type,
                vehicle_number,
                verification_status
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )

        """, (

            name,

            phone,

            4.8,

            0,

            0,

            "Available",

            email,

            hashed_password,

            license_number,

            license_filename,

            id_filename,

            vehicle_type,

            vehicle_number,

            "Pending Verification"

        ))


        conn.commit()

        conn.close()


        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        flash(
            "Registration submitted successfully! Your documents are now pending verification.",
            "success"
        )


        return redirect(
            url_for("driver_login")
        )


    return render_template(
        "driver-register.html"
    )


# =========================================================
# DRIVER LOGIN
# =========================================================

@app.route(
    "/driver-login",
    methods=["GET", "POST"]
)
def driver_login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        if not email or not password:

            flash(
                "Please enter driver email and password.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        conn = get_db()

        cursor = conn.cursor()


        cursor.execute("""
            SELECT *
            FROM drivers

            WHERE LOWER(email) = ?

        """, (
            email,
        ))


        driver = cursor.fetchone()


        conn.close()


        if not driver:

            flash(
                "Invalid driver email or password.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        # =================================================
        # VERIFICATION CHECK
        # =================================================

        verification_status = (
            driver["verification_status"]
            or "Pending Verification"
        )


        if verification_status == "Pending Verification":

            flash(
                "Your driver account is pending verification. Please wait for admin approval.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        if verification_status == "Rejected":

            flash(
                "Your driver application has been rejected. Please contact the admin.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        if verification_status != "Approved":

            flash(
                "Your driver account is not activated yet.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        # =================================================
        # PASSWORD CHECK
        # =================================================

        try:

            password_valid = check_password_hash(
                driver["password"],
                password
            )

        except Exception:

            password_valid = (
                driver["password"] == password
            )


        if not password_valid:

            flash(
                "Invalid driver email or password.",
                "error"
            )

            return render_template(
                "driver-login.html"
            )


        # =================================================
        # DRIVER SESSION
        # =================================================

        session.clear()

        session["driver_id"] = driver["id"]

        session["driver_name"] = driver["name"]

        session["driver_email"] = driver["email"]


        return redirect(
            url_for("driver_dashboard")
        )


    return render_template(
        "driver-login.html"
    )


# =========================================================
# DRIVER DOCUMENT VIEW
# =========================================================

@app.route(
    "/driver-document/<filename>"
)
@driver_login_required
def driver_document(filename):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            license_proof,
            id_proof

        FROM drivers

        WHERE id = ?

    """, (
        session["driver_id"],
    ))


    driver = cursor.fetchone()


    conn.close()


    if not driver:

        return "Document not found", 404


    if filename not in [
        driver["license_proof"],
        driver["id_proof"]
    ]:

        return "Access denied", 403


    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================================================
# DRIVER DASHBOARD
# =========================================================

@app.route("/driver-dashboard")
@driver_login_required
def driver_dashboard():

    conn = get_db()

    cursor = conn.cursor()


    # Driver details

    cursor.execute("""
        SELECT *
        FROM drivers

        WHERE id = ?

    """, (
        session["driver_id"],
    ))


    driver = cursor.fetchone()


    # All bookings for this driver

    cursor.execute("""
        SELECT

            bookings.*,

            users.name AS customer_name,

            users.phone AS customer_phone,

            users.email AS customer_email

        FROM bookings

        LEFT JOIN users
        ON bookings.user_id = users.id

        WHERE bookings.driver_id = ?

        ORDER BY bookings.id DESC

    """, (
        session["driver_id"],
    ))


    bookings = cursor.fetchall()


    # Notification count

    cursor.execute("""
        SELECT COUNT(*) AS count

        FROM bookings

        WHERE
            driver_id = ?

            AND status = 'Pending'

    """, (
        session["driver_id"],
    ))


    notification_count = (
        cursor.fetchone()["count"]
    )


    # Pending bookings

    cursor.execute("""
        SELECT

            bookings.*,

            users.name AS customer_name,

            users.phone AS customer_phone,

            users.email AS customer_email

        FROM bookings

        LEFT JOIN users
        ON bookings.user_id = users.id

        WHERE

            bookings.driver_id = ?

            AND bookings.status = 'Pending'

        ORDER BY bookings.id DESC

    """, (
        session["driver_id"],
    ))


    pending_bookings = cursor.fetchall()


    conn.close()


    return render_template(
        "driver-dashboard.html",

        driver=driver,

        bookings=bookings,

        pending_bookings=pending_bookings,

        notification_count=notification_count
    )


# =========================================================
# DRIVER ACCEPT BOOKING
# =========================================================

@app.route(
    "/driver/accept/<int:booking_id>",
    methods=["POST"]
)
@driver_login_required
def driver_accept_booking(booking_id):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM bookings

        WHERE

            id = ?

            AND driver_id = ?

            AND status = 'Pending'

    """, (
        booking_id,
        session["driver_id"]
    ))


    booking = cursor.fetchone()


    if not booking:

        conn.close()

        flash(
            "Booking request is no longer available.",
            "error"
        )

        return redirect(
            url_for("driver_dashboard")
        )


    # Accept booking

    cursor.execute("""
        UPDATE bookings

        SET status = 'Confirmed'

        WHERE

            id = ?

            AND driver_id = ?

    """, (
        booking_id,
        session["driver_id"]
    ))


    # Driver becomes booked

    cursor.execute("""
        UPDATE drivers

        SET status = 'Booked'

        WHERE id = ?

    """, (
        session["driver_id"],
    ))


    conn.commit()

    conn.close()


    flash(
        "Booking accepted successfully!",
        "success"
    )


    return redirect(
        url_for("driver_dashboard")
    )


# =========================================================
# DRIVER REJECT BOOKING
# =========================================================

@app.route(
    "/driver/reject/<int:booking_id>",
    methods=["POST"]
)
@driver_login_required
def driver_reject_booking(booking_id):

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *

        FROM bookings

        WHERE

            id = ?

            AND driver_id = ?

            AND status = 'Pending'

    """, (
        booking_id,
        session["driver_id"]
    ))


    booking = cursor.fetchone()


    if not booking:

        conn.close()

        flash(
            "Booking request is no longer available.",
            "error"
        )

        return redirect(
            url_for("driver_dashboard")
        )


    # Reject booking

    cursor.execute("""
        UPDATE bookings

        SET
            status = 'Rejected',
            driver_id = NULL

        WHERE

            id = ?

            AND driver_id = ?

    """, (
        booking_id,
        session["driver_id"]
    ))


    # Driver becomes available

    cursor.execute("""
        UPDATE drivers

        SET status = 'Available'

        WHERE id = ?

    """, (
        session["driver_id"],
    ))


    conn.commit()

    conn.close()


    flash(
        "Booking request rejected.",
        "error"
    )


    return redirect(
        url_for("driver_dashboard")
    )


# =========================================================
# DRIVER LOGOUT
# =========================================================

@app.route("/driver-logout")
def driver_logout():

    session.clear()

    return redirect(
        url_for("driver_login")
    )


# =========================================================
# CUSTOMER LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    was_driver = (
        "driver_id" in session
    )


    session.clear()


    if was_driver:

        return redirect(
            url_for("driver_login")
        )


    return redirect(
        url_for("login")
    )


# =========================================================
# ADMIN LOGIN & DRIVER VERIFICATION
# =========================================================

ADMIN_EMAIL = "admin@actingdriver.com"
ADMIN_PASSWORD = "admin123"


def admin_login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            flash("Please login as admin.", "error")
            return redirect(url_for("admin_login"))

        return function(*args, **kwargs)

    return wrapper


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.", "error")

    return render_template("admin-login.html")


@app.route("/admin-dashboard")
@admin_login_required
def admin_dashboard():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM drivers
        ORDER BY id DESC
    """)
    drivers = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM drivers
        WHERE verification_status = 'Pending Verification'
    """)
    pending_count = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM drivers
        WHERE verification_status = 'Approved'
    """)
    approved_count = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM drivers
        WHERE verification_status = 'Rejected'
    """)
    rejected_count = cursor.fetchone()["count"]

    conn.close()

    return render_template(
        "admin-dashboard.html",
        drivers=drivers,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count
    )


@app.route("/admin/document/<int:driver_id>/<document_type>")
@admin_login_required
def admin_document(driver_id, document_type):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT license_proof, id_proof
        FROM drivers
        WHERE id = ?
    """, (driver_id,))

    driver = cursor.fetchone()
    conn.close()

    if not driver:
        return "Driver not found.", 404

    if document_type == "license":
        filename = driver["license_proof"]
    elif document_type == "id":
        filename = driver["id_proof"]
    else:
        return "Invalid document type.", 400

    if not filename:
        return "Document not available.", 404

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.isfile(filepath):
        return "Document file not found.", 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


@app.route("/admin/approve-driver/<int:driver_id>", methods=["POST"])
@admin_login_required
def admin_approve_driver(driver_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM drivers
        WHERE id = ?
    """, (driver_id,))

    driver = cursor.fetchone()

    if not driver:
        conn.close()
        flash("Driver application not found.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor.execute("""
        UPDATE drivers
        SET
            verification_status = 'Approved',
            status = 'Available'
        WHERE id = ?
    """, (driver_id,))

    conn.commit()
    conn.close()

    flash(
        f"{driver['name']} has been approved successfully.",
        "success"
    )

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reject-driver/<int:driver_id>", methods=["POST"])
@admin_login_required
def admin_reject_driver(driver_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM drivers
        WHERE id = ?
    """, (driver_id,))

    driver = cursor.fetchone()

    if not driver:
        conn.close()
        flash("Driver application not found.", "error")
        return redirect(url_for("admin_dashboard"))

    cursor.execute("""
        UPDATE drivers
        SET
            verification_status = 'Rejected',
            status = 'Unavailable'
        WHERE id = ?
    """, (driver_id,))

    conn.commit()
    conn.close()

    flash(
        f"{driver['name']} application has been rejected.",
        "success"
    )

    return redirect(url_for("admin_dashboard"))


@app.route("/admin-logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum allowed size is 5 MB.",
        "error"
    )

    return redirect(
        url_for("driver_register")
    )


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>404 - Page Not Found</title>

        <style>

            body {

                font-family: Arial, sans-serif;

                background: #f5f7ff;

                text-align: center;

                padding: 80px;
            }

            h1 {

                color: #1e293b;
            }

            a {

                display: inline-block;

                margin-top: 20px;

                padding: 12px 22px;

                background: #315bea;

                color: white;

                text-decoration: none;

                border-radius: 10px;
            }

        </style>

    </head>

    <body>

        <h1>
            404 - Page Not Found
        </h1>

        <p>
            The requested page does not exist.
        </p>

        <a href="/">
            Go Home
        </a>

    </body>

    </html>
    """, 404


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>500 - Server Error</title>

        <style>

            body {

                font-family: Arial, sans-serif;

                background: #f5f7ff;

                text-align: center;

                padding: 80px;
            }

            h1 {

                color: #dc2626;
            }

            a {

                display: inline-block;

                margin-top: 20px;

                padding: 12px 22px;

                background: #315bea;

                color: white;

                text-decoration: none;

                border-radius: 10px;
            }

        </style>

    </head>

    <body>

        <h1>
            500 - Server Error
        </h1>

        <p>
            Something went wrong on the server.
        </p>

        <a href="/">
            Go Home
        </a>

    </body>

    </html>
    """, 500


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )