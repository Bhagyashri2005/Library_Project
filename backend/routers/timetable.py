from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from database import get_db_connection
import csv, io

router = APIRouter(prefix="/admin/timetable", tags=["Timetable"])


# ======================================================
# GET TIMETABLE
# ======================================================
def normalize_time(t):
    if isinstance(t, int):
        h = t // 3600
        m = (t % 3600) // 60
        return f"{h:02d}:{m:02d}"
    else:
        parts = str(t).split(":")
        h = parts[0].zfill(2)
        m = parts[1][:2]
        return f"{h}:{m}"
    
def to_12_hour(time_str):
    """
    Converts 'HH:MM' -> 'HH:MM AM/PM'
    """
    h, m = map(int, time_str.split(":"))
    ampm = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    return f"{h:02d}:{m:02d} {ampm}"



@router.get("/")
def get_timetable(
    role: str = Query(None),            # student / teacher
    department: str = Query(None),
    year: str = Query(None),
    division: str = Query(None),
    batch: str = Query(None),
    teacher_id: str = Query(None),
    day_of_week: str = Query(None)
):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    query = "SELECT * FROM timetable WHERE 1=1"
    params = []

    if role == "student":
        if department:
            query += " AND department=%s"
            params.append(department)
        if year:
            query += " AND year=%s"
            params.append(year)
        if division:
            query += " AND division=%s"
            params.append(division)

        # lecture → batch NULL | practical → batch match
        if batch:
            query += " AND (batch IS NULL OR batch=%s)"
            params.append(batch)

    elif role == "teacher" and teacher_id:
        query += " AND teacher_id=%s"
        params.append(teacher_id)

    if day_of_week:
        day_of_week = day_of_week.strip().capitalize()
        query += " AND day_of_week=%s"
        params.append(day_of_week)

    query += " ORDER BY day_of_week, start_time"

    cur.execute(query, params)
    data = cur.fetchall()

    # 🔧 NORMALIZE TIME FORMAT FOR FRONTEND
    for row in data:
        # normalize to HH:MM first
        start = normalize_time(row["start_time"])
        end = normalize_time(row["end_time"])

        # convert to 12-hour
        row["start_time"] = to_12_hour(start)
        row["end_time"] = to_12_hour(end)


    conn.close()
    return data


# ======================================================
# ADD TIMETABLE ENTRY
# ======================================================
@router.post("/add")
def add_timetable_entry(
    department: str = Form(...),
    year: str = Form(...),
    division: str = Form(...),
    subject: str = Form(...),
    teacher_id: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    type: str = Form(...),           # Lecture / Practical
    batch: str = Form(None)
):
    conn = get_db_connection()
    cur = conn.cursor()

    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_of_week = day_of_week.strip().capitalize()

    if day_of_week not in valid_days:
        raise HTTPException(status_code=400, detail="Invalid day_of_week")

    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    if type not in ["Lecture", "Practical"]:
        raise HTTPException(status_code=400, detail="Invalid class type")

    if type == "Practical" and not batch:
        raise HTTPException(status_code=400, detail="Batch required for practical")

    if type == "Lecture":
        batch = None

    # ---------- CLASS CLASH ----------
    cur.execute("""
        SELECT 1 FROM timetable
        WHERE department=%s AND year=%s AND division=%s
          AND day_of_week=%s
          AND (%s < end_time AND %s > start_time)
          AND (batch IS NULL OR batch=%s)
    """, (department, year, division, day_of_week, start_time, end_time, batch))

    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Class timetable clash detected")

    # ---------- TEACHER CLASH ----------
    cur.execute("""
        SELECT 1 FROM timetable
        WHERE teacher_id=%s AND day_of_week=%s
          AND (%s < end_time AND %s > start_time)
    """, (teacher_id, day_of_week, start_time, end_time))

    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Teacher already assigned in this slot")

    # ---------- INSERT ----------
    cur.execute("""
        INSERT INTO timetable
        (department, year, division, batch, subject, teacher_id,
         day_of_week, start_time, end_time, type)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        department, year, division, batch,
        subject, teacher_id, day_of_week,
        start_time, end_time, type
    ))

    conn.commit()
    conn.close()
    return {"status": "success"}


# ======================================================
# BULK UPLOAD TIMETABLE
# ======================================================
@router.post("/upload")
def upload_timetable(file: UploadFile = File(...)):
    conn = get_db_connection()
    cur = conn.cursor()

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    added = 0
    skipped = 0

    for row in reader:
        try:
            day_of_week = row["day_of_week"].strip().capitalize()
            start_time = normalize_time(row["start_time"])
            end_time = normalize_time(row["end_time"])
            type = row["type"]
            batch = row.get("batch")

            if day_of_week not in valid_days:
                skipped += 1
                continue

            if type not in ["Lecture", "Practical"]:
                skipped += 1
                continue

            if start_time >= end_time:
                skipped += 1
                continue

            if type == "Practical" and not batch:
                skipped += 1
                continue

            if type == "Lecture":
                batch = None   # ✅ THIS WAS MISSING

            # class clash
            cur.execute("""
                SELECT 1 FROM timetable
                WHERE department=%s AND year=%s AND division=%s
                AND day_of_week=%s
                AND (%s < end_time AND %s > start_time)
                AND (batch IS NULL OR batch=%s)
            """, (
                row["department"], row["year"], row["division"],
                day_of_week, start_time, end_time, batch
            ))

            if cur.fetchone():
                skipped += 1
                continue

            # teacher clash
            cur.execute("""
                SELECT 1 FROM timetable
                WHERE teacher_id=%s AND day_of_week=%s
                AND (%s < end_time AND %s > start_time)
            """, (row["teacher_id"], day_of_week, start_time, end_time))

            if cur.fetchone():
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO timetable
                (department, year, division, batch, subject,
                teacher_id, day_of_week, start_time, end_time, type)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                row["department"], row["year"], row["division"],
                batch, row["subject"], row["teacher_id"],
                day_of_week, start_time, end_time, type
            ))

            added += 1

        except Exception:
            skipped += 1


    conn.commit()
    conn.close()
    return {"status": "success", "added": added, "skipped": skipped}


@router.put("/update/{timetable_id}")
def update_timetable_entry(
    timetable_id: int,
    department: str = Form(...),
    year: str = Form(...),
    division: str = Form(...),
    subject: str = Form(...),
    teacher_id: str = Form(...),
    day_of_week: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    type: str = Form(...),
    batch: str = Form(None)
):
    conn = get_db_connection()
    cur = conn.cursor()

    # existence check
    cur.execute(
        "SELECT timetable_id FROM timetable WHERE timetable_id=%s",
        (timetable_id,)
    )
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    day_of_week = day_of_week.strip().capitalize()
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    if day_of_week not in valid_days:
        raise HTTPException(status_code=400, detail="Invalid day_of_week")

    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Invalid time range")

    if type == "Practical" and not batch:
        raise HTTPException(status_code=400, detail="Batch required for practical")

    if type == "Lecture":
        batch = None

    # class clash
    cur.execute("""
        SELECT 1 FROM timetable
        WHERE timetable_id != %s
          AND department=%s AND year=%s AND division=%s
          AND day_of_week=%s
          AND (%s < end_time AND %s > start_time)
          AND (batch IS NULL OR batch=%s)
    """, (
        timetable_id, department, year, division,
        day_of_week, start_time, end_time, batch
    ))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Class timetable clash detected")

    # teacher clash
    cur.execute("""
        SELECT 1 FROM timetable
        WHERE timetable_id != %s
          AND teacher_id=%s AND day_of_week=%s
          AND (%s < end_time AND %s > start_time)
    """, (
        timetable_id, teacher_id, day_of_week,
        start_time, end_time
    ))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Teacher timetable clash detected")

    # update
    cur.execute("""
        UPDATE timetable
        SET department=%s, year=%s, division=%s, batch=%s,
            subject=%s, teacher_id=%s, day_of_week=%s,
            start_time=%s, end_time=%s, type=%s
        WHERE timetable_id=%s
    """, (
        department, year, division, batch,
        subject, teacher_id, day_of_week,
        start_time, end_time, type, timetable_id
    ))

    conn.commit()
    conn.close()
    return {"status": "success", "message": "Timetable updated successfully"}


# ======================================================
# FILTER OPTIONS
# ======================================================
@router.get("/filters")
def get_timetable_filters(
    department: str = Query(None),
    year: str = Query(None),
    division: str = Query(None)
):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT DISTINCT department FROM timetable ORDER BY department")
    departments = [r["department"] for r in cur.fetchall()]

    years = []
    if department:
        cur.execute("SELECT DISTINCT year FROM timetable WHERE department=%s", (department,))
        years = [r["year"] for r in cur.fetchall()]

    divisions = []
    if department and year:
        cur.execute(
            "SELECT DISTINCT division FROM timetable WHERE department=%s AND year=%s",
            (department, year)
        )
        divisions = [r["division"] for r in cur.fetchall()]

    batches = []
    if department and year and division:
        cur.execute("""
            SELECT DISTINCT batch FROM timetable
            WHERE department=%s AND year=%s AND division=%s AND batch IS NOT NULL
        """, (department, year, division))
        batches = [r["batch"] for r in cur.fetchall()]

    conn.close()
    return {
        "departments": departments,
        "years": years,
        "divisions": divisions,
        "batches": batches
    }

# ======================================================
# DELETE TIMETABLE ENTRY
# ======================================================
@router.delete("/delete/{timetable_id}")
def delete_timetable_entry(timetable_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT timetable_id FROM timetable WHERE timetable_id=%s",
        (timetable_id,)
    )
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    cur.execute(
        "DELETE FROM timetable WHERE timetable_id=%s",
        (timetable_id,)
    )

    conn.commit()
    conn.close()

    return {"status": "success", "message": "Timetable entry deleted"}
