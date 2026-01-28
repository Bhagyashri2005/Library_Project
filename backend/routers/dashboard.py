from fastapi import APIRouter
from database import get_db_connection
from datetime import datetime
from utils import normalize_text   # ✅ ADDED

router = APIRouter(prefix="/admin", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM logs
        WHERE action='ENTRY'
    """)
    total_inside = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM logs
        WHERE status='SKIP' AND DATE(scan_time)=CURDATE()
    """)
    alerts_today = cursor.fetchone()["count"]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM logs
        WHERE DATE(scan_time)=CURDATE()
    """)
    total_today = cursor.fetchone()["count"]

    conn.close()

    return {
        "inside_now": total_inside,
        "alerts_today": alerts_today,
        "total_entries_today": total_today
    }


@router.get("/summary")
def admin_summary():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS cnt FROM students")
    total_students = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
    total_teachers = cur.fetchone()["cnt"]

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM logs
        WHERE DATE(scan_time)=%s AND action='ENTRY'
    """, (today,))
    today_entries = cur.fetchone()["cnt"]

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM logs
        WHERE DATE(scan_time)=%s AND action='EXIT'
    """, (today,))
    today_exits = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM logs")
    total_logs = cur.fetchone()["cnt"]

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM logs
        WHERE status='SKIP' AND DATE(scan_time)=%s
    """, (today,))
    skipping_alerts = cur.fetchone()["cnt"]

    conn.close()

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "today_entries": today_entries,
        "today_exits": today_exits,
        "total_logs": total_logs,
        "skipping_alerts": skipping_alerts
    }


@router.get("/stats/charts")
def stats_charts():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS cnt FROM students")
    students = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
    teachers = cur.fetchone()["cnt"]

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM logs
        WHERE DATE(scan_time)=%s AND action='ENTRY'
    """, (today,))
    entry = cur.fetchone()["cnt"]

    cur.execute("""
        SELECT COUNT(*) AS cnt
        FROM logs
        WHERE DATE(scan_time)=%s AND action='EXIT'
    """, (today,))
    exitc = cur.fetchone()["cnt"]

    cur.execute("""
        SELECT HOUR(scan_time) AS hr, COUNT(*) AS cnt
        FROM logs
        WHERE DATE(scan_time)=%s
        GROUP BY HOUR(scan_time)
        ORDER BY hr
    """, (today,))
    rows = cur.fetchall()

    conn.close()

    return {
        "members": {"students": students, "teachers": teachers},
        "today": {"entry": entry, "exit": exitc},
        "logs_by_hour": [{"hour": r["hr"], "count": r["cnt"]} for r in rows]
    }


@router.get("/filters")
def get_filter_options():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT DISTINCT department FROM students")
    departments = [row["department"] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT year FROM students")
    years = [row["year"] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT division FROM students")
    divisions = [row["division"] for row in cursor.fetchall()]

    conn.close()

    return {
        "departments": departments,
        "years": years,
        "divisions": divisions
    }


@router.get("/charts/members")
def members_chart(
    member_type: str = None,
    department: str = None,
    year: str = None,
    division: str = None
):
    # ✅ NORMALIZATION ADDED
    member_type = normalize_text(member_type, "lower")
    department = normalize_text(department, "upper")
    year = normalize_text(year, "upper")
    division = normalize_text(division, "upper")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if not member_type:
        cursor.execute("SELECT COUNT(*) AS count FROM students")
        student_count = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM teachers")
        teacher_count = cursor.fetchone()["count"]

        conn.close()
        return [
            {"name": "Students", "value": student_count},
            {"name": "Teachers", "value": teacher_count}
        ]

    if member_type == "student":
        query = "SELECT COUNT(*) AS count FROM students WHERE 1=1"
        params = []

        if department:
            query += " AND department = %s"
            params.append(department)

        if year:
            query += " AND year = %s"
            params.append(year)

        if division:
            query += " AND division = %s"
            params.append(division)

        cursor.execute(query, params)
        count = cursor.fetchone()["count"]

        conn.close()
        return [{"name": "Students", "value": count}]

    if member_type == "teacher":
        query = "SELECT COUNT(*) AS count FROM teachers WHERE 1=1"
        params = []

        if department:
            query += " AND department = %s"
            params.append(department)

        cursor.execute(query, params)
        count = cursor.fetchone()["count"]

        conn.close()
        return [{"name": "Teachers", "value": count}]


@router.get("/filters/student/departments")
def student_departments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT department 
        FROM students 
        ORDER BY department
    """)
    data = [row["department"] for row in cursor.fetchall()]

    conn.close()
    return data


@router.get("/filters/student/years")
def student_years(department: str = None):
    department = normalize_text(department, "upper")  # ✅ ADDED

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if department:
        cursor.execute("""
            SELECT DISTINCT year
            FROM students
            WHERE department = %s
            ORDER BY year
        """, (department,))
    else:
        cursor.execute("""
            SELECT DISTINCT year
            FROM students
            ORDER BY year
        """)

    data = [row["year"] for row in cursor.fetchall()]
    conn.close()
    return data


@router.get("/filters/student/divisions")
def student_divisions(department: str = None, year: str = None):
    department = normalize_text(department, "upper")  # ✅ ADDED
    year = normalize_text(year, "upper")              # ✅ ADDED

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT DISTINCT division FROM students WHERE 1=1"
    params = []

    if department:
        query += " AND department = %s"
        params.append(department)

    if year:
        query += " AND year = %s"
        params.append(year)

    query += " ORDER BY division"

    cursor.execute(query, params)
    data = [row["division"] for row in cursor.fetchall()]

    conn.close()
    return data


@router.get("/filters/teacher/departments")
def teacher_departments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT department
        FROM teachers
        ORDER BY department
    """)

    data = [row["department"] for row in cursor.fetchall()]
    conn.close()
    return data


@router.get("/charts/department-wise")
def department_wise_chart(
    member_type: str = None,
    year: str = None,
    division: str = None
):
    member_type = normalize_text(member_type, "lower")  # ✅ ADDED
    year = normalize_text(year, "upper")                # ✅ ADDED
    division = normalize_text(division, "upper")        # ✅ ADDED

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    student_query = """
        SELECT department, COUNT(*) AS students
        FROM students
        WHERE 1=1
    """
    student_params = []

    if year:
        student_query += " AND year = %s"
        student_params.append(year)

    if division:
        student_query += " AND division = %s"
        student_params.append(division)

    student_query += " GROUP BY department"

    cursor.execute(student_query, student_params)
    student_data = cursor.fetchall()

    cursor.execute("""
        SELECT department, COUNT(*) AS teachers
        FROM teachers
        GROUP BY department
    """)
    teacher_data = cursor.fetchall()

    conn.close()

    result = {}

    for row in student_data:
        dept = row["department"]
        result.setdefault(dept, {"department": dept, "students": 0, "teachers": 0})
        result[dept]["students"] = row["students"]

    for row in teacher_data:
        dept = row["department"]
        result.setdefault(dept, {"department": dept, "students": 0, "teachers": 0})
        result[dept]["teachers"] = row["teachers"]

    data = list(result.values())

    if member_type == "student":
        for d in data:
            d["teachers"] = 0

    if member_type == "teacher":
        for d in data:
            d["students"] = 0

    return data


@router.get("/charts/attendance-timeline")
def attendance_timeline(
    date: str = None,
    start_hour: int = 8,
    end_hour: int = 18
):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    date_condition = "CURDATE()" if not date else "%s"

    query = f"""
        SELECT
            HOUR(scan_time) AS hr,
            SUM(action='ENTRY') AS entry_count,
            SUM(action='EXIT') AS exit_count
        FROM logs
        WHERE DATE(scan_time) = {date_condition}
          AND HOUR(scan_time) BETWEEN %s AND %s
        GROUP BY hr
        ORDER BY hr
    """

    params = []
    if date:
        params.append(date)
    params.extend([start_hour, end_hour])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    timeline = []
    for h in range(start_hour, end_hour + 1):
        label = f"{h if h<=12 else h-12} {'AM' if h<12 else 'PM'}"
        row = next((r for r in rows if r["hr"] == h), None)
        timeline.append({
            "time": label,
            "entry": row["entry_count"] if row else 0,
            "exit": row["exit_count"] if row else 0,
            "skip": 0
        })

    return timeline

# from fastapi import APIRouter
# from database import get_db_connection
# from datetime import datetime

# router = APIRouter(prefix="/admin", tags=["Dashboard"])

# @router.get("/stats")
# def dashboard_stats():
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("""
#         SELECT COUNT(*) AS count
#         FROM logs
#         WHERE action='ENTRY'
#     """)
#     total_inside = cursor.fetchone()["count"]

#     cursor.execute("""
#         SELECT COUNT(*) AS count
#         FROM logs
#         WHERE status='SKIP' AND DATE(scan_time)=CURDATE()
#     """)
#     alerts_today = cursor.fetchone()["count"]

#     cursor.execute("""
#         SELECT COUNT(*) AS count
#         FROM logs
#         WHERE DATE(scan_time)=CURDATE()
#     """)
#     total_today = cursor.fetchone()["count"]

#     conn.close()

#     return {
#         "inside_now": total_inside,
#         "alerts_today": alerts_today,
#         "total_entries_today": total_today
#     }



# @router.get("/summary")
# def admin_summary():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("SELECT COUNT(*) AS cnt FROM students")
#     total_students = cur.fetchone()["cnt"]

#     cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
#     total_teachers = cur.fetchone()["cnt"]

#     today = datetime.now().strftime("%Y-%m-%d")

#     cur.execute("""
#         SELECT COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s AND action='ENTRY'
#     """, (today,))
#     today_entries = cur.fetchone()["cnt"]

#     cur.execute("""
#         SELECT COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s AND action='EXIT'
#     """, (today,))
#     today_exits = cur.fetchone()["cnt"]

#     cur.execute("SELECT COUNT(*) AS cnt FROM logs")
#     total_logs = cur.fetchone()["cnt"]

#     cur.execute("""
#         SELECT COUNT(*) AS cnt
#         FROM logs
#         WHERE status='SKIP' AND DATE(scan_time)=%s
#     """, (today,))
#     skipping_alerts = cur.fetchone()["cnt"]

#     conn.close()

#     return {
#         "total_students": total_students,
#         "total_teachers": total_teachers,
#         "today_entries": today_entries,
#         "today_exits": today_exits,
#         "total_logs": total_logs,
#         "skipping_alerts": skipping_alerts
#     }



# @router.get("/stats/charts")
# def stats_charts():
#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     cur.execute("SELECT COUNT(*) AS cnt FROM students")
#     students = cur.fetchone()["cnt"]

#     cur.execute("SELECT COUNT(*) AS cnt FROM teachers")
#     teachers = cur.fetchone()["cnt"]

#     today = datetime.now().strftime("%Y-%m-%d")

#     cur.execute("""
#         SELECT COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s AND action='ENTRY'
#     """, (today,))
#     entry = cur.fetchone()["cnt"]

#     cur.execute("""
#         SELECT COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s AND action='EXIT'
#     """, (today,))
#     exitc = cur.fetchone()["cnt"]

#     cur.execute("""
#         SELECT HOUR(scan_time) AS hr, COUNT(*) AS cnt
#         FROM logs
#         WHERE DATE(scan_time)=%s
#         GROUP BY HOUR(scan_time)
#         ORDER BY hr
#     """, (today,))
#     rows = cur.fetchall()

#     conn.close()

#     return {
#         "members": {"students": students, "teachers": teachers},
#         "today": {"entry": entry, "exit": exitc},
#         "logs_by_hour": [{"hour": r["hr"], "count": r["cnt"]} for r in rows]
#     }


# @router.get("/filters")
# def get_filter_options():
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("SELECT DISTINCT department FROM students")
#     departments = [row["department"] for row in cursor.fetchall()]

#     cursor.execute("SELECT DISTINCT year FROM students")
#     years = [row["year"] for row in cursor.fetchall()]

#     cursor.execute("SELECT DISTINCT division FROM students")
#     divisions = [row["division"] for row in cursor.fetchall()]

#     conn.close()

#     return {
#         "departments": departments,
#         "years": years,
#         "divisions": divisions
#     }

# @router.get("/charts/members")
# def members_chart(
#     member_type: str = None,
#     department: str = None,
#     year: str = None,
#     division: str = None
# ):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     # ---------------- NO FILTER AT ALL ----------------
#     if not member_type:
#         cursor.execute("SELECT COUNT(*) AS count FROM students")
#         student_count = cursor.fetchone()["count"]

#         cursor.execute("SELECT COUNT(*) AS count FROM teachers")
#         teacher_count = cursor.fetchone()["count"]

#         conn.close()
#         return [
#             {"name": "Students", "value": student_count},
#             {"name": "Teachers", "value": teacher_count}
#         ]

#     # ---------------- STUDENT FILTER ----------------
#     if member_type == "student":
#         query = "SELECT COUNT(*) AS count FROM students WHERE 1=1"
#         params = []

#         # Apply ONLY selected filters
#         if department:
#             query += " AND department = %s"
#             params.append(department)

#         if year:
#             query += " AND year = %s"
#             params.append(year)

#         if division:
#             query += " AND division = %s"
#             params.append(division)

#         cursor.execute(query, params)
#         count = cursor.fetchone()["count"]

#         conn.close()
#         return [
#             {"name": "Students", "value": count}
#         ]

#     # ---------------- TEACHER FILTER ----------------
#     if member_type == "teacher":
#         query = "SELECT COUNT(*) AS count FROM teachers WHERE 1=1"
#         params = []

#         # Teachers only filtered by department
#         if department:
#             query += " AND department = %s"
#             params.append(department)

#         cursor.execute(query, params)
#         count = cursor.fetchone()["count"]

#         conn.close()
#         return [
#             {"name": "Teachers", "value": count}
#         ]
    

# @router.get("/filters/student/departments")
# def student_departments():
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("""
#         SELECT DISTINCT department 
#         FROM students 
#         ORDER BY department
#     """)
#     data = [row["department"] for row in cursor.fetchall()]

#     conn.close()
#     return data


# @router.get("/filters/student/years")
# def student_years(department: str = None):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     if department:
#         cursor.execute("""
#             SELECT DISTINCT year
#             FROM students
#             WHERE department = %s
#             ORDER BY year
#         """, (department,))
#     else:
#         cursor.execute("""
#             SELECT DISTINCT year
#             FROM students
#             ORDER BY year
#         """)

#     data = [row["year"] for row in cursor.fetchall()]
#     conn.close()
#     return data


# @router.get("/filters/student/divisions")
# def student_divisions(department: str = None, year: str = None):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     query = "SELECT DISTINCT division FROM students WHERE 1=1"
#     params = []

#     if department:
#         query += " AND department = %s"
#         params.append(department)

#     if year:
#         query += " AND year = %s"
#         params.append(year)

#     query += " ORDER BY division"

#     cursor.execute(query, params)
#     data = [row["division"] for row in cursor.fetchall()]

#     conn.close()
#     return data


# @router.get("/filters/teacher/departments")
# def teacher_departments():
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     cursor.execute("""
#         SELECT DISTINCT department
#         FROM teachers
#         ORDER BY department
#     """)

#     data = [row["department"] for row in cursor.fetchall()]
#     conn.close()
#     return data

# @router.get("/charts/department-wise")
# def department_wise_chart(
#     member_type: str = None,
#     year: str = None,
#     division: str = None
# ):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     # ---------- STUDENTS QUERY ----------
#     student_query = """
#         SELECT department, COUNT(*) AS students
#         FROM students
#         WHERE 1=1
#     """
#     student_params = []

#     if year:
#         student_query += " AND year = %s"
#         student_params.append(year)

#     if division:
#         student_query += " AND division = %s"
#         student_params.append(division)

#     student_query += " GROUP BY department"

#     cursor.execute(student_query, student_params)
#     student_data = cursor.fetchall()

#     # ---------- TEACHERS QUERY ----------
#     cursor.execute("""
#         SELECT department, COUNT(*) AS teachers
#         FROM teachers
#         GROUP BY department
#     """)
#     teacher_data = cursor.fetchall()

#     conn.close()

#     # ---------- MERGE DATA DYNAMICALLY ----------
#     result = {}

#     for row in student_data:
#         dept = row["department"]
#         result.setdefault(dept, {"department": dept, "students": 0, "teachers": 0})
#         result[dept]["students"] = row["students"]

#     for row in teacher_data:
#         dept = row["department"]
#         result.setdefault(dept, {"department": dept, "students": 0, "teachers": 0})
#         result[dept]["teachers"] = row["teachers"]

#     data = list(result.values())

#     # ---------- MEMBER TYPE FILTER ----------
#     if member_type == "student":
#         for d in data:
#             d["teachers"] = 0

#     if member_type == "teacher":
#         for d in data:
#             d["students"] = 0

#     return data


# # line chart....
# @router.get("/charts/attendance-timeline")
# def attendance_timeline(
#     date: str = None,
#     start_hour: int = 8,
#     end_hour: int = 18
# ):
#     conn = get_db_connection()
#     cursor = conn.cursor(dictionary=True)

#     date_condition = "CURDATE()" if not date else "%s"

#     query = f"""
#         SELECT
#             HOUR(scan_time) AS hr,
#             SUM(action='ENTRY') AS entry_count,
#             SUM(action='EXIT') AS exit_count
#         FROM logs
#         WHERE DATE(scan_time) = {date_condition}
#           AND HOUR(scan_time) BETWEEN %s AND %s
#         GROUP BY hr
#         ORDER BY hr
#     """

#     params = []
#     if date:
#         params.append(date)
#     params.extend([start_hour, end_hour])

#     cursor.execute(query, params)
#     rows = cursor.fetchall()
#     conn.close()

#     timeline = []
#     for h in range(start_hour, end_hour + 1):
#         label = f"{h if h<=12 else h-12} {'AM' if h<12 else 'PM'}"
#         row = next((r for r in rows if r["hr"] == h), None)
#         timeline.append({
#             "time": label,
#             "entry": row["entry_count"] if row else 0,
#             "exit": row["exit_count"] if row else 0,
#             "skip": 0
#         })

#     return timeline

