from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, scan, logs, dashboard, members,timetable,academic_calendar

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include all router files
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(logs.router)
app.include_router(dashboard.router)
app.include_router(members.router)
app.include_router(timetable.router)
app.include_router(academic_calendar.router)

@app.get("/")
def home():
    return {"message": "Library Access System API Working 🎉"}


# from fastapi import FastAPI
# from pydantic import BaseModel
# import mysql.connector
# from datetime import datetime
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# # Enable CORS for all
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ---------------------------------
# # DATABASE CONNECTION
# # ---------------------------------
# def get_db_connection():
#     print("\n🔌 Connecting to MySQL...")
#     try:
#         conn = mysql.connector.connect(
#             host="127.0.0.1",
#             user="root",
#             password="2005",
#             database="library_access",
#             connection_timeout=5,
#             auth_plugin="mysql_native_password",
#             use_pure=True
#         )
#         print("✅ MySQL Connected Successfully")
#         return conn
#     except mysql.connector.Error as e:
#         print("❌ MySQL Connection Error:", e)
#         return None


# # ---------------------------------
# # REQUEST MODELS
# # ---------------------------------
# class ScanRequest(BaseModel):
#     user_id: str

# class AdminLoginRequest(BaseModel):
#     username: str
#     password: str


# # ---------------------------------
# # DATABASE CHECK FUNCTIONS
# # ---------------------------------
# def check_teacher(user_id):
#     print(f"👨‍🏫 Checking TEACHER: {user_id}")
#     conn = get_db_connection()
#     if conn is None:
#         return None

#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM teachers WHERE teacher_id=%s LIMIT 1", (user_id,))
#     result = cursor.fetchone()
#     conn.close()
#     return result


# def check_student(user_id):
#     print(f"🎓 Checking STUDENT: {user_id}")
#     conn = get_db_connection()
#     if conn is None:
#         return None

#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM students WHERE student_id=%s LIMIT 1", (user_id,))
#     result = cursor.fetchone()
#     conn.close()
#     return result


# def check_timetable(dept, year, div):
#     conn = get_db_connection()
#     if conn is None:
#         return None

#     cursor = conn.cursor(dictionary=True)
#     now = datetime.now()

#     query = """
#         SELECT * FROM timetable
#         WHERE department=%s AND year=%s AND division=%s
#         AND day_of_week=%s
#         AND start_time <= %s AND end_time >= %s
#         LIMIT 1
#     """

#     cursor.execute(query, (
#         dept, year, div,
#         now.strftime("%A"),
#         now.strftime("%H:%M:%S"),
#         now.strftime("%H:%M:%S")
#     ))

#     lecture = cursor.fetchone()
#     conn.close()
#     return lecture


# def insert_log(user_id, role, action, status, remarks):
#     print(f"📝 LOGGING → {user_id}, {role}, {action}, {status}")

#     conn = get_db_connection()
#     if conn is None:
#         return

#     cursor = conn.cursor()
#     cursor.execute(
#         "INSERT INTO logs (user_id, role, action, status, remarks) VALUES (%s, %s, %s, %s, %s)",
#         (user_id, role, action, status, remarks)
#     )
#     conn.commit()
#     conn.close()


# def get_last_action(user_id):
#     conn = get_db_connection()
#     if conn is None:
#         return None

#     cursor = conn.cursor(dictionary=True)
#     cursor.execute(
#         "SELECT action FROM logs WHERE user_id=%s ORDER BY scan_time DESC LIMIT 1",
#         (user_id,)
#     )
#     row = cursor.fetchone()
#     conn.close()

#     return row["action"] if row else None


# # ---------------------------------
# # ADMIN LOGIN API
# # ---------------------------------
# @app.post("/admin/login")
# def admin_login(data: AdminLoginRequest):
#     conn = get_db_connection()
#     if conn is None:
#         return {"status": "error", "message": "DB connection failed"}

#     cursor = conn.cursor(dictionary=True)
#     cursor.execute(
#         "SELECT * FROM admin WHERE username=%s AND password_hash=%s LIMIT 1",
#         (data.username, data.password)
#     )
#     admin = cursor.fetchone()
#     conn.close()

#     if admin:
#         return {
#             "status": "success",
#             "message": "Admin login successful",
#             "admin_id": admin["admin_id"],
#             "username": admin["username"],
#             "role": admin["role"]
#         }

#     return {"status": "failed", "message": "Invalid username or password"}


# # ---------------------------------
# # HOME API
# # ---------------------------------
# @app.get("/")
# def home():
#     return {"message": "Library Access System API Working 🎉"}


# # ---------------------------------
# # SCAN API (Entry/Exit + Timetable check)
# # ---------------------------------
# @app.post("/scan")
# def scan_id(data: ScanRequest):
#     user_id = data.user_id

#     print("\n----------------------")
#     print("🔔 SCAN RECEIVED:", user_id)
#     print("----------------------")

#     last_action = get_last_action(user_id)
#     next_action = "exit" if last_action == "entry" else "entry"

#     # Teacher check
#     teacher = check_teacher(user_id)
#     if teacher:
#         insert_log(user_id, "teacher", next_action, "allowed", f"Teacher {next_action}")
#         return {
#             "status": "Access Granted",
#             "role": "teacher",
#             "action": next_action,
#             "message": f"Teacher {next_action.capitalize()} Successful"
#         }

#     # Student check
#     student = check_student(user_id)
#     if student:
#         if next_action == "entry":  # Only check timetable on entry
#             lecture = check_timetable(student["department"], student["year"], student["division"])
#             if lecture:
#                 insert_log(user_id, "student", next_action, "alert_sent", "Skipping class detected")
#                 return {
#                     "status": "Access Granted (Skipping Class Alert!)",
#                     "subject": lecture["subject"],
#                     "teacher": lecture["teacher_id"],
#                     "time": f"{lecture['start_time']} - {lecture['end_time']}"
#                 }

#         insert_log(user_id, "student", next_action, "allowed", f"Student {next_action}")
#         return {
#             "status": "Access Granted",
#             "role": "student",
#             "action": next_action,
#             "message": f"Student {next_action.capitalize()} Successful"
#         }

#     # Unknown user
#     insert_log(user_id, "unknown", "entry", "denied", "Invalid ID")
#     return {"status": "Access Denied", "message": "User not found"}


# # ---------------------------------
# # ADMIN LOGS API
# # ---------------------------------
# @app.get("/admin/logs")
# def get_logs():
#     conn = get_db_connection()
#     if conn is None:
#         return []

#     cursor = conn.cursor(dictionary=True)
#     cursor.execute("SELECT * FROM logs ORDER BY scan_time DESC")
#     logs = cursor.fetchall()
#     conn.close()
#     return logs


# # ---------------------------------
# # ADMIN DASHBOARD STATS API
# # ---------------------------------
# @app.get("/admin/stats")
# def dashboard_stats():
#     conn = get_db_connection()
#     if conn is None:
#         return {"status": "error", "message": "DB connection failed"}

#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT COUNT(*) AS count FROM logs WHERE role='student' AND action='entry'")
#     students_inside = cursor.fetchone()["count"]

#     cursor.execute("SELECT COUNT(*) AS count FROM logs WHERE role='teacher' AND action='entry'")
#     teachers_inside = cursor.fetchone()["count"]

#     cursor.execute("""
#         SELECT COUNT(*) AS count FROM logs 
#         WHERE status='alert_sent' AND DATE(scan_time)=CURDATE()
#     """)
#     alerts_today = cursor.fetchone()["count"]

#     cursor.execute("SELECT COUNT(*) AS count FROM logs WHERE DATE(scan_time)=CURDATE()")
#     total_today = cursor.fetchone()["count"]

#     conn.close()

#     return {
#         "students_inside": students_inside,
#         "teachers_inside": teachers_inside,
#         "alerts_today": alerts_today,
#         "total_entries_today": total_today
#     }

# # --- Dashboard summary endpoint ---
# @app.get("/admin/summary")
# def admin_summary():
#     conn = get_db_connection()
#     if conn is None:
#         return {"error": "db_failed"}

#     cur = conn.cursor(dictionary=True)
#     # total students
#     cur.execute("SELECT COUNT(*) AS cnt FROM students")
#     total_students = cur.fetchone()["cnt"] or 0

#     cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
#     total_teachers = cur.fetchone()["cnt"] or 0

#     # today entries / exits
#     today = datetime.now().strftime("%Y-%m-%d")
#     cur.execute("SELECT COUNT(*) AS cnt FROM logs WHERE DATE(scan_time)=%s AND action='entry'", (today,))
#     today_entries = cur.fetchone()["cnt"] or 0
#     cur.execute("SELECT COUNT(*) AS cnt FROM logs WHERE DATE(scan_time)=%s AND action='exit'", (today,))
#     today_exits = cur.fetchone()["cnt"] or 0

#     cur.execute("SELECT COUNT(*) AS cnt FROM logs")
#     total_logs = cur.fetchone()["cnt"] or 0

#     # skipping alerts count
#     cur.execute("SELECT COUNT(*) AS cnt FROM logs WHERE remarks LIKE %s", ("%Skipping class%",))
#     skipping_alerts = cur.fetchone()["cnt"] or 0

#     conn.close()
#     return {
#         "total_students": total_students,
#         "total_teachers": total_teachers,
#         "today_entries": today_entries,
#         "today_exits": today_exits,
#         "total_logs": total_logs,
#         "skipping_alerts": skipping_alerts
#     }


# # --- Recent logs ---
# @app.get("/admin/logs/recent")
# def recent_logs(limit: int = 10):
#     conn = get_db_connection()
#     if conn is None:
#         return []
#     cur = conn.cursor(dictionary=True)
#     cur.execute("SELECT log_id, user_id, role, action, status, remarks, scan_time FROM logs ORDER BY scan_time DESC LIMIT %s", (limit,))
#     rows = cur.fetchall()
#     conn.close()
#     return rows


# # --- Charts / stats ---
# @app.get("/admin/stats/charts")
# def stats_charts():
#     conn = get_db_connection()
#     if conn is None:
#         return {}
#     cur = conn.cursor(dictionary=True)

#     # member distribution
#     cur.execute("SELECT COUNT(*) AS cnt FROM students")
#     students = cur.fetchone()["cnt"] or 0
#     cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
#     teachers = cur.fetchone()["cnt"] or 0

#     # today entry/exit
#     today = datetime.now().strftime("%Y-%m-%d")
#     cur.execute("SELECT COUNT(*) AS cnt FROM logs WHERE DATE(scan_time)=%s AND action='entry'", (today,))
#     entry = cur.fetchone()["cnt"] or 0
#     cur.execute("SELECT COUNT(*) AS cnt FROM logs WHERE DATE(scan_time)=%s AND action='exit'", (today,))
#     exitc = cur.fetchone()["cnt"] or 0

#     # logs per hour (0..23) today
#     cur.execute("""
#         SELECT HOUR(scan_time) AS hr, COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s
#         GROUP BY HOUR(scan_time)
#         ORDER BY hr
#     """, (today,))
#     rows = cur.fetchall()
#     # convert to array hr->cnt
#     logs_by_hour = [{"hour": r["hr"], "count": r["cnt"]} for r in rows]

#     conn.close()
#     return {
#         "members": {"students": students, "teachers": teachers},
#         "today": {"entry": entry, "exit": exitc},
#         "logs_by_hour": logs_by_hour
#     }
