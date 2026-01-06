from database import get_db_connection
from datetime import datetime

# ======================================================
# CHECK TEACHER
# ======================================================
def check_teacher(user_id):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM teachers WHERE teacher_id=%s LIMIT 1",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


# ======================================================
# CHECK STUDENT
# ======================================================
def check_student(user_id):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM students WHERE student_id=%s LIMIT 1",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


# ======================================================
# CHECK TIMETABLE (FOR FUTURE SKIP LOGIC)
# ======================================================
def check_timetable(dept, year, division):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    now = datetime.now()

    cursor.execute("""
        SELECT *
        FROM timetable
        WHERE department=%s
          AND year=%s
          AND division=%s
          AND day_of_week=%s
          AND TIME(%s) BETWEEN start_time AND end_time
        LIMIT 1
    """, (
        dept,
        year,
        division,
        now.strftime("%A"),
        now.strftime("%H:%M:%S")
    ))

    row = cursor.fetchone()
    conn.close()
    return row


# ======================================================
# INSERT LOG (FINAL & CORRECT)
# ======================================================
def insert_log(
    student_id,
    action,
    status,
    matched_subject=None,
    matched_teacher_id=None
):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs
        (user_id, scan_time, action, status, matched_subject, matched_teacher_id)
        VALUES (%s, NOW(), %s, %s, %s, %s)
    """, (
        student_id,
        action,
        status,
        matched_subject,
        matched_teacher_id
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id



# ======================================================
# GET LAST ACTION (ENTRY / EXIT)
# ======================================================
def get_last_action(user_id):
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT action
        FROM logs
        WHERE user_id=%s
        ORDER BY scan_time DESC
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()
    return row["action"] if row else None


# ======================================================
# PASSWORD UTILS (KEEP AS IS)
# ======================================================
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# backend/utils.py

import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "smartlibrary.alerts@gmail.com"
SENDER_PASSWORD = ""

def send_skip_email(
    teacher_email,
    teacher_name,
    student_name,
    subject,
    scan_time
):
    msg = MIMEText(f"""
Dear {teacher_name},

The following student was detected inside the library
during your scheduled lecture.

Student Name : {student_name}
Subject      : {subject}
Scan Time    : {scan_time}

This is a system-generated alert.

Regards,
Smart Library Monitoring System
""")

    msg["Subject"] = "Lecture Skipping Alert"
    msg["From"] = SENDER_EMAIL
    msg["To"] = teacher_email

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

# ======================================================
# TEMPORARY TEST CODE (ADD ONLY FOR TESTING)
# ======================================================
# if __name__ == "__main__":
#     send_skip_email(
#         teacher_email="bhagyashripatil0526@gmail.com",  # put YOUR email here
#         teacher_name="Test Teacher",
#         student_name="Test Student",
#         subject="DBMS",
#         scan_time="2026-01-04 10:30"
#     )