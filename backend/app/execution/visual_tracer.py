import sys
import subprocess
import tempfile
import os
import json
import time
from typing import Dict, Any
from app.execution.isolated_sandbox import validate_code_safety

TRACER_WORKER_PATH = os.path.join(os.path.dirname(__file__), "tracer_worker.py")

def trace_execution(code: str, stdin: str = "", max_steps: int = 150) -> Dict[str, Any]:
    """
    Spawns tracer_worker.py in an isolated child process to trace variables and execution line by line.
    Enforces maximum steps and timeout to prevent runaway loops.
    """
    is_safe, error_msg = validate_code_safety(code)
    if not is_safe:
        return {
            "success": False,
            "steps": [],
            "total_steps": 0,
            "error": error_msg,
            "output": ""
        }

    payload = {
        "code": code,
        "stdin": stdin,
        "max_steps": max_steps
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as temp_payload:
        json.dump(payload, temp_payload)
        temp_payload_path = temp_payload.name

    try:
        proc = subprocess.run(
            [sys.executable, TRACER_WORKER_PATH, temp_payload_path],
            capture_output=True,
            text=True,
            timeout=3.5,
            cwd=tempfile.gettempdir()
        )

        if proc.returncode != 0 and not proc.stdout:
            return {
                "success": False,
                "steps": [],
                "total_steps": 0,
                "error": proc.stderr or "Tracing worker process exited abnormally.",
                "output": ""
            }

        try:
            result = json.loads(proc.stdout.strip())
            return result
        except json.JSONDecodeError:
            return {
                "success": False,
                "steps": [],
                "total_steps": 0,
                "error": f"Failed to parse trace results. Output: {proc.stdout}",
                "output": proc.stdout
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "steps": [],
            "total_steps": 0,
            "error": "Tracing timed out (3.5s limit). Please check for infinite loops or reduce iteration count.",
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "steps": [],
            "total_steps": 0,
            "error": f"Visual tracing failed: {str(e)}",
            "output": ""
        }
    finally:
        try:
            if os.path.exists(temp_payload_path):
                os.remove(temp_payload_path)
        except Exception:
            pass
