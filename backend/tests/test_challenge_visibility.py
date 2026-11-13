"""
Challenge visibility: private challenges are visible only to their creator.
Uses two throwaway students that are deleted afterwards.
Run:  .venv\\Scripts\\python.exe backend\\tests\\test_challenge_visibility.py
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from httpx import ASGITransport, AsyncClient

from app.database.session import get_db, init_database
from app.main import app


async def register(c, name):
    r = await c.post("/api/auth/register", json={"email": f"qa-{uuid.uuid4().hex[:10]}@dbce.test",
                                                 "password": "QaPassword123!", "full_name": name})
    assert r.status_code == 200, r.text
    return r.json()["user"]["id"], {"Authorization": f"Bearer {r.json()['access_token']}"}


async def main():
    init_database()
    ids = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60) as c:
        try:
            a_id, a = await register(c, "Owner")
            b_id, b = await register(c, "Other")
            ids += [a_id, b_id]

            priv = (await c.post("/api/challenges/generate?topic=Strings&difficulty=Beginner&visibility=private", headers=a)).json()
            pub = (await c.post("/api/challenges/generate?topic=Strings&difficulty=Beginner&visibility=public", headers=a)).json()
            assert priv["visibility"] == "private" and priv["is_mine"], priv
            assert pub["visibility"] == "public", pub

            a_list = {x["id"]: x for x in (await c.get("/api/challenges", headers=a)).json()}
            b_list = {x["id"]: x for x in (await c.get("/api/challenges", headers=b)).json()}
            anon = {x["id"] for x in (await c.get("/api/challenges")).json()}
            assert priv["id"] in a_list and a_list[priv["id"]]["is_mine"], "owner must see own private challenge"
            assert priv["id"] not in b_list and priv["id"] not in anon, "private challenge leaked to others"
            assert pub["id"] in b_list and not b_list[pub["id"]]["is_mine"] and pub["id"] in anon, "shared challenge must be visible to all"
            assert "ch_sum_list" in b_list, "seeded challenges stay public"

            assert (await c.get(f"/api/challenges/{priv['id']}", headers=b)).status_code == 404
            assert (await c.get(f"/api/challenges/{priv['id']}")).status_code == 404
            assert (await c.get(f"/api/challenges/{priv['id']}", headers=a)).status_code == 200
            r = await c.post("/api/execution/submit", headers=b, json={"challenge_id": priv["id"], "code": "def f(s):\n    return s\n"})
            assert r.status_code == 404, "others must not submit to a private challenge"
            print("ALL CHALLENGE VISIBILITY CHECKS PASSED")
        finally:
            with get_db() as conn:
                for uid in ids:  # ON DELETE CASCADE also removes the challenges they created
                    conn.cursor().execute("DELETE FROM users WHERE id = %s;", (uid,))


if __name__ == "__main__":
    asyncio.run(main())
