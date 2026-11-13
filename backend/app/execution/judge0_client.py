import httpx
import base64
from typing import Optional, Dict, Any
from app.core.config import settings

# Judge0 language ID mapping
LANGUAGE_IDS = {
    "python": 71,       # Python (3.8.1) / 92 for (3.11.2)
    "c": 50,            # C (GCC 9.2.0) - Coding Academy C course
    "javascript": 63,   # JavaScript (Node.js 12.14.0)
    "cpp": 54,          # C++ (GCC 9.2.0)
    "java": 62           # Java (OpenJDK 13.0.1)
}

def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _unb64(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return value


class Judge0Client:
    def __init__(self):
        self.api_url = settings.JUDGE0_API_URL.strip().rstrip("/")
        self.api_key = settings.JUDGE0_API_KEY.strip()

    def is_configured(self) -> bool:
        return bool(self.api_url)

    async def execute(self, code: str, language: str = "python", stdin: str = "") -> Dict[str, Any]:
        if not self.is_configured():
            return {
                "success": False,
                "error": "Judge0 API credentials not configured. Please set JUDGE0_API_URL and JUDGE0_API_KEY in backend/.env",
                "stdout": "",
                "stderr": "Service configuration error: Judge0 credentials missing.",
                "exit_code": -1,
                "execution_time": 0.0,
                "status": "Service Unavailable"
            }

        lang_id = LANGUAGE_IDS.get(language.lower(), 71)
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            host = self.api_url.replace("https://", "").replace("http://", "").split("/")[0]
            if "rapidapi.com" in host:
                headers["X-RapidAPI-Key"] = self.api_key
                headers["X-RapidAPI-Host"] = host
            else:
                # Self-hosted / official Judge0 instances authenticate with X-Auth-Token
                headers["X-Auth-Token"] = self.api_key

        # base64 in both directions: compiler diagnostics (e.g. GCC's quote characters) and
        # program output are not always valid UTF-8, which Judge0 rejects in plain-text mode.
        payload = {
            "source_code": _b64(code),
            "language_id": lang_id,
            "stdin": _b64(stdin or ""),
            "cpu_time_limit": 5.0,
            "memory_limit": 128000
        }

        url = f"{self.api_url}/submissions?base64_encoded=true&wait=true"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code not in (200, 201):
                    return {
                        "success": False,
                        "error": f"Judge0 returned status {resp.status_code}: {resp.text}",
                        "stdout": "",
                        "stderr": resp.text,
                        "exit_code": 1,
                        "execution_time": 0.0,
                        "status": "Execution Error"
                    }
                
                result = resp.json()
                status_desc = result.get("status", {}).get("description", "Unknown")
                stdout = _unb64(result.get("stdout"))
                stderr = _unb64(result.get("stderr"))
                compile_output = _unb64(result.get("compile_output"))
                time_taken = float(result.get("time") or 0.0)
                accepted = result.get("status", {}).get("id") == 3  # 3 = Accepted
                # Judge0's default response omits exit_code; derive it from the status.
                exit_code = result.get("exit_code")
                if exit_code is None:
                    exit_code = 0 if accepted else 1

                return {
                    "success": accepted,
                    "stdout": stdout,
                    "stderr": stderr,
                    "compile_output": compile_output,
                    "exit_code": exit_code,
                    "execution_time": time_taken,
                    "status": status_desc
                }
            except httpx.RequestError as exc:
                return {
                    "success": False,
                    "error": f"Judge0 connection error: {str(exc)}",
                    "stdout": "",
                    "stderr": f"Failed to contact Judge0 execution provider: {str(exc)}",
                    "exit_code": -1,
                    "execution_time": 0.0,
                    "status": "Network Timeout / Provider Offline"
                }

judge0_client = Judge0Client()
