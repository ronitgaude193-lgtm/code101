import sys
import subprocess
import tempfile
import os
import json
import time
import ast
from typing import Dict, Any

# Security AST validator to prevent untrusted code attempting malicious host modifications
FORBIDDEN_MODULES = {"os", "subprocess", "socket", "http", "urllib", "requests", "shutil", "ctypes", "winreg", "msvcrt"}
FORBIDDEN_CALLS = {"__import__", "eval", "exec", "compile", "open"}

def validate_code_safety(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # Let Python interpreter catch syntax error naturally during execution
        return True, ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod in FORBIDDEN_MODULES:
                    return False, f"Security Policy Violation: Import of module '{mod}' is not allowed in student learning sandbox."
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in FORBIDDEN_MODULES:
                return False, f"Security Policy Violation: Import from module '{mod}' is not allowed in student learning sandbox."
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                # Disallow raw open() for local filesystem protection
                if node.func.id == "open":
                    return False, "Security Policy Violation: File system access via 'open()' is restricted in the coding sandbox."
    return True, ""

def execute_in_isolated_process(code: str, stdin: str = "", timeout_seconds: float = 4.0) -> Dict[str, Any]:
    """
    Executes student code in a separate, isolated subprocess with timeout and AST filtering.
    Never executes inside the main FastAPI application.
    """
    is_safe, error_msg = validate_code_safety(code)
    if not is_safe:
        return {
            "success": False,
            "stdout": "",
            "stderr": error_msg,
            "exit_code": 1,
            "execution_time": 0.0,
            "status": "Blocked by Security Policy"
        }

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, temp_path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=tempfile.gettempdir()
        )
        duration = round(time.perf_counter() - start_time, 4)
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode

        status_desc = "Accepted" if exit_code == 0 else "Runtime Error"
        if "SyntaxError" in stderr:
            status_desc = "Syntax Error"

        return {
            "success": exit_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
            "execution_time": duration,
            "status": status_desc
        }
    except subprocess.TimeoutExpired:
        duration = round(time.perf_counter() - start_time, 4)
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds} seconds (Possible infinite loop).",
            "exit_code": 124,
            "execution_time": duration,
            "status": "Time Limit Exceeded"
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution environment error: {str(e)}",
            "exit_code": 1,
            "execution_time": 0.0,
            "status": "Execution Failure"
        }
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass
