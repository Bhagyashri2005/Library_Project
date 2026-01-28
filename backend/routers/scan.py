from fastapi import APIRouter, HTTPException
from datetime import datetime
from schemas import ScanRequest
from database import get_db_connection

from utils import (
    check_teacher,
    check_student,
    get_last_action,
    insert_log,
    send_skip_email,
    normalize_text          # ✅ ADDED
)

router = APIRouter(tags=["Scan"])


@router.post("/scan")
def scan_id(data: ScanRequest):
    user_id = normalize_text(data.user_id, "upper")   # ✅ ADDED

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Determine ENTRY / EXIT
    last_action = get_last_action(user_id)
    next_action = "EXIT" if last_action == "ENTRY" else "ENTRY"

    # ================= TEACHER =================
    teacher = check_teacher(user_id)
    if teacher:
        insert_log(
            student_id=user_id,
            action=normalize_text(next_action, "upper"),  # ✅ ADDED
            status="NORMAL"
        )

        return {
            "status": "Access Granted",
            "role": "teacher",
            "action": next_action,
            "message": f"Teacher {next_action} Successful"
        }

    # ================= STUDENT =================
    student = check_student(user_id)
    if student:

        status = "NORMAL"
        matched_subject = None
        matched_teacher_id = None

        # 🔍 Check SKIP only on ENTRY
        if next_action == "ENTRY":
            lecture = get_current_lecture(
                department=normalize_text(student["department"], "upper"),  # ✅
                year=normalize_text(student["year"], "upper"),              # ✅
                division=normalize_text(student["division"], "upper"),      # ✅
                batch=normalize_text(student["batch"], "upper")             # ✅
            )

            if lecture:
                status = "SKIP"
                matched_subject = lecture["subject"]
                matched_teacher_id = lecture["teacher_id"]

        # 📝 Insert log
        log_id = insert_log(
            student_id=user_id,
            action=normalize_text(next_action, "upper"),   # ✅ ADDED
            status=normalize_text(status, "upper"),        # ✅ ADDED
            matched_subject=matched_subject,
            matched_teacher_id=matched_teacher_id
        )

        # 📧 Trigger email if skipped
        if status == "SKIP":
            trigger_skip_email(log_id)

        return {
            "status": "Access Granted",
            "role": "student",
            "action": next_action,
            "message": f"Student {next_action} Successful"
        }

    # ================= INVALID =================
    raise HTTPException(status_code=403, detail="Access Denied: Invalid ID")


# =========================================================
# Helper: Get Current Lecture from Timetable
# =========================================================
def get_current_lecture(department, year, division, batch):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    now = datetime.now()
    day = normalize_text(now.strftime("%A"), "title")
    current_time = now.strftime("%H:%M")  # TIME column → HH:MM

    cur.execute("""
        SELECT subject, teacher_id
        FROM timetable
        WHERE department=%s
          AND year=%s
          AND division=%s
          AND (batch IS NULL OR batch=%s)
          AND day_of_week=%s
          AND %s BETWEEN start_time AND end_time
    """, (
        department,
        year,
        division,
        batch,
        day,
        current_time
    ))

    lecture = cur.fetchone()
    conn.close()
    return lecture


# =========================================================
# Helper: Trigger Skip Email
# =========================================================
def trigger_skip_email(log_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Fetch log + student
    cur.execute("""
        SELECT l.matched_subject, l.matched_teacher_id, l.scan_time,
               s.name AS student_name
        FROM logs l
        JOIN students s ON l.user_id = s.student_id
        WHERE l.log_id = %s
    """, (log_id,))
    log = cur.fetchone()

    if not log or not log["matched_teacher_id"]:
        conn.close()
        return

    # Fetch teacher
    cur.execute("""
        SELECT name, email
        FROM teachers
        WHERE teacher_id = %s
    """, (log["matched_teacher_id"],))
    teacher = cur.fetchone()

    if not teacher:
        conn.close()
        return

    # Send email
    send_skip_email(
        teacher_email=teacher["email"],
        teacher_name=teacher["name"],
        student_name=log["student_name"],
        subject=log["matched_subject"],
        scan_time=log["scan_time"]
    )

    conn.close()


# from fastapi import APIRouter, HTTPException
# from datetime import datetime
# from schemas import ScanRequest
# from database import get_db_connection

# from utils import (
#     check_teacher,
#     check_student,
#     get_last_action,
#     insert_log,
#     send_skip_email
# )

# router = APIRouter(tags=["Scan"])


# @router.post("/scan")
# def scan_id(data: ScanRequest):
#     user_id = data.user_id.strip()

#     if not user_id:
#         raise HTTPException(status_code=400, detail="Invalid ID")

#     # Determine ENTRY / EXIT
#     last_action = get_last_action(user_id)
#     next_action = "EXIT" if last_action == "ENTRY" else "ENTRY"

#     # ================= TEACHER =================
#     teacher = check_teacher(user_id)
#     if teacher:
#         insert_log(
#             student_id=user_id,
#             action=next_action,
#             status="NORMAL"
#         )

#         return {
#             "status": "Access Granted",
#             "role": "teacher",
#             "action": next_action,
#             "message": f"Teacher {next_action} Successful"
#         }

#     # ================= STUDENT =================
#     student = check_student(user_id)
#     if student:

#         status = "NORMAL"
#         matched_subject = None
#         matched_teacher_id = None

#         # 🔍 Check SKIP only on ENTRY
#         if next_action == "ENTRY":
#             lecture = get_current_lecture(
#                 department=student["department"],
#                 year=student["year"],
#                 division=student["division"],
#                 batch=student["batch"]
#             )

#             if lecture:
#                 status = "SKIP"
#                 matched_subject = lecture["subject"]
#                 matched_teacher_id = lecture["teacher_id"]

#         # 📝 Insert log
#         log_id = insert_log(
#             student_id=user_id,
#             action=next_action,
#             status=status,
#             matched_subject=matched_subject,
#             matched_teacher_id=matched_teacher_id
#         )

#         # 📧 Trigger email if skipped
#         if status == "SKIP":
#             trigger_skip_email(log_id)

#         return {
#             "status": "Access Granted",
#             "role": "student",
#             "action": next_action,
#             "message": f"Student {next_action} Successful"
#         }

#     # ================= INVALID =================
#     raise HTTPException(status_code=403, detail="Access Denied: Invalid ID")


# # =========================================================
# # Helper: Get Current Lecture from Timetable
# # =========================================================
# def get_current_lecture(department, year, division, batch):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     now = datetime.now()
#     day = now.strftime("%A")
#     current_time = now.strftime("%H:%M:%S")

#     cur.execute("""
#         SELECT subject, teacher_id
#         FROM timetable
#         WHERE department=%s
#           AND year=%s
#           AND division=%s
#           AND batch=%s
#           AND day_of_week=%s
#           AND %s BETWEEN start_time AND end_time
#     """, (
#         department,
#         year,
#         division,
#         batch,
#         day,
#         current_time
#     ))

#     lecture = cur.fetchone()
#     conn.close()
#     return lecture


# # =========================================================
# # Helper: Trigger Skip Email
# # =========================================================
# def trigger_skip_email(log_id):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     # Fetch log + student
#     cur.execute("""
#         SELECT l.matched_subject, l.matched_teacher_id, l.scan_time,
#                s.name AS student_name
#         FROM logs l
#         JOIN students s ON l.user_id = s.student_id
#         WHERE l.log_id = %s
#     """, (log_id,))
#     log = cur.fetchone()

#     if not log or not log["matched_teacher_id"]:
#         conn.close()
#         return

#     # Fetch teacher
#     cur.execute("""
#         SELECT name, email
#         FROM teachers
#         WHERE teacher_id = %s
#     """, (log["matched_teacher_id"],))
#     teacher = cur.fetchone()

#     if not teacher:
#         conn.close()
#         return

#     # Send email
#     send_skip_email(
#         teacher_email=teacher["email"],
#         teacher_name=teacher["name"],
#         student_name=log["student_name"],
#         subject=log["matched_subject"],
#         scan_time=log["scan_time"]
#     )

#     conn.close()


