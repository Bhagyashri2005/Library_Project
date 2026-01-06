from pydantic import BaseModel

class ScanRequest(BaseModel):
    user_id: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# ================== SETTINGS SCHEMAS ==================

class AdminProfileResponse(BaseModel):
    username: str
    role: str

class UpdateAdminRequest(BaseModel):
    username: str
    old_password: str
    new_password: str
