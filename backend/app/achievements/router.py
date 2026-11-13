from typing import List
from fastapi import APIRouter, Depends
from app.database.session import get_db
from app.core.security import get_current_user_payload
from app.schemas.all_schemas import AchievementResponse

router = APIRouter(prefix="/api/achievements", tags=["Gamification"])

@router.get("", response_model=List[AchievementResponse])
def get_student_achievements(user_payload: dict = Depends(get_current_user_payload)):
    user_id = user_payload["sub"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.id, a.code, a.title, a.description, a.badge_icon, a.xp_reward,
               sa.unlocked_at,
               CASE WHEN sa.achievement_id IS NOT NULL THEN 1 ELSE 0 END as is_unlocked,
               c.title AS course_title
        FROM achievements a
        LEFT JOIN student_achievements sa ON a.id = sa.achievement_id AND sa.user_id = %s
        LEFT JOIN courses c ON c.completion_achievement_id = a.id
        ORDER BY (c.id IS NOT NULL) ASC, a.xp_reward ASC;
        """, (user_id,))
        rows = cursor.fetchall()

        result = []
        for r in rows:
            result.append(AchievementResponse(
                id=r["id"],
                code=r["code"],
                title=r["title"],
                description=r["description"],
                badge_icon=r["badge_icon"],
                xp_reward=r["xp_reward"],
                unlocked=bool(r["is_unlocked"]),
                unlocked_at=r["unlocked_at"].isoformat() if r["unlocked_at"] else None,
                category="course" if r["course_title"] else "general",
                course_title=r["course_title"]
            ))
        return result
