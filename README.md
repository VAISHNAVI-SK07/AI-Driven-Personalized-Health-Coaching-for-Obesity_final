# AI-Driven Platform for Personalized Health Coaching for Obesity

Full‑stack web application using **Flask (Python)**, **MySQL**, and a simple **rule‑based AI** for personalized obesity coaching.

## 1. Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Bootstrap 5, vanilla JavaScript
- **Database**: MySQL
- **AI/ML**: Rule-based BMI classification + recommendations

## 2. Project Structure

- `app.py` – main Flask application (routes, logic)
- `config.py` – configuration for secret key and DB connection
- `requirements.txt` – Python dependencies
- `mysql_schema.sql` – database schema + sample data
- `templates/` – HTML templates (Jinja2)
  - `base.html`, `index.html`
  - `admin_login.html`, `user_login.html`, `user_register.html`
  - `admin_dashboard.html`, `user_dashboard.html`
- `static/`
  - `css/main.css` – custom styling
  - `js/main.js` – daily tracking AJAX logic

## 3. Features Overview

- **Authentication**
  - Separate admin and user logins.
  - Single predefined admin account (in DB).
  - Multiple users can register and log in.
  - Passwords stored using secure hashing (Werkzeug).
  - Login timestamps stored in `login_logs`.

- **Admin Dashboard**
  - Total registered users.
  - View recent login activity (admin + users).
  - View each user's latest BMI, category, and target status.
  - Update user target goals (Completed / Ongoing / Not Completed).
  - Send motivational messages to users (`admin_messages` table).
  - See daily challenge completion per user (`daily_tracking`).

- **User Dashboard**
  - Input height (cm) & weight (kg) and calculate BMI.
  - Obesity classification:
    - Underweight, Normal, Overweight, Obese, Severely Obese.
  - Color-coded BMI badges.
  - AI-generated:
    - Weekly food plan.
    - Daily workout plan.
    - Water intake target (L/day).
    - Daily calorie target (kcal).
  - Daily tracking:
    - Water intake, food target, workout, daily challenge.
    - Progress bar with percentage and dynamic motivational messages.
  - Admin messages displayed in dashboard.
  - Daily motivational quote (`motivational_quotes` table).
  - Improvement analytics if BMI improves/worsens over time.

- **Reminders**
  - In‑app reminders (no external SMS/email).
  - Reminders to drink water, work out, and follow meal plan shown on UI.

## 4. Setup Instructions (Local)

### 4.1. Install Python and MySQL

1. Install **Python 3.10+**.
2. Install **MySQL Server** (and optionally MySQL Workbench).

### 4.2. Create Virtual Environment and Install Dependencies

Open a terminal in the project folder (where `app.py` is located):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4.3. Create Database and Tables

1. Start MySQL and log in:

```sql
mysql -u root -p
```

2. Run the schema script (from MySQL CLI or Workbench):

```sql
SOURCE path/to/mysql_schema.sql;
```

This will:

- Create database `ai_obesity_coaching`.
- Create all required tables.
- Insert:
  - One admin account.
  - Two sample users.
  - Some BMI history.
  - Sample daily tracking rows.
  - Motivational quotes.

### 4.4. Configure Database Connection (Optional)

Open `config.py` and adjust if necessary:

- `DB_HOST` (default: `"localhost"`)
- `DB_PORT` (default: `3306`)
- `DB_USER` (default: `"root"`)
- `DB_PASSWORD` – set your MySQL root password if needed.
- `DB_NAME` (default: `"ai_obesity_coaching"`)

For more secure/production‑like usage, set environment variables:

- `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

### 4.5. Run the Flask App

With the virtual environment active:

```bash
python app.py
```

Open your browser and go to:

```text
http://127.0.0.1:5000/
```

### 4.6. Login Credentials

- **Admin**
  - Email: `admin@healthcoach.com`
  - Password: `Admin@123`

- **Sample Users**
  - Email: `john@example.com`, Password: `User@123`
  - Email: `jane@example.com`, Password: `User@123`

You can also register new user accounts via the registration form.

## 5. Notes for College Project Submission

- The AI logic is **rule‑based** (BMI → category → recommendations), which is easy to explain in a report and presentation.
- The app demonstrates:
  - Full CRUD interaction with a relational database (MySQL).
  - Authentication and authorization (admin vs user).
  - Basic analytics (BMI improvement/worsening over time).
  - Daily tracking, progress bar, and motivational system.
- You can extend it further by:
  - Adding charts (e.g., Chart.js) for BMI history.
  - Exporting user progress reports.
  - Connecting to real ML models in the future.

