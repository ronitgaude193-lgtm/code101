import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from app.database.session import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_payload
)
from app.schemas.all_schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    StudentProfileResponse,
    StudentProfileUpdate
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
def register(req: UserRegister):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s;", (req.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A student with this email address is already registered."
            )

        user_id = str(uuid.uuid4())
        hashed = hash_password(req.password)
        cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s, 'student');
        """, (user_id, req.email, hashed, req.full_name))

        # Create student profile
        cursor.execute("""
        INSERT INTO student_profiles (user_id, current_level, total_xp, streak_days, preferred_language, bio)
        VALUES (%s, 1, 0, 1, %s, 'Aspiring Software Engineer');
        """, (user_id, req.preferred_language or "python"))

        # Seed initial achievement: Welcome
        token = create_access_token({"sub": user_id, "email": req.email, "role": "student"})

        user_resp = UserResponse(
            id=user_id,
            email=req.email,
            full_name=req.full_name,
            role="student",
            created_at=""
        )
        return TokenResponse(access_token=token, user=user_resp)

@router.post("/login", response_model=TokenResponse)
def login(req: UserLogin):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, email, password_hash, full_name, role, created_at
        FROM users WHERE email = %s;
        """, (req.email,))
        user_row = cursor.fetchone()

        if not user_row or not verify_password(req.password, user_row["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        token = create_access_token({
            "sub": user_row["id"],
            "email": user_row["email"],
            "role": user_row["role"]
        })

        user_resp = UserResponse(
            id=user_row["id"],
            email=user_row["email"],
            full_name=user_row["full_name"],
            role=user_row["role"],
            created_at=str(user_row["created_at"])
        )
        return TokenResponse(access_token=token, user=user_resp)

@router.get("/me", response_model=StudentProfileResponse)
def get_current_profile(user_payload: dict = Depends(get_current_user_payload)):
    user_id = user_payload["sub"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT u.id, u.email, u.full_name, p.current_level, p.total_xp, p.streak_days, p.last_active_date, p.preferred_language, p.bio
        FROM users u
        LEFT JOIN student_profiles p ON u.id = p.user_id
        WHERE u.id = %s;
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Student profile not found")

        return StudentProfileResponse(
            user_id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            current_level=row["current_level"] or 1,
            total_xp=row["total_xp"] or 0,
            streak_days=row["streak_days"] or 0,
            last_active_date=row["last_active_date"],
            preferred_language=row["preferred_language"] or "python",
            bio=row["bio"] or ""
        )

@router.put("/profile", response_model=StudentProfileResponse)
def update_profile(req: StudentProfileUpdate, user_payload: dict = Depends(get_current_user_payload)):
    user_id = user_payload["sub"]
    with get_db() as conn:
        cursor = conn.cursor()
        if req.full_name:
            cursor.execute("UPDATE users SET full_name = %s WHERE id = %s;", (req.full_name, user_id))
        if req.preferred_language:
            cursor.execute("UPDATE student_profiles SET preferred_language = %s WHERE user_id = %s;", (req.preferred_language, user_id))
        if req.bio is not None:
            cursor.execute("UPDATE student_profiles SET bio = %s WHERE user_id = %s;", (req.bio, user_id))

    return get_current_profile(user_payload)
