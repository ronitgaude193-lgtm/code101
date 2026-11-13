import psycopg
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from app.schemas.all_schemas import (
    SkillProgress,
    WeaknessItem,
    ProgrammingDNAResponse,
    DashboardResponse,
    StudentProfileResponse,
    ChallengeSummary
)

SKILL_TOPICS = [
    "Variables & Data Types",
    "Conditions",
    "Loops & Lists",
    "Functions",
    "Strings",
    "Recursion",
    "Data Structures",
    "Algorithms"
]

class AdaptiveLearningEngine:
    def record_submission_event(
        self,
        conn: psycopg.Connection,
        user_id: str,
        challenge_id: Optional[str],
        status: str,
        execution_time: float,
        error_type: Optional[str]
    ) -> Dict[str, Any]:
        """
        Updates student skills, XP, streak, and checks unlocked achievements.
        """
        cursor = conn.cursor()
        today_str = date.today().isoformat()

        # 1. Fetch challenge details if present
        topic = "General Programming"
        xp_gain = 0
        if challenge_id:
            cursor.execute("SELECT topic, xp_reward FROM coding_challenges WHERE id = %s;", (challenge_id,))
            ch_row = cursor.fetchone()
            if ch_row:
                topic = ch_row["topic"]
                if status == "Accepted":
                    # Full XP only for the first accepted solution of a challenge (no XP farming by resubmitting).
                    cursor.execute("""
                    SELECT COUNT(*) AS n FROM code_submissions
                    WHERE user_id = %s AND challenge_id = %s AND status = 'Accepted';
                    """, (user_id, challenge_id))
                    prior_accepted = cursor.fetchone()["n"]  # includes the submission being recorded now
                    xp_gain = ch_row["xp_reward"] if prior_accepted <= 1 else 0
                else:
                    xp_gain = 10  # Partial effort XP

        # 2. Update student profile (XP, streak, level)
        current_level, total_xp, streak_days = self._apply_profile_xp(cursor, user_id, xp_gain)

        # 3. Update skill metrics
        self._update_skill_metrics(cursor, user_id, topic, status == "Accepted")

        # 4. Check & Unlock Achievements
        unlocked = self._check_and_unlock_achievements(conn, user_id, status, streak_days, total_xp)

        # 5. Log learning history
        cursor.execute("""
        INSERT INTO learning_history (id, user_id, event_type, details, xp_earned)
        VALUES (%s, %s, %s, %s, %s);
        """, (
            str(uuid.uuid4()),
            user_id,
            "submission",
            json.dumps({"challenge_id": challenge_id, "status": status, "topic": topic}),
            xp_gain
        ))

        return {
            "xp_earned": xp_gain,
            "new_total_xp": total_xp,
            "new_level": current_level,
            "new_streak": streak_days,
            "unlocked_achievements": unlocked
        }

    # ------------------------------------------------------------------
    # Shared gamification primitives (used by challenges, Coding Academy
    # and the roadmap so there is exactly one XP / level / streak system)
    # ------------------------------------------------------------------
    def _apply_profile_xp(self, cursor, user_id: str, xp_gain: int):
        """Adds XP, recalculates level (100 XP per level) and updates the daily streak."""
        today_str = date.today().isoformat()
        cursor.execute("SELECT current_level, total_xp, streak_days, last_active_date FROM student_profiles WHERE user_id = %s;", (user_id,))
        profile_row = cursor.fetchone()

        current_level = 1
        total_xp = 0
        streak_days = 1

        if profile_row:
            current_level = profile_row["current_level"]
            total_xp = profile_row["total_xp"] + xp_gain
            streak_days = profile_row["streak_days"]
            last_active = profile_row["last_active_date"]

            if last_active != today_str:
                if last_active:
                    last_date = datetime.strptime(last_active, "%Y-%m-%d").date()
                    if (date.today() - last_date).days == 1:
                        streak_days += 1
                    elif (date.today() - last_date).days > 1:
                        streak_days = 1
                else:
                    streak_days = 1

            current_level = max(1, (total_xp // 100) + 1)

            cursor.execute("""
            UPDATE student_profiles
            SET total_xp = %s, current_level = %s, streak_days = %s, last_active_date = %s
            WHERE user_id = %s;
            """, (total_xp, current_level, streak_days, today_str, user_id))

        return current_level, total_xp, streak_days

    def award_xp(self, conn: psycopg.Connection, user_id: str, xp: int, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Awards XP through the existing profile/level/streak system and logs it to
        learning_history. Callers are responsible for duplicate prevention (they only
        call this after an INSERT ... ON CONFLICT DO NOTHING actually inserted a row).
        """
        cursor = conn.cursor()
        level, total, streak = self._apply_profile_xp(cursor, user_id, xp)
        cursor.execute("""
        INSERT INTO learning_history (id, user_id, event_type, details, xp_earned)
        VALUES (%s, %s, %s, %s, %s);
        """, (str(uuid.uuid4()), user_id, event_type, json.dumps(details), xp))
        return {"xp_earned": xp, "new_total_xp": total, "new_level": level, "new_streak": streak}

    def update_skill(self, conn: psycopg.Connection, user_id: str, skill_name: str, passed: bool) -> None:
        self._update_skill_metrics(conn.cursor(), user_id, skill_name, passed)

    def get_practice_difficulty(self, conn: psycopg.Connection, user_id: str) -> str:
        """
        'easier' while the student is struggling (3+ of the last 5 graded attempts failed),
        back to 'normal' once they recover (last 3 attempts passed or not enough data).
        """
        cursor = conn.cursor()
        cursor.execute("""
        SELECT passed FROM practice_attempts WHERE user_id = %s ORDER BY created_at DESC LIMIT 5;
        """, (user_id,))
        recent = [r["passed"] for r in cursor.fetchall()]
        if len(recent) >= 3 and all(recent[:3]):
            return "normal"
        if len(recent) >= 5 and sum(1 for p in recent if not p) >= 3:
            return "easier"
        return "normal"

    def _update_skill_metrics(self, cursor, user_id: str, skill_name: str, passed: bool) -> None:
        normalized_skill = skill_name
        status = "Accepted" if passed else "Failed"
        cursor.execute("""
        SELECT id, mastery_level, problems_solved, problems_attempted, error_count
        FROM student_skills
        WHERE user_id = %s AND skill_name = %s;
        """, (user_id, normalized_skill))
        skill_row = cursor.fetchone()

        if skill_row:
            solved = skill_row["problems_solved"] + (1 if status == "Accepted" else 0)
            attempted = skill_row["problems_attempted"] + 1
            errors = skill_row["error_count"] + (0 if status == "Accepted" else 1)
            # Mastery formula: baseline 10 + (solved/attempted * 70) + (min(solved, 10) * 2) - min(errors*2, 20)
            ratio = (solved / attempted) if attempted > 0 else 0
            mastery = round(max(5.0, min(100.0, 15.0 + (ratio * 70.0) + min(solved * 2.0, 15.0) - min(errors * 1.5, 20.0))), 1)

            cursor.execute("""
            UPDATE student_skills
            SET mastery_level = %s, problems_solved = %s, problems_attempted = %s, error_count = %s, last_practiced = CURRENT_TIMESTAMP
            WHERE id = %s;
            """, (mastery, solved, attempted, errors, skill_row["id"]))
        else:
            is_solved = 1 if status == "Accepted" else 0
            is_err = 0 if status == "Accepted" else 1
            mastery = 35.0 if is_solved else 15.0
            cursor.execute("""
            INSERT INTO student_skills (id, user_id, skill_name, mastery_level, problems_solved, problems_attempted, error_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (str(uuid.uuid4()), user_id, normalized_skill, mastery, is_solved, 1, is_err))

    def _check_and_unlock_achievements(
        self,
        conn: psycopg.Connection,
        user_id: str,
        status: str,
        streak_days: int,
        total_xp: int
    ) -> List[str]:
        cursor = conn.cursor()
        unlocked_titles = []

        # Check existing unlocked
        cursor.execute("SELECT achievement_id FROM student_achievements WHERE user_id = %s;", (user_id,))
        already_unlocked = {row["achievement_id"] for row in cursor.fetchall()}

        # 1. First Code Executed
        if "ach_first_code" not in already_unlocked:
            self._award_achievement(conn, user_id, "ach_first_code", "First Code Executed", unlocked_titles)

        # 2. First Solve
        if status == "Accepted" and "ach_first_solve" not in already_unlocked:
            self._award_achievement(conn, user_id, "ach_first_solve", "Bug Hunter", unlocked_titles)

        # 3. 3-Day Streak
        if streak_days >= 3 and "ach_three_streak" not in already_unlocked:
            self._award_achievement(conn, user_id, "ach_three_streak", "3-Day Streak", unlocked_titles)

        # 4. Loop Master
        cursor.execute("""
        SELECT problems_solved FROM student_skills WHERE user_id = %s AND skill_name LIKE %s;
        """, (user_id, "%Loop%"))
        loop_skill = cursor.fetchone()
        if loop_skill and loop_skill["problems_solved"] >= 5 and "ach_loops_master" not in already_unlocked:
            self._award_achievement(conn, user_id, "ach_loops_master", "Master of Loops", unlocked_titles)

        return unlocked_titles

    def _award_achievement(self, conn: psycopg.Connection, user_id: str, ach_id: str, title: str, tracker: List[str]):
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO student_achievements (id, user_id, achievement_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, achievement_id) DO NOTHING;
        """, (str(uuid.uuid4()), user_id, ach_id))
        tracker.append(title)

    def get_dashboard_data(self, conn: psycopg.Connection, user_id: str) -> DashboardResponse:
        cursor = conn.cursor()

        # Profile
        cursor.execute("""
        SELECT u.id, u.email, u.full_name, p.current_level, p.total_xp, p.streak_days, p.last_active_date, p.preferred_language, p.bio
        FROM users u
        LEFT JOIN student_profiles p ON u.id = p.user_id
        WHERE u.id = %s;
        """, (user_id,))
        p_row = cursor.fetchone()
        if not p_row:
            raise ValueError("Student profile not found")

        profile = StudentProfileResponse(
            user_id=p_row["id"],
            full_name=p_row["full_name"],
            email=p_row["email"],
            current_level=p_row["current_level"] or 1,
            total_xp=p_row["total_xp"] or 0,
            streak_days=p_row["streak_days"] or 0,
            last_active_date=p_row["last_active_date"],
            preferred_language=p_row["preferred_language"] or "python",
            bio=p_row["bio"] or ""
        )

        # Submissions stats
        cursor.execute("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as total_solved
        FROM code_submissions
        WHERE user_id = %s;
        """, (user_id,))
        sub_row = cursor.fetchone()
        attempted = sub_row["total_attempts"] or 0
        solved = sub_row["total_solved"] or 0
        solve_rate = round((solved / attempted * 100), 1) if attempted > 0 else 0.0

        # Skills
        cursor.execute("""
        SELECT skill_name, mastery_level, problems_solved, problems_attempted, error_count
        FROM student_skills
        WHERE user_id = %s
        ORDER BY mastery_level DESC;
        """, (user_id,))
        skills: List[SkillProgress] = []
        weaknesses: List[WeaknessItem] = []

        for row in cursor.fetchall():
            m = row["mastery_level"]
            status_label = "Strong" if m >= 70 else ("Developing" if m >= 40 else "Needs Focus")
            skills.append(SkillProgress(
                skill_name=row["skill_name"],
                mastery_level=m,
                problems_solved=row["problems_solved"],
                problems_attempted=row["problems_attempted"],
                error_count=row["error_count"],
                status=status_label
            ))

            if m < 50 or row["error_count"] > row["problems_solved"]:
                err_rate = round(row["error_count"] / max(1, row["problems_attempted"]), 2)
                weaknesses.append(WeaknessItem(
                    topic=row["skill_name"],
                    error_rate=err_rate,
                    recommendation=f"Practice targeted fundamentals in {row['skill_name']} to reinforce execution rules.",
                    recommended_challenge_id=None
                ))

        # Fill default skill if student is brand new
        if not skills:
            skills.append(SkillProgress(
                skill_name="Python Fundamentals",
                mastery_level=20.0,
                problems_solved=0,
                problems_attempted=0,
                error_count=0,
                status="Developing"
            ))

        # Recent activity
        cursor.execute("""
        SELECT event_type, details, xp_earned, created_at
        FROM learning_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5;
        """, (user_id,))
        recent_activity = []
        for r in cursor.fetchall():
            recent_activity.append({
                "event_type": r["event_type"],
                "details": json.loads(r["details"]) if r["details"] else {},
                "xp_earned": r["xp_earned"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None
            })

        # Calculate Programming DNA
        programming_dna = self._calculate_programming_dna(conn, user_id, attempted, solved, skills)

        # Recommended Challenges
        cursor.execute("""
        SELECT id, title, slug, topic, difficulty, description, xp_reward
        FROM coding_challenges
        WHERE (visibility = 'public' OR created_by = %s)
        LIMIT 3;
        """, (user_id,))
        recommended = []
        for ch in cursor.fetchall():
            recommended.append(ChallengeSummary(
                id=ch["id"],
                title=ch["title"],
                slug=ch["slug"],
                topic=ch["topic"],
                difficulty=ch["difficulty"],
                description=ch["description"][:120] + "...",
                xp_reward=ch["xp_reward"],
                solved=False
            ))

        return DashboardResponse(
            profile=profile,
            problems_attempted=attempted,
            problems_solved=solved,
            solve_rate=solve_rate,
            skills=skills,
            weaknesses=weaknesses,
            recent_activity=recent_activity,
            programming_dna=programming_dna,
            recommended_challenges=recommended
        )

    def _calculate_programming_dna(
        self,
        conn: psycopg.Connection,
        user_id: str,
        attempted: int,
        solved: int,
        skills: List[SkillProgress]
    ) -> ProgrammingDNAResponse:
        """
        Derives verifiable Programming DNA based purely on recorded submission metrics.
        """
        # Baseline scores
        logic = 65
        debugging = 60
        correctness = 55
        speed = 70
        independence = 75
        consistency = 60

        if attempted > 0:
            solve_ratio = solved / attempted
            correctness = int(min(98, max(30, solve_ratio * 100)))
            logic = int(min(95, max(35, (solve_ratio * 60) + (len(skills) * 5))))
            debugging = int(min(95, max(40, 50 + (solved * 4))))

        # Hint dependency check
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as hint_count FROM ai_feedback WHERE user_id = %s AND mode = 'hint';", (user_id,))
        hints_used = cursor.fetchone()["hint_count"] or 0
        independence = max(30, 95 - (hints_used * 5))

        # Consistency from streak
        cursor.execute("SELECT streak_days FROM student_profiles WHERE user_id = %s;", (user_id,))
        s_row = cursor.fetchone()
        streak = s_row["streak_days"] if s_row else 0
        consistency = min(98, 50 + (streak * 10))

        strengths = []
        growth_areas = []

        if logic >= 70:
            strengths.append("Strong Algorithmic Decomposition")
        else:
            growth_areas.append("Edge Case Formulation")

        if correctness >= 70:
            strengths.append("High First-Attempt Code Precision")
        else:
            growth_areas.append("Syntax & Type Verification")

        if debugging >= 65:
            strengths.append("Independent Error Isolation")
        else:
            growth_areas.append("Systematic Runtime Tracing")

        if independence >= 75:
            strengths.append("Autonomous Problem Solving")
        else:
            growth_areas.append("Reducing Hint Reliance")

        # Archetype
        if logic >= 75 and correctness >= 75:
            archetype = "Algorithmic Architect"
        elif debugging >= 75:
            archetype = "Methodical Debugger"
        elif independence >= 80:
            archetype = "Autonomous Pioneer"
        else:
            archetype = "Emerging Synthesizer"

        return ProgrammingDNAResponse(
            logical_thinking_score=logic,
            debugging_skill_score=debugging,
            code_correctness_score=correctness,
            problem_solving_speed=speed,
            hint_independence_score=independence,
            consistency_score=consistency,
            top_strengths=strengths if strengths else ["Curious Learner", "Persistent Iteration"],
            key_growth_areas=growth_areas if growth_areas else ["Advanced Data Structures"],
            overall_dna_archetype=archetype
        )

adaptive_engine = AdaptiveLearningEngine()
