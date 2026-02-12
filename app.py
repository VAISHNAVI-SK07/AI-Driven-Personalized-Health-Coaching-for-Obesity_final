from datetime import datetime, date

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

from config import config


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY

    # -----------------------------
    # Database helper
    # -----------------------------

    def get_db_connection():
        """Create a new MySQL connection."""
        return mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            auth_plugin="mysql_native_password",
        )

    # -----------------------------
    # Utility functions
    # -----------------------------

    def calculate_bmi(height_cm: float, weight_kg: float):
        """Calculate BMI and category based on height (cm) and weight (kg)."""
        if height_cm <= 0:
            return None, None
        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m**2)
        bmi = round(bmi, 2)

        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 25:
            category = "Normal"
        elif 25 <= bmi < 30:
            category = "Overweight"
        elif 30 <= bmi < 35:
            category = "Obese"
        else:
            category = "Severely Obese"

        return bmi, category

    def get_bmi_recommendations(category: str):
        """
        Simple rule-based AI for recommendations.
        Returns (weekly_food_plan, daily_workout_plan, water_target_liters, calorie_target).
        """
        # These are intentionally simple to keep it college-project friendly.
        base_plans = {
            "Underweight": {
                "food": "High-calorie nutritious foods: nuts, avocados, whole milk, lean meats, and whole grains. 5–6 small meals per day.",
                "workout": "Light strength training 3–4 days/week, focus on muscle gain, minimal cardio.",
                "water": 2.0,
                "calories": 2500,
            },
            "Normal": {
                "food": "Balanced diet: vegetables, fruits, lean protein, whole grains. Limit processed sugar and fried foods.",
                "workout": "30–45 minutes moderate exercise 5 days/week (mix of cardio and strength).",
                "water": 2.5,
                "calories": 2000,
            },
            "Overweight": {
                "food": "Calorie-controlled, high-fiber meals. Focus on vegetables, lean protein, reduce refined carbs and sugary drinks.",
                "workout": "45 minutes brisk walking/cardio 5 days/week + 2 days light strength.",
                "water": 3.0,
                "calories": 1700,
            },
            "Obese": {
                "food": "Low-calorie, nutrient-dense meals. Avoid sugary snacks and late-night eating. Smaller, frequent meals.",
                "workout": "Start with 20–30 minutes low-impact cardio (walking, cycling) 5 days/week; gradually increase.",
                "water": 3.0,
                "calories": 1500,
            },
            "Severely Obese": {
                "food": "Strict calorie deficit under medical guidance. Mostly vegetables, lean proteins, and whole grains. Avoid fried and ultra-processed foods.",
                "workout": "Very low-impact activity (short walks, chair exercises) 5–6 days/week. Increase duration slowly.",
                "water": 3.5,
                "calories": 1300,
            },
        }
        default_plan = {
            "food": "Balanced meals with vegetables, fruits, lean proteins, and whole grains.",
            "workout": "At least 30 minutes of moderate activity daily.",
            "water": 2.5,
            "calories": 2000,
        }

        plan = base_plans.get(category, default_plan)

        # Construct simple weekly and daily textual plans
        weekly_food_plan = f"Weekly Food Plan for {category}:\n- {plan['food']}\n- Spread meals evenly throughout the day.\n- Avoid excessive sugar and deep-fried foods.\n- Include seasonal fruits and vegetables."
        daily_workout_plan = f"Daily Workout Plan for {category}:\n- {plan['workout']}\n- Do a 5–10 minute warm-up and cool-down.\n- Include stretching to prevent injury."

        return weekly_food_plan, daily_workout_plan, plan["water"], plan["calories"]

    def get_today_quote():
        """Get or choose a motivational quote for today."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            today_str = date.today().isoformat()
            # Try to get a quote already marked for today
            cursor.execute(
                "SELECT id, quote_text, author FROM motivational_quotes WHERE used_date = %s LIMIT 1",
                (today_str,),
            )
            row = cursor.fetchone()
            if row:
                return row

            # Otherwise choose a random quote and mark it as used today
            cursor.execute(
                "SELECT id, quote_text, author FROM motivational_quotes ORDER BY RAND() LIMIT 1"
            )
            row = cursor.fetchone()
            if not row:
                return {
                    "id": None,
                    "quote_text": "Your health is an investment, not an expense.",
                    "author": "Unknown",
                }

            cursor.execute(
                "UPDATE motivational_quotes SET used_date = %s WHERE id = %s",
                (today_str, row["id"]),
            )
            conn.commit()
            return row
        finally:
            cursor.close()
            conn.close()

    def get_user_daily_tracking(user_id: int, on_date: date | None = None):
        """Fetch or create daily tracking record for a user."""
        if on_date is None:
            on_date = date.today()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT * FROM daily_tracking
                WHERE user_id = %s AND track_date = %s
                """,
                (user_id, on_date),
            )
            record = cursor.fetchone()
            if not record:
                # Create a blank record
                cursor.execute(
                    """
                    INSERT INTO daily_tracking
                        (user_id, track_date, water_completed, food_completed,
                         workout_completed, challenge_completed, progress_percent)
                    VALUES (%s, %s, 0, 0, 0, 0, 0)
                    """,
                    (user_id, on_date),
                )
                conn.commit()
                cursor.execute(
                    """
                    SELECT * FROM daily_tracking
                    WHERE user_id = %s AND track_date = %s
                    """,
                    (user_id, on_date),
                )
                record = cursor.fetchone()
            return record
        finally:
            cursor.close()
            conn.close()

    def update_daily_tracking(user_id: int, water: bool, food: bool, workout: bool, challenge: bool):
        """Update daily tracking flags and progress percentage."""
        on_date = date.today()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Ensure record exists
            record = get_user_daily_tracking(user_id, on_date)

            total_items = 4
            completed = sum(
                [1 if water else 0, 1 if food else 0, 1 if workout else 0, 1 if challenge else 0]
            )
            progress = int((completed / total_items) * 100)

            cursor.execute(
                """
                UPDATE daily_tracking
                SET water_completed = %s,
                    food_completed = %s,
                    workout_completed = %s,
                    challenge_completed = %s,
                    progress_percent = %s
                WHERE id = %s
                """,
                (
                    int(water),
                    int(food),
                    int(workout),
                    int(challenge),
                    progress,
                    record["id"],
                ),
            )
            conn.commit()
            return progress
        finally:
            cursor.close()
            conn.close()

    # -----------------------------
    # Decorators
    # -----------------------------

    def login_required(role="user"):
        """Simple login_required decorator for user/admin."""

        def decorator(view_func):
            def wrapper(*args, **kwargs):
                if role == "admin":
                    if not session.get("admin_id"):
                        return redirect(url_for("admin_login"))
                else:
                    if not session.get("user_id"):
                        return redirect(url_for("user_login"))
                return view_func(*args, **kwargs)

            # Preserve function name for Flask
            wrapper.__name__ = view_func.__name__
            return wrapper

        return decorator

    # -----------------------------
    # Routes: Public
    # -----------------------------

    @app.route("/")
    def index():
        """Homepage with consistency message and daily quote."""
        quote = get_today_quote()
        consistency_message = (
            "Consistency beats intensity: small healthy choices every day lead to big changes."
        )
        return render_template("index.html", quote=quote, consistency_message=consistency_message)

    # -----------------------------
    # Authentication Routes
    # -----------------------------

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
                admin = cursor.fetchone()
                if admin and check_password_hash(admin["password_hash"], password):
                    session.clear()
                    session["admin_id"] = admin["id"]
                    session["admin_email"] = admin["email"]

                    # Log login activity (reuse login_logs table)
                    cursor.execute(
                        """
                        INSERT INTO login_logs (user_id, is_admin, login_time)
                        VALUES (%s, %s, %s)
                        """,
                        (None, 1, datetime.utcnow()),
                    )
                    conn.commit()
                    return redirect(url_for("admin_dashboard"))
                else:
                    flash("Invalid admin credentials.", "danger")
            finally:
                cursor.close()
                conn.close()

        return render_template("admin_login.html")

    @app.route("/user/login", methods=["GET", "POST"])
    def user_login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if user and check_password_hash(user["password_hash"], password):
                    session.clear()
                    session["user_id"] = user["id"]
                    session["user_name"] = user["full_name"]

                    # log login activity
                    cursor.execute(
                        """
                        INSERT INTO login_logs (user_id, is_admin, login_time)
                        VALUES (%s, %s, %s)
                        """,
                        (user["id"], 0, datetime.utcnow()),
                    )
                    conn.commit()
                    return redirect(url_for("user_dashboard"))
                else:
                    flash("Invalid email or password.", "danger")
            finally:
                cursor.close()
                conn.close()

        return render_template("user_login.html")

    @app.route("/user/register", methods=["GET", "POST"])
    def user_register():
        if request.method == "POST":
            full_name = request.form.get("full_name")
            email = request.form.get("email")
            password = request.form.get("password")

            password_hash = generate_password_hash(password)

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            try:
                # Check if user already exists
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("Email already registered. Please login instead.", "warning")
                    return redirect(url_for("user_login"))

                cursor.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash, target_status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (full_name, email, password_hash, "Ongoing"),
                )
                conn.commit()
                flash("Registration successful. Please login.", "success")
                return redirect(url_for("user_login"))
            finally:
                cursor.close()
                conn.close()

        return render_template("user_register.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    # -----------------------------
    # Admin Dashboard
    # -----------------------------

    @app.route("/admin/dashboard")
    @login_required(role="admin")
    def admin_dashboard():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Total users
            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            # Recent login logs
            cursor.execute(
                """
                SELECT ll.*, u.full_name, u.email
                FROM login_logs ll
                LEFT JOIN users u ON ll.user_id = u.id
                ORDER BY ll.login_time DESC
                LIMIT 20
                """
            )
            login_logs = cursor.fetchall()

            # User BMI and target status
            cursor.execute(
                """
                SELECT u.id, u.full_name, u.email, u.target_status,
                       br.height_cm, br.weight_kg, br.bmi_value, br.category,
                       br.created_at
                FROM users u
                LEFT JOIN bmi_records br
                    ON br.id = (
                        SELECT id FROM bmi_records
                        WHERE user_id = u.id
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                ORDER BY u.full_name ASC
                """
            )
            user_bmi_records = cursor.fetchall()

            # Daily challenge completion summary (today)
            today = date.today()
            cursor.execute(
                """
                SELECT u.full_name, dt.*
                FROM daily_tracking dt
                JOIN users u ON dt.user_id = u.id
                WHERE dt.track_date = %s
                ORDER BY u.full_name ASC
                """,
                (today,),
            )
            daily_tracking = cursor.fetchall()

            return render_template(
                "admin_dashboard.html",
                total_users=total_users,
                login_logs=login_logs,
                user_bmi_records=user_bmi_records,
                daily_tracking=daily_tracking,
            )
        finally:
            cursor.close()
            conn.close()

    @app.route("/admin/message", methods=["POST"])
    @login_required(role="admin")
    def admin_send_message():
        user_id = request.form.get("user_id")
        message = request.form.get("message")
        if not user_id or not message:
            flash("User and message are required.", "warning")
            return redirect(url_for("admin_dashboard"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO admin_messages (admin_id, user_id, message, created_at, is_read)
                VALUES (%s, %s, %s, %s, 0)
                """,
                (session.get("admin_id"), user_id, message, datetime.utcnow()),
            )
            conn.commit()
            flash("Message sent to user.", "success")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/update_target", methods=["POST"])
    @login_required(role="admin")
    def admin_update_target():
        user_id = request.form.get("user_id")
        target_status = request.form.get("target_status")

        if not user_id or not target_status:
            flash("User and target status are required.", "warning")
            return redirect(url_for("admin_dashboard"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE users SET target_status = %s WHERE id = %s",
                (target_status, user_id),
            )
            conn.commit()
            flash("User target status updated.", "success")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for("admin_dashboard"))

    # -----------------------------
    # User Dashboard & BMI Logic
    # -----------------------------

    @app.route("/user/dashboard", methods=["GET", "POST"])
    @login_required(role="user")
    def user_dashboard():
        user_id = session.get("user_id")
        bmi_result = None
        bmi_category = None
        weekly_food_plan = None
        daily_workout_plan = None
        water_target = None
        calorie_target = None
        improvement_status = None
        latest_bmi_record = None

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            if request.method == "POST":
                try:
                    height_cm = float(request.form.get("height_cm"))
                    weight_kg = float(request.form.get("weight_kg"))
                except (TypeError, ValueError):
                    flash("Please enter valid height and weight.", "danger")
                    return redirect(url_for("user_dashboard"))

                bmi_result, bmi_category = calculate_bmi(height_cm, weight_kg)
                if bmi_result is None:
                    flash("Invalid height provided.", "danger")
                    return redirect(url_for("user_dashboard"))

                # Insert BMI record
                cursor.execute(
                    """
                    INSERT INTO bmi_records
                        (user_id, height_cm, weight_kg, bmi_value, category, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, height_cm, weight_kg, bmi_result, bmi_category, datetime.utcnow()),
                )
                conn.commit()

            # Fetch the latest BMI record
            cursor.execute(
                """
                SELECT * FROM bmi_records
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 2
                """,
                (user_id,),
            )
            bmi_records = cursor.fetchall()
            if bmi_records:
                latest_bmi_record = bmi_records[0]
                bmi_result = latest_bmi_record["bmi_value"]
                bmi_category = latest_bmi_record["category"]

                # Improvement analytics: compare latest with previous
                if len(bmi_records) == 2:
                    previous_bmi = bmi_records[1]["bmi_value"]
                    if bmi_result < previous_bmi:
                        improvement_status = "improved"
                    elif bmi_result > previous_bmi:
                        improvement_status = "worsened"
                    else:
                        improvement_status = "stable"

                # Get AI recommendations
                (
                    weekly_food_plan,
                    daily_workout_plan,
                    water_target,
                    calorie_target,
                ) = get_bmi_recommendations(bmi_category)

            # Fetch user profile & target status
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            # Daily tracking info
            tracking = get_user_daily_tracking(user_id)

            # Admin messages
            cursor.execute(
                """
                SELECT * FROM admin_messages
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (user_id,),
            )
            admin_messages = cursor.fetchall()

            # Motivational quote
            quote = get_today_quote()

            # Motivational message based on target completion
            motivational_message = None
            if user.get("target_status") == "Completed":
                motivational_message = "Amazing job completing your target! Keep up the great work and maintain your healthy habits."
            else:
                motivational_message = "You are on your journey. Stay consistent today – even a small step counts."

            # Improvement analytics message
            improvement_message = None
            if improvement_status == "improved":
                improvement_message = "Your BMI has improved compared to your last record. Fantastic progress!"
            elif improvement_status == "worsened":
                improvement_message = (
                    "Your BMI has increased compared to your last record. Consider tightening your food plan "
                    "and staying more consistent with workouts."
                )
            elif improvement_status == "stable":
                improvement_message = "Your BMI is stable. Keep following your plan to see gradual improvements."

            return render_template(
                "user_dashboard.html",
                user=user,
                bmi_result=bmi_result,
                bmi_category=bmi_category,
                weekly_food_plan=weekly_food_plan,
                daily_workout_plan=daily_workout_plan,
                water_target=water_target,
                calorie_target=calorie_target,
                tracking=tracking,
                admin_messages=admin_messages,
                quote=quote,
                motivational_message=motivational_message,
                improvement_message=improvement_message,
            )
        finally:
            cursor.close()
            conn.close()

    # -----------------------------
    # Daily Tracking (AJAX)
    # -----------------------------

    @app.route("/user/daily-tracking", methods=["POST"])
    @login_required(role="user")
    def update_tracking_route():
        user_id = session.get("user_id")
        data = request.get_json() or {}

        water = bool(data.get("water_completed"))
        food = bool(data.get("food_completed"))
        workout = bool(data.get("workout_completed"))
        challenge = bool(data.get("challenge_completed"))

        progress = update_daily_tracking(user_id, water, food, workout, challenge)

        # Simple encouragement message based on progress
        if progress == 100:
            message = "Congratulations! You have completed all your health goals for today."
        elif progress >= 50:
            message = "Great job. You're more than halfway there – keep going!"
        else:
            message = "Good start! Make a small healthy choice right now to move closer to your goal."

        return jsonify({"success": True, "progress": progress, "message": message})

    # -----------------------------
    # Simple health reminders (static, simulated)
    # -----------------------------

    @app.context_processor
    def inject_reminders():
        """Inject reminder text into all templates."""
        reminders = [
            "Drink a glass of water now.",
            "Take a 5-minute walk or stretch break.",
            "Review your meal plan for today.",
        ]
        return {"global_reminders": reminders}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

