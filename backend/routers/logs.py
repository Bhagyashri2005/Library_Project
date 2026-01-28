from fastapi import APIRouter, HTTPException
from database import get_db_connection
import math
from fastapi.responses import StreamingResponse
import csv, io
from utils import normalize_text   # ✅ ADDED

router = APIRouter(prefix="/admin/logs", tags=["Logs"])


# =========================================================
# GET ALL LOGS (WITH FILTERS + PAGINATION)
# =========================================================
@router.get("")
def get_logs(
    page: int = 1,
    page_size: int = 20,
    user_id: str = "",
    role: str = "",
    department: str = "",
    year: str = "",
    division: str = "",
    batch: str = "",
    action: str = "",
    status: str = "",
    dateFrom: str = "",
    dateTo: str = ""
):

    # ✅ NORMALIZATION (ADDED)
    user_id = normalize_text(user_id, "upper")
    role = normalize_text(role, "lower")
    department = normalize_text(department, "upper")
    year = normalize_text(year, "upper")
    division = normalize_text(division, "upper")
    batch = normalize_text(batch, "upper")
    action = normalize_text(action, "upper")
    status = normalize_text(status, "upper")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    conditions = []
    params = []

    if user_id:
        conditions.append("logs.user_id LIKE %s")
        params.append(f"%{user_id}%")

    if department:
        conditions.append(
            "(students.department = %s OR teachers.department = %s)"
        )
        params.extend([department, department])

    if action:
        conditions.append("logs.action = %s")
        params.append(action)

    if status:
        conditions.append("logs.status = %s")
        params.append(status)

    if dateFrom:
        conditions.append("DATE(logs.scan_time) >= %s")
        params.append(dateFrom)

    if dateTo:
        conditions.append("DATE(logs.scan_time) <= %s")
        params.append(dateTo)

    if role == "student":
        conditions.append("students.student_id IS NOT NULL")

    if role == "teacher":
        conditions.append("teachers.teacher_id IS NOT NULL")

    if year:
        conditions.append("students.year = %s")
        params.append(year)

    if division:
        conditions.append("students.division = %s")
        params.append(division)

    if batch:
        conditions.append("students.batch = %s")
        params.append(batch)

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    count_query = f"""
        SELECT COUNT(*) AS total
        FROM logs
        LEFT JOIN students ON students.student_id = logs.user_id
        LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
        {where_clause}
    """
    cur.execute(count_query, params)
    total = cur.fetchone()["total"]

    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    query = f"""
        SELECT
            logs.log_id,
            logs.user_id,
            COALESCE(students.name, teachers.name) AS name,
            CASE
                WHEN students.student_id IS NOT NULL THEN 'student'
                ELSE 'teacher'
            END AS role,
            COALESCE(students.department, teachers.department) AS department,
            logs.action,
            logs.status,
            logs.matched_subject,
            logs.matched_teacher_id,
            logs.scan_time
        FROM logs
        LEFT JOIN students ON students.student_id = logs.user_id
        LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
        {where_clause}
        ORDER BY logs.scan_time DESC
        LIMIT %s OFFSET %s
    """

    cur.execute(query, params + [page_size, offset])
    rows = cur.fetchall()
    conn.close()

    return {
        "data": rows,
        "total_pages": total_pages
    }


# =========================================================
# RECENT LOGS
# =========================================================
@router.get("/recent")
def recent_logs(limit: int = 10):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            logs.log_id,
            logs.user_id,
            COALESCE(students.name, teachers.name) AS name,
            logs.action,
            logs.status,
            logs.scan_time
        FROM logs
        LEFT JOIN students ON students.student_id = logs.user_id
        LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
        ORDER BY logs.scan_time DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


# =========================================================
# MANUAL ENTRY / EXIT
# =========================================================
@router.post("/manual")
def manual_entry(
    user_id: str,
    action: str
):
    user_id = normalize_text(user_id, "upper")   # ✅ ADDED
    action = normalize_text(action, "upper")     # ✅ ADDED

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT student_id FROM students WHERE student_id = %s
        UNION
        SELECT teacher_id FROM teachers WHERE teacher_id = %s
    """, (user_id, user_id))

    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="User not found")

    cur.execute("""
        SELECT action FROM logs
        WHERE user_id = %s
        ORDER BY scan_time DESC
        LIMIT 1
    """, (user_id,))

    last_log = cur.fetchone()

    if last_log and last_log["action"] == action:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"User already has an active {action}"
        )

    cur.execute("""
        INSERT INTO logs (user_id, scan_time, action, status)
        VALUES (%s, NOW(), %s, 'NORMAL')
    """, (user_id, action))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"{action} recorded successfully"
    }


@router.get("/departments")
def get_departments():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT DISTINCT department FROM students
        UNION
        SELECT DISTINCT department FROM teachers
        ORDER BY department
    """)

    rows = cur.fetchall()
    conn.close()
    return [row["department"] for row in rows if row["department"]]


@router.get("/export")
def export_logs(
    user_id: str = "",
    department: str = "",
    action: str = "",
    status: str = "",
    dateFrom: str = "",
    dateTo: str = ""
):
    user_id = normalize_text(user_id, "upper")
    department = normalize_text(department, "upper")
    action = normalize_text(action, "upper")
    status = normalize_text(status, "upper")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    conditions = []
    params = []

    if user_id:
        conditions.append("logs.user_id LIKE %s")
        params.append(f"%{user_id}%")

    if department:
        conditions.append(
            "(students.department = %s OR teachers.department = %s)"
        )
        params.extend([department, department])

    if action:
        conditions.append("logs.action = %s")
        params.append(action)

    if status:
        conditions.append("logs.status = %s")
        params.append(status)

    if dateFrom:
        conditions.append("DATE(logs.scan_time) >= %s")
        params.append(dateFrom)

    if dateTo:
        conditions.append("DATE(logs.scan_time) <= %s")
        params.append(dateTo)

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
        SELECT
            logs.log_id,
            logs.user_id,
            COALESCE(students.name, teachers.name) AS name,
            CASE
                WHEN students.student_id IS NOT NULL THEN 'student'
                ELSE 'teacher'
            END AS role,
            COALESCE(students.department, teachers.department) AS department,
            logs.action,
            logs.status,
            logs.matched_subject,
            logs.scan_time
        FROM logs
        LEFT JOIN students ON students.student_id = logs.user_id
        LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
        {where_clause}
        ORDER BY logs.scan_time DESC
    """

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Log ID", "User ID", "Name", "Role",
        "Department", "Action", "Status",
        "Subject", "Time"
    ])

    for r in rows:
        writer.writerow([
            r["log_id"],
            r["user_id"],
            r["name"],
            r["role"],
            r["department"],
            r["action"],
            r["status"],
            r["matched_subject"] or "",
            r["scan_time"]
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=logs_report.csv"
        }
    )


@router.get("/departments/by-role")
def get_departments_by_role(role: str = ""):
    role = normalize_text(role, "lower")   # ✅ ADDED

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if role == "teacher":
        cur.execute("SELECT DISTINCT department FROM teachers ORDER BY department")
    elif role == "student":
        cur.execute("SELECT DISTINCT department FROM students ORDER BY department")
    else:
        cur.execute("""
            SELECT DISTINCT department FROM students
            UNION
            SELECT DISTINCT department FROM teachers
            ORDER BY department
        """)

    rows = cur.fetchall()
    conn.close()
    return [r["department"] for r in rows]


@router.get("/students/meta")
def student_meta():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT DISTINCT year FROM students ORDER BY year")
    years = [r["year"] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT division FROM students ORDER BY division")
    divisions = [r["division"] for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT batch FROM students ORDER BY batch")
    batches = [r["batch"] for r in cur.fetchall()]

    conn.close()

    return {
        "years": years,
        "divisions": divisions,
        "batches": batches
    }


# from fastapi import APIRouter, HTTPException
# from database import get_db_connection
# import math
# from fastapi.responses import StreamingResponse
# import csv, io

# router = APIRouter(prefix="/admin/logs", tags=["Logs"])


# # =========================================================
# # GET ALL LOGS (WITH FILTERS + PAGINATION)
# # =========================================================
# @router.get("")
# def get_logs(
#     page: int = 1,
#     page_size: int = 20,
#     user_id: str = "",
#     role: str = "",
#     department: str = "",
#     year: str = "",
#     division: str = "",
#     batch: str = "",
#     action: str = "",
#     status: str = "",
#     dateFrom: str = "",
#     dateTo: str = ""
# ):

#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     conditions = []
#     params = []

#     # --- Filters ---
#     if user_id:
#         conditions.append("logs.user_id LIKE %s")
#         params.append(f"%{user_id}%")

#     if department:
#         conditions.append(
#             "(students.department = %s OR teachers.department = %s)"
#         )
#         params.extend([department, department])


#     if action:
#         conditions.append("logs.action = %s")
#         params.append(action.upper())

#     if status:
#         conditions.append("logs.status = %s")
#         params.append(status.upper())

#     if dateFrom:
#         conditions.append("DATE(logs.scan_time) >= %s")
#         params.append(dateFrom)

#     if dateTo:
#         conditions.append("DATE(logs.scan_time) <= %s")
#         params.append(dateTo)

#     # Role filter
#     if role == "student":
#         conditions.append("students.student_id IS NOT NULL")

#     if role == "teacher":
#         conditions.append("teachers.teacher_id IS NOT NULL")

#     # Student-only filters
#     if year:
#         conditions.append("students.year = %s")
#         params.append(year)

#     if division:
#         conditions.append("students.division = %s")
#         params.append(division)

#     if batch:
#         conditions.append("students.batch = %s")
#         params.append(batch)


#     where_clause = " AND ".join(conditions)
#     if where_clause:
#         where_clause = "WHERE " + where_clause

#     # =====================================================
#     # COUNT QUERY
#     # =====================================================
#     count_query = f"""
#         SELECT COUNT(*) AS total
#         FROM logs
#         LEFT JOIN students ON students.student_id = logs.user_id
#         LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
#         {where_clause}
#     """
#     cur.execute(count_query, params)
#     total = cur.fetchone()["total"]

#     total_pages = max(1, math.ceil(total / page_size))
#     offset = (page - 1) * page_size

#     # =====================================================
#     # MAIN DATA QUERY
#     # =====================================================
#     query = f"""
#         SELECT
#             logs.log_id,
#             logs.user_id,

#             COALESCE(students.name, teachers.name) AS name,

#             CASE
#                 WHEN students.student_id IS NOT NULL THEN 'student'
#                 ELSE 'teacher'
#             END AS role,

#             COALESCE(students.department, teachers.department) AS department,

#             logs.action,
#             logs.status,
#             logs.matched_subject,
#             logs.matched_teacher_id,
#             logs.scan_time
#         FROM logs
#         LEFT JOIN students ON students.student_id = logs.user_id
#         LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
#         {where_clause}
#         ORDER BY logs.scan_time DESC
#         LIMIT %s OFFSET %s
#     """

#     cur.execute(query, params + [page_size, offset])
#     rows = cur.fetchall()

#     conn.close()

#     return {
#         "data": rows,
#         "total_pages": total_pages
#     }


# # =========================================================
# # RECENT LOGS (FOR DASHBOARD)
# # =========================================================
# @router.get("/recent")
# def recent_logs(limit: int = 10):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT
#             logs.log_id,
#             logs.user_id,
#             COALESCE(students.name, teachers.name) AS name,
#             logs.action,
#             logs.status,
#             logs.scan_time
#         FROM logs
#         LEFT JOIN students ON students.student_id = logs.user_id
#         LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
#         ORDER BY logs.scan_time DESC
#         LIMIT %s
#     """, (limit,))

#     rows = cur.fetchall()
#     conn.close()
#     return rows


# # =========================================================
# # MANUAL ENTRY / EXIT
# # =========================================================
# @router.post("/manual")
# def manual_entry(
#     user_id: str,
#     action: str
# ):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     action = action.upper()

#     # 1️⃣ Check user exists (student or teacher)
#     cur.execute("""
#         SELECT student_id FROM students WHERE student_id = %s
#         UNION
#         SELECT teacher_id FROM teachers WHERE teacher_id = %s
#     """, (user_id, user_id))

#     if not cur.fetchone():
#         raise HTTPException(status_code=404, detail="User not found")

#     # 2️⃣ Get last log for this user
#     cur.execute("""
#         SELECT action FROM logs
#         WHERE user_id = %s
#         ORDER BY scan_time DESC
#         LIMIT 1
#     """, (user_id,))

#     last_log = cur.fetchone()

#     # 3️⃣ Prevent duplicate consecutive actions
#     if last_log and last_log["action"] == action:
#         conn.close()
#         raise HTTPException(
#             status_code=400,
#             detail=f"User already has an active {action}"
#         )

#     # 4️⃣ Insert new log
#     cur.execute("""
#         INSERT INTO logs (user_id, scan_time, action, status)
#         VALUES (%s, NOW(), %s, 'NORMAL')
#     """, (user_id, action))

#     conn.commit()
#     conn.close()

#     return {
#         "status": "success",
#         "message": f"{action} recorded successfully"
#     }


# @router.get("/departments")
# def get_departments():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("""
#         SELECT DISTINCT department FROM students
#         UNION
#         SELECT DISTINCT department FROM teachers
#         ORDER BY department
#     """)

#     rows = cur.fetchall()
#     conn.close()

#     return [row["department"] for row in rows if row["department"]]

# @router.get("/export")
# def export_logs(
#     user_id: str = "",
#     department: str = "",
#     action: str = "",
#     status: str = "",
#     dateFrom: str = "",
#     dateTo: str = ""
# ):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     conditions = []
#     params = []

#     if user_id:
#         conditions.append("logs.user_id LIKE %s")
#         params.append(f"%{user_id}%")

#     if department:
#         conditions.append(
#             "(students.department = %s OR teachers.department = %s)"
#         )
#         params.extend([department, department])

#     if action:
#         conditions.append("logs.action = %s")
#         params.append(action.upper())

#     if status:
#         conditions.append("logs.status = %s")
#         params.append(status.upper())

#     if dateFrom:
#         conditions.append("DATE(logs.scan_time) >= %s")
#         params.append(dateFrom)

#     if dateTo:
#         conditions.append("DATE(logs.scan_time) <= %s")
#         params.append(dateTo)

#     where_clause = " AND ".join(conditions)
#     if where_clause:
#         where_clause = "WHERE " + where_clause

#     query = f"""
#         SELECT
#             logs.log_id,
#             logs.user_id,
#             COALESCE(students.name, teachers.name) AS name,
#             CASE
#                 WHEN students.student_id IS NOT NULL THEN 'student'
#                 ELSE 'teacher'
#             END AS role,
#             COALESCE(students.department, teachers.department) AS department,
#             logs.action,
#             logs.status,
#             logs.matched_subject,
#             logs.scan_time
#         FROM logs
#         LEFT JOIN students ON students.student_id = logs.user_id
#         LEFT JOIN teachers ON teachers.teacher_id = logs.user_id
#         {where_clause}
#         ORDER BY logs.scan_time DESC
#     """

#     cur.execute(query, params)
#     rows = cur.fetchall()
#     conn.close()

#     # ---- CSV ----
#     output = io.StringIO()
#     writer = csv.writer(output)

#     writer.writerow([
#         "Log ID", "User ID", "Name", "Role",
#         "Department", "Action", "Status",
#         "Subject", "Time"
#     ])

#     for r in rows:
#         writer.writerow([
#             r["log_id"],
#             r["user_id"],
#             r["name"],
#             r["role"],
#             r["department"],
#             r["action"],
#             r["status"],
#             r["matched_subject"] or "",
#             r["scan_time"]
#         ])

#     output.seek(0)

#     return StreamingResponse(
#         output,
#         media_type="text/csv",
#         headers={
#             "Content-Disposition": "attachment; filename=logs_report.csv"
#         }
#     )

# @router.get("/departments/by-role")
# def get_departments_by_role(role: str = ""):
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     if role == "teacher":
#         cur.execute("SELECT DISTINCT department FROM teachers ORDER BY department")
#     elif role == "student":
#         cur.execute("SELECT DISTINCT department FROM students ORDER BY department")
#     else:
#         cur.execute("""
#             SELECT DISTINCT department FROM students
#             UNION
#             SELECT DISTINCT department FROM teachers
#             ORDER BY department
#         """)

#     rows = cur.fetchall()
#     conn.close()
#     return [r["department"] for r in rows]

# @router.get("/students/meta")
# def student_meta():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("SELECT DISTINCT year FROM students ORDER BY year")
#     years = [r["year"] for r in cur.fetchall()]

#     cur.execute("SELECT DISTINCT division FROM students ORDER BY division")
#     divisions = [r["division"] for r in cur.fetchall()]

#     cur.execute("SELECT DISTINCT batch FROM students ORDER BY batch")
#     batches = [r["batch"] for r in cur.fetchall()]

#     conn.close()

#     return {
#         "years": years,
#         "divisions": divisions,
#         "batches": batches
#     }

