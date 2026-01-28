from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import get_db_connection
import csv
import io
import re
from utils import normalize_text   # ✅ ADDED

router = APIRouter(prefix="/admin/members", tags=["Members"])


# ======================================================
# VALIDATION HELPERS
# ======================================================
def is_valid_email(email: str) -> bool:
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


def is_valid_contact(contact: str) -> bool:
    return contact.isdigit() and len(contact) == 10


# ======================================================
# GET MEMBERS (WITH PAGINATION + FILTERS)
# ======================================================
@router.get("/{role}")
def get_members(
    role: str,
    page: int = 1,
    page_size: int = 10,
    department: str = "",
    year: str = "",
    division: str = "",
    batch: str = ""
):
    role = normalize_text(role, "lower")              # ✅ ADDED
    department = normalize_text(department, "upper")  # ✅ ADDED
    year = normalize_text(year, "upper")              # ✅ ADDED
    division = normalize_text(division, "upper")      # ✅ ADDED
    batch = normalize_text(batch, "upper")            # ✅ ADDED

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    conditions = []
    params = []

    if department:
        conditions.append("department = %s")
        params.append(department)

    if role == "student":
        if year:
            conditions.append("year = %s")
            params.append(year)
        if division:
            conditions.append("division = %s")
            params.append(division)
        if batch:
            conditions.append("batch = %s")
            params.append(batch)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    table = "students" if role == "student" else "teachers"
    id_col = "student_id" if role == "student" else "teacher_id"

    cur.execute(
        f"SELECT COUNT(*) AS total FROM {table} {where_clause}",
        params
    )
    total = cur.fetchone()["total"]
    total_pages = max(1, (total + page_size - 1) // page_size)
    offset = (page - 1) * page_size

    cur.execute(
        f"""
        SELECT *
        FROM {table}
        {where_clause}
        ORDER BY {id_col}
        LIMIT %s OFFSET %s
        """,
        params + [page_size, offset]
    )

    rows = cur.fetchall()
    conn.close()

    return {
        "data": rows,
        "total_pages": total_pages
    }


# ======================================================
# FILTER VALUES (DB DRIVEN)
# ======================================================
@router.get("/filters/{role}")
def get_member_filters(role: str):
    role = normalize_text(role, "lower")   # ✅ ADDED

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if role == "teacher":
        cur.execute("SELECT DISTINCT department FROM teachers ORDER BY department")
        data = {"departments": [r["department"] for r in cur.fetchall()]}

    else:
        cur.execute("SELECT DISTINCT department FROM students ORDER BY department")
        departments = [r["department"] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT year FROM students ORDER BY year")
        years = [r["year"] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT division FROM students ORDER BY division")
        divisions = [r["division"] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT batch FROM students ORDER BY batch")
        batches = [r["batch"] for r in cur.fetchall()]

        data = {
            "departments": departments,
            "years": years,
            "divisions": divisions,
            "batches": batches
        }

    conn.close()
    return data


# ======================================================
# ADD SINGLE MEMBER (WITH FULL VALIDATION)
# ======================================================
@router.post("/add")
def add_member(
    role: str = Form(...),
    member_id: str = Form(...),
    name: str = Form(...),
    department: str = Form(...),
    year: str = Form(None),
    division: str = Form(None),
    batch: str = Form(None),
    email: str = Form(...),
    contact_no: str = Form(...),
    designation: str = Form(None)
):
    role = normalize_text(role, "lower")               # ✅ ADDED
    member_id = normalize_text(member_id, "upper")     # ✅ ADDED
    department = normalize_text(department, "upper")   # ✅ ADDED
    year = normalize_text(year, "upper")               # ✅ ADDED
    division = normalize_text(division, "upper")       # ✅ ADDED
    batch = normalize_text(batch, "upper")             # ✅ ADDED
    email = normalize_text(email, "lower")             # ✅ ADDED
    designation = normalize_text(designation, "title") # ✅ ADDED

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if not is_valid_contact(contact_no):
        raise HTTPException(status_code=400, detail="Contact number must be 10 digits")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if role == "student":
            if not (year and division and batch):
                raise HTTPException(
                    status_code=400,
                    detail="Year, division and batch are required for student"
                )

            cur.execute("SELECT 1 FROM students WHERE student_id=%s", (member_id,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Student ID already exists")

            cur.execute("""
                INSERT INTO students
                (student_id, name, department, year, division, batch, email, contact_no)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                member_id, name, department,
                year, division, batch,
                email, contact_no
            ))

        else:
            if not designation:
                raise HTTPException(status_code=400, detail="Designation required")

            cur.execute("SELECT 1 FROM teachers WHERE teacher_id=%s", (member_id,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Teacher ID already exists")

            cur.execute("""
                INSERT INTO teachers
                (teacher_id, name, department, email, contact_no, designation)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                member_id, name, department,
                email, contact_no, designation
            ))

        conn.commit()

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    return {"status": "success"}


# ======================================================
# BULK UPLOAD (CSV – SKIP DUPLICATES)
# ======================================================
@router.post("/upload")
def upload_members(
    role: str = Form(...),
    file: UploadFile = File(...)
):
    role = normalize_text(role, "lower")  # ✅ ADDED

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    conn = get_db_connection()
    cur = conn.cursor()

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    added = 0
    skipped = 0

    try:
        for row in reader:
            try:
                if role == "student":
                    row["student_id"] = normalize_text(row["student_id"], "upper")
                    row["department"] = normalize_text(row["department"], "upper")
                    row["year"] = normalize_text(row["year"], "upper")
                    row["division"] = normalize_text(row["division"], "upper")
                    row["batch"] = normalize_text(row["batch"], "upper")
                    row["email"] = normalize_text(row["email"], "lower")

                    cur.execute("SELECT 1 FROM students WHERE student_id=%s", (row["student_id"],))
                    if cur.fetchone():
                        skipped += 1
                        continue

                    cur.execute("""
                        INSERT INTO students
                        (student_id, name, department, year, division, batch, email, contact_no)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """, (
                        row["student_id"], row["name"], row["department"],
                        row["year"], row["division"], row["batch"],
                        row["email"], row["contact_no"]
                    ))
                else:
                    row["teacher_id"] = normalize_text(row["teacher_id"], "upper")
                    row["department"] = normalize_text(row["department"], "upper")
                    row["email"] = normalize_text(row["email"], "lower")
                    row["designation"] = normalize_text(row["designation"], "title")

                    cur.execute("SELECT 1 FROM teachers WHERE teacher_id=%s", (row["teacher_id"],))
                    if cur.fetchone():
                        skipped += 1
                        continue

                    cur.execute("""
                        INSERT INTO teachers
                        (teacher_id, name, department, email, contact_no, designation)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        row["teacher_id"], row["name"], row["department"],
                        row["email"], row["contact_no"], row["designation"]
                    ))

                added += 1
            except:
                skipped += 1

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    return {
        "status": "success",
        "added": added,
        "skipped": skipped
    }


# ======================================================
# UPDATE MEMBER (STUDENT / TEACHER)
# ======================================================
@router.put("/update")
def update_member(
    role: str = Form(...),
    member_id: str = Form(...),
    name: str = Form(...),
    department: str = Form(...),
    year: str = Form(None),
    division: str = Form(None),
    batch: str = Form(None),
    email: str = Form(...),
    contact_no: str = Form(...),
    designation: str = Form(None)
):
    role = normalize_text(role, "lower")               # ✅ ADDED
    member_id = normalize_text(member_id, "upper")     # ✅ ADDED
    department = normalize_text(department, "upper")   # ✅ ADDED
    year = normalize_text(year, "upper")               # ✅ ADDED
    division = normalize_text(division, "upper")       # ✅ ADDED
    batch = normalize_text(batch, "upper")             # ✅ ADDED
    email = normalize_text(email, "lower")             # ✅ ADDED
    designation = normalize_text(designation, "title") # ✅ ADDED

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    if not is_valid_contact(contact_no):
        raise HTTPException(status_code=400, detail="Contact number must be 10 digits")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        if role == "student":
            cur.execute(
                "SELECT 1 FROM students WHERE student_id=%s",
                (member_id,)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Student not found")

            if not (year and division and batch):
                raise HTTPException(
                    status_code=400,
                    detail="Year, division and batch required"
                )

            cur.execute("""
                UPDATE students
                SET name=%s,
                    department=%s,
                    year=%s,
                    division=%s,
                    batch=%s,
                    email=%s,
                    contact_no=%s
                WHERE student_id=%s
            """, (
                name, department, year, division, batch,
                email, contact_no, member_id
            ))

        else:
            cur.execute(
                "SELECT 1 FROM teachers WHERE teacher_id=%s",
                (member_id,)
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Teacher not found")

            if not designation:
                raise HTTPException(
                    status_code=400,
                    detail="Designation is required"
                )

            cur.execute("""
                UPDATE teachers
                SET name=%s,
                    department=%s,
                    email=%s,
                    contact_no=%s,
                    designation=%s
                WHERE teacher_id=%s
            """, (
                name, department,
                email, contact_no,
                designation, member_id
            ))

        conn.commit()

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    return {
        "status": "success",
        "message": f"{role.capitalize()} updated successfully"
    }


# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from database import get_db_connection
# import csv
# import io
# import re

# router = APIRouter(prefix="/admin/members", tags=["Members"])


# # ======================================================
# # VALIDATION HELPERS
# # ======================================================
# def is_valid_email(email: str) -> bool:
#     return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email) is not None


# def is_valid_contact(contact: str) -> bool:
#     return contact.isdigit() and len(contact) == 10


# # ======================================================
# # GET MEMBERS (WITH PAGINATION + FILTERS)
# # ======================================================
# @router.get("/{role}")
# def get_members(
#     role: str,
#     page: int = 1,
#     page_size: int = 10,
#     department: str = "",
#     year: str = "",
#     division: str = "",
#     batch: str = ""
# ):
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     conditions = []
#     params = []

#     if department:
#         conditions.append("department = %s")
#         params.append(department)

#     if role == "student":
#         if year:
#             conditions.append("year = %s")
#             params.append(year)
#         if division:
#             conditions.append("division = %s")
#             params.append(division)
#         if batch:
#             conditions.append("batch = %s")
#             params.append(batch)

#     where_clause = ""
#     if conditions:
#         where_clause = "WHERE " + " AND ".join(conditions)

#     table = "students" if role == "student" else "teachers"
#     id_col = "student_id" if role == "student" else "teacher_id"

#     # COUNT
#     cur.execute(
#         f"SELECT COUNT(*) AS total FROM {table} {where_clause}",
#         params
#     )
#     total = cur.fetchone()["total"]
#     total_pages = max(1, (total + page_size - 1) // page_size)
#     offset = (page - 1) * page_size

#     # DATA
#     cur.execute(
#         f"""
#         SELECT *
#         FROM {table}
#         {where_clause}
#         ORDER BY {id_col}
#         LIMIT %s OFFSET %s
#         """,
#         params + [page_size, offset]
#     )

#     rows = cur.fetchall()
#     conn.close()

#     return {
#         "data": rows,
#         "total_pages": total_pages
#     }


# # ======================================================
# # FILTER VALUES (DB DRIVEN)
# # ======================================================
# @router.get("/filters/{role}")
# def get_member_filters(role: str):
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     conn = get_db_connection()
#     cur = conn.cursor(dictionary=True)

#     if role == "teacher":
#         cur.execute("SELECT DISTINCT department FROM teachers ORDER BY department")
#         data = {"departments": [r["department"] for r in cur.fetchall()]}

#     else:
#         cur.execute("SELECT DISTINCT department FROM students ORDER BY department")
#         departments = [r["department"] for r in cur.fetchall()]

#         cur.execute("SELECT DISTINCT year FROM students ORDER BY year")
#         years = [r["year"] for r in cur.fetchall()]

#         cur.execute("SELECT DISTINCT division FROM students ORDER BY division")
#         divisions = [r["division"] for r in cur.fetchall()]

#         cur.execute("SELECT DISTINCT batch FROM students ORDER BY batch")
#         batches = [r["batch"] for r in cur.fetchall()]

#         data = {
#             "departments": departments,
#             "years": years,
#             "divisions": divisions,
#             "batches": batches
#         }

#     conn.close()
#     return data


# # ======================================================
# # ADD SINGLE MEMBER (WITH FULL VALIDATION)
# # ======================================================
# @router.post("/add")
# def add_member(
#     role: str = Form(...),
#     member_id: str = Form(...),
#     name: str = Form(...),
#     department: str = Form(...),
#     year: str = Form(None),
#     division: str = Form(None),
#     batch: str = Form(None),
#     email: str = Form(...),
#     contact_no: str = Form(...),
#     designation: str = Form(None)
# ):
#     # ---- COMMON VALIDATION ----
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     if not is_valid_email(email):
#         raise HTTPException(status_code=400, detail="Invalid email format")

#     if not is_valid_contact(contact_no):
#         raise HTTPException(status_code=400, detail="Contact number must be 10 digits")

#     conn = get_db_connection()
#     cur = conn.cursor()

#     try:
#         if role == "student":
#             if not (year and division and batch):
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Year, division and batch are required for student"
#                 )

#             # duplicate check
#             cur.execute("SELECT 1 FROM students WHERE student_id=%s", (member_id,))
#             if cur.fetchone():
#                 raise HTTPException(status_code=400, detail="Student ID already exists")

#             cur.execute("""
#                 INSERT INTO students
#                 (student_id, name, department, year, division, batch, email, contact_no)
#                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
#             """, (
#                 member_id, name, department,
#                 year, division, batch,
#                 email, contact_no
#             ))

#         else:
#             if not designation:
#                 raise HTTPException(status_code=400, detail="Designation required")

#             cur.execute("SELECT 1 FROM teachers WHERE teacher_id=%s", (member_id,))
#             if cur.fetchone():
#                 raise HTTPException(status_code=400, detail="Teacher ID already exists")

#             cur.execute("""
#                 INSERT INTO teachers
#                 (teacher_id, name, department, email, contact_no, designation)
#                 VALUES (%s,%s,%s,%s,%s,%s)
#             """, (
#                 member_id, name, department,
#                 email, contact_no, designation
#             ))

#         conn.commit()

#     except HTTPException:
#         conn.rollback()
#         raise
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
#     finally:
#         conn.close()

#     return {"status": "success"}


# # ======================================================
# # BULK UPLOAD (CSV – SKIP DUPLICATES)
# # ======================================================
# @router.post("/upload")
# def upload_members(
#     role: str = Form(...),
#     file: UploadFile = File(...)
# ):
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     conn = get_db_connection()
#     cur = conn.cursor()

#     content = file.file.read().decode("utf-8")
#     reader = csv.DictReader(io.StringIO(content))

#     added = 0
#     skipped = 0

#     try:
#         for row in reader:
#             try:
#                 if role == "student":
#                     cur.execute("SELECT 1 FROM students WHERE student_id=%s", (row["student_id"],))
#                     if cur.fetchone():
#                         skipped += 1
#                         continue

#                     cur.execute("""
#                         INSERT INTO students
#                         (student_id, name, department, year, division, batch, email, contact_no)
#                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
#                     """, (
#                         row["student_id"], row["name"], row["department"],
#                         row["year"], row["division"], row["batch"],
#                         row["email"], row["contact_no"]
#                     ))
#                 else:
#                     cur.execute("SELECT 1 FROM teachers WHERE teacher_id=%s", (row["teacher_id"],))
#                     if cur.fetchone():
#                         skipped += 1
#                         continue

#                     cur.execute("""
#                         INSERT INTO teachers
#                         (teacher_id, name, department, email, contact_no, designation)
#                         VALUES (%s,%s,%s,%s,%s,%s)
#                     """, (
#                         row["teacher_id"], row["name"], row["department"],
#                         row["email"], row["contact_no"], row["designation"]
#                     ))

#                 added += 1
#             except:
#                 skipped += 1

#         conn.commit()

#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
#     finally:
#         conn.close()

#     return {
#         "status": "success",
#         "added": added,
#         "skipped": skipped
#     }

# # ======================================================
# # UPDATE MEMBER (STUDENT / TEACHER)
# # ======================================================
# @router.put("/update")
# def update_member(
#     role: str = Form(...),
#     member_id: str = Form(...),
#     name: str = Form(...),
#     department: str = Form(...),
#     year: str = Form(None),
#     division: str = Form(None),
#     batch: str = Form(None),
#     email: str = Form(...),
#     contact_no: str = Form(...),
#     designation: str = Form(None)
# ):
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     if not is_valid_email(email):
#         raise HTTPException(status_code=400, detail="Invalid email format")

#     if not is_valid_contact(contact_no):
#         raise HTTPException(status_code=400, detail="Contact number must be 10 digits")

#     conn = get_db_connection()
#     cur = conn.cursor()

#     try:
#         if role == "student":
#             # check exists
#             cur.execute(
#                 "SELECT 1 FROM students WHERE student_id=%s",
#                 (member_id,)
#             )
#             if not cur.fetchone():
#                 raise HTTPException(status_code=404, detail="Student not found")

#             if not (year and division and batch):
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Year, division and batch required"
#                 )

#             cur.execute("""
#                 UPDATE students
#                 SET name=%s,
#                     department=%s,
#                     year=%s,
#                     division=%s,
#                     batch=%s,
#                     email=%s,
#                     contact_no=%s
#                 WHERE student_id=%s
#             """, (
#                 name, department, year, division, batch,
#                 email, contact_no, member_id
#             ))

#         else:  # teacher
#             cur.execute(
#                 "SELECT 1 FROM teachers WHERE teacher_id=%s",
#                 (member_id,)
#             )
#             if not cur.fetchone():
#                 raise HTTPException(status_code=404, detail="Teacher not found")

#             if not designation:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Designation is required"
#                 )

#             cur.execute("""
#                 UPDATE teachers
#                 SET name=%s,
#                     department=%s,
#                     email=%s,
#                     contact_no=%s,
#                     designation=%s
#                 WHERE teacher_id=%s
#             """, (
#                 name, department,
#                 email, contact_no,
#                 designation, member_id
#             ))

#         conn.commit()

#     except HTTPException:
#         conn.rollback()
#         raise
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=str(e))
#     finally:
#         conn.close()

#     return {
#         "status": "success",
#         "message": f"{role.capitalize()} updated successfully"
#     }
