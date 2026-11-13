import uuid
import json
from typing import List, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from app.database.session import get_db
from app.core.security import get_optional_user_payload, get_current_user_payload
from app.schemas.all_schemas import (
    ChallengeSummary,
    ChallengeDetail,
    ChallengeCreate,
    TestCase
)

router = APIRouter(prefix="/api/challenges", tags=["Challenges"])

@router.get("", response_model=List[ChallengeSummary])
def list_challenges(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    user_payload: Optional[dict] = Depends(get_optional_user_payload)
):
    with get_db() as conn:
        cursor = conn.cursor()
        uid = user_payload.get("sub") if user_payload else None
        # Private challenges are only listed for their creator.
        query = "SELECT id, title, slug, topic, difficulty, description, xp_reward, visibility, created_by FROM coding_challenges WHERE (visibility = 'public' OR created_by = %s)"
        params = [uid]
        if topic:
            query += " AND topic LIKE %s"
            params.append(f"%{topic}%")
        if difficulty:
            query += " AND difficulty = %s"
            params.append(difficulty)

        query += " ORDER BY created_at ASC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Check solved ids for current user
        solved_ids = set()
        if user_payload and "sub" in user_payload:
            cursor.execute("SELECT DISTINCT challenge_id FROM code_submissions WHERE user_id = %s AND status = 'Accepted';", (user_payload["sub"],))
            solved_ids = {r["challenge_id"] for r in cursor.fetchall()}

        result = []
        for r in rows:
            result.append(ChallengeSummary(
                id=r["id"],
                title=r["title"],
                slug=r["slug"],
                topic=r["topic"],
                difficulty=r["difficulty"],
                description=r["description"],
                xp_reward=r["xp_reward"],
                solved=r["id"] in solved_ids,
                visibility=r["visibility"],
                is_mine=uid is not None and r["created_by"] == uid
            ))
        return result

@router.get("/{id_or_slug}", response_model=ChallengeDetail)
def get_challenge(id_or_slug: str, user_payload: Optional[dict] = Depends(get_optional_user_payload)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, title, slug, topic, difficulty, description, initial_code, solution_code, test_cases, constraints, hints, xp_reward,
               visibility, created_by
        FROM coding_challenges
        WHERE (id = %s OR slug = %s) AND (visibility = 'public' OR created_by = %s);
        """, (id_or_slug, id_or_slug, user_payload.get("sub") if user_payload else None))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Challenge not found")

        is_solved = False
        if user_payload and "sub" in user_payload:
            cursor.execute("SELECT id FROM code_submissions WHERE user_id = %s AND challenge_id = %s AND status = 'Accepted';", (user_payload["sub"], row["id"]))
            is_solved = bool(cursor.fetchone())

        raw_tcs = json.loads(row["test_cases"])
        test_cases = [TestCase(**tc) for tc in raw_tcs]
        hints = json.loads(row["hints"]) if row["hints"] else []

        return ChallengeDetail(
            id=row["id"],
            title=row["title"],
            slug=row["slug"],
            topic=row["topic"],
            difficulty=row["difficulty"],
            description=row["description"],
            initial_code=row["initial_code"],
            solution_code=None, # Never reveal solution code in API response to students
            test_cases=test_cases,
            constraints=row["constraints"],
            hints=hints,
            xp_reward=row["xp_reward"],
            solved=is_solved,
            visibility=row["visibility"],
            is_mine=bool(user_payload) and row["created_by"] == user_payload.get("sub")
        )

@router.post("/generate", response_model=ChallengeDetail)
def generate_personalized_challenge(
    topic: str = "Loops & Lists",
    difficulty: str = "Beginner",
    visibility: Literal["private", "public"] = "private",
    user_payload: dict = Depends(get_current_user_payload)
):
    """
    AI Challenge Generator (MODULE I): Creates and registers a validated personalized practice challenge.
    """
    ch_id = f"gen_{uuid.uuid4().hex[:8]}"
    slug = f"practice-{topic.lower().replace(' ', '-').replace('&', 'and')}-{ch_id[-4:]}"

    # Educational templates tailored to topic
    if "loop" in topic.lower():
        title = "Count Even Numbers in List"
        desc = "Write a function `count_evens(nums)` that takes a list of integers and counts how many even numbers it contains."
        initial = "def count_evens(nums):\n    # Return the count of even numbers\n    pass\n"
        solution = "def count_evens(nums):\n    return sum(1 for x in nums if x % 2 == 0)\n"
        tcs = [
            {"input": "[1, 2, 3, 4, 6]", "expected_output": "3", "hidden": False},
            {"input": "[1, 3, 5]", "expected_output": "0", "hidden": False},
            {"input": "[0, -2, 4]", "expected_output": "3", "hidden": True}
        ]
        hints = [
            "An integer `x` is even if `x % 2 == 0`.",
            "Use an accumulator counter or a list comprehension with `sum()`."
        ]
    elif "string" in topic.lower():
        title = "Check Palindrome String"
        desc = "Write a function `is_palindrome(s)` that returns True if the string reads the same backwards and forwards (ignoring case), False otherwise."
        initial = "def is_palindrome(s):\n    # Return True or False\n    pass\n"
        solution = "def is_palindrome(s):\n    s = s.lower()\n    return s == s[::-1]\n"
        tcs = [
            {"input": "'racecar'", "expected_output": "true", "hidden": False},
            {"input": "'python'", "expected_output": "false", "hidden": False},
            {"input": "'Madam'", "expected_output": "true", "hidden": True}
        ]
        hints = [
            "Convert the string to lowercase first using `.lower()`.",
            "Compare the string against its reversed slice `s[::-1]`."
        ]
    else:
        title = f"Targeted Practice: {topic}"
        desc = f"Write a function `solve_problem(items)` that processes the elements according to {topic} principles."
        initial = "def solve_problem(items):\n    # Your implementation here\n    pass\n"
        solution = "def solve_problem(items):\n    return len(items)\n"
        tcs = [
            {"input": "[1, 2, 3]", "expected_output": "3", "hidden": False},
            {"input": "[]", "expected_output": "0", "hidden": False}
        ]
        hints = ["Start by verifying what the function should do when given empty inputs."]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO coding_challenges (id, title, slug, topic, difficulty, description, initial_code, solution_code, test_cases, constraints, hints, xp_reward, created_by, visibility)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            ch_id,
            title,
            slug,
            topic,
            difficulty,
            desc,
            initial,
            solution,
            json.dumps(tcs),
            "Handle standard Python inputs safely.",
            json.dumps(hints),
            50,
            user_payload["sub"],
            visibility
        ))

    return get_challenge(ch_id, user_payload)
