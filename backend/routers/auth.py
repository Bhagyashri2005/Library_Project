from fastapi import APIRouter
from database import get_db_connection
from schemas import AdminLoginRequest
from schemas import AdminProfileResponse
from fastapi import HTTPException
from schemas import UpdateAdminRequest
from passlib.exc import UnknownHashError
from utils import verify_password, hash_password


router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/login")
def admin_login(data: AdminLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s LIMIT 1",
        (data.username,)
    )
    admin = cursor.fetchone()
    conn.close()

    if not admin:
        return {"status": "failed", "message": "Invalid credentials"}

    if not verify_password(data.password, admin["password_hash"]):
        return {"status": "failed", "message": "Invalid credentials"}

    return {
        "status": "success",
        "username": admin["username"],
        "role": admin["role"]
    }



@router.get("/profile", response_model=AdminProfileResponse)
def get_admin_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT username, role FROM admin LIMIT 1")
    admin = cursor.fetchone()

    conn.close()

    if not admin:
        return {"username": "", "role": ""}

    return admin

from passlib.exc import UnknownHashError

@router.put("/update-profile")
def update_admin_profile(data: UpdateAdminRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admin LIMIT 1")
        admin = cursor.fetchone()

        if not admin:
            raise HTTPException(status_code=404, detail="Admin not found")

        # DEBUG (temporary)
        print("OLD PASSWORD INPUT:", data.old_password)
        print("HASH FROM DB:", admin["password_hash"])

        try:
            is_valid = verify_password(
                data.old_password,
                admin["password_hash"]
            )
        except UnknownHashError:
            raise HTTPException(
                status_code=400,
                detail="Stored password is not a valid bcrypt hash"
            )

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Old password is incorrect"
            )

        new_hashed_password = hash_password(data.new_password)

        cursor.execute(
            "UPDATE admin SET username=%s, password_hash=%s WHERE admin_id=%s",
            (data.username, new_hashed_password, admin["admin_id"])
        )

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "message": "Admin credentials updated successfully"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print("UNEXPECTED ERROR:", str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error (check backend logs)"
        )
