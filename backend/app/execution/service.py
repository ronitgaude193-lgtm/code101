import json
from typing import Dict, Any, List
from app.execution.judge0_client import judge0_client
from app.execution.isolated_sandbox import execute_in_isolated_process, validate_code_safety
from app.schemas.all_schemas import TestResultDetail

class ExecutionService:
    async def run_code(self, code: str, language: str = "python", stdin: str = "") -> Dict[str, Any]:
        """
        Executes code through Judge0 if configured, otherwise uses isolated subprocess sandbox.
        Maintains an honest execution provider status.
        """
        if language.lower() == "python":
            is_safe, error_msg = validate_code_safety(code)
            if not is_safe:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": error_msg,
                    "exit_code": 1,
                    "execution_time": 0.0,
                    "status": "Blocked by Security Policy",
                    "provider": "Isolated Local Sandbox"
                }

        if judge0_client.is_configured():
            result = await judge0_client.execute(code, language, stdin)
            result["provider"] = "Judge0 Hosted API"
            return result
        else:
            # Fallback to isolated process sandbox
            result = execute_in_isolated_process(code, stdin)
            result["provider"] = "Isolated Local Sandbox (Judge0 credentials not supplied)"
            return result

    async def evaluate_challenge(
        self,
        challenge_id: str,
        student_code: str,
        test_cases_json: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Tests student code against all challenge test cases.
        """
        test_cases = json.loads(test_cases_json)
        test_results: List[TestResultDetail] = []
        all_passed = True
        passed_count = 0
        total_time = 0.0
        first_error = None

        for idx, tc in enumerate(test_cases):
            raw_input = tc.get("input", "")
            expected = str(tc.get("expected_output", "")).strip().strip("'\"")
            is_hidden = bool(tc.get("hidden", False))

            # Build runner wrapper to safely invoke the student function
            # E.g. student defines function, we call it with test case input and print output
            test_runner_code = f"""
{student_code}

# Test Runner Injected Invocation
import json
try:
    # Attempt to find the defined student function
    funcs = [v for k, v in list(locals().items()) if callable(v) and not k.startswith('_')]
    if not funcs:
        print("__NO_FUNCTION_FOUND__")
    else:
        fn = funcs[-1]
        raw_in = {raw_input}
        if isinstance(raw_in, tuple):
            res = fn(*raw_in)
        else:
            res = fn(raw_in)
        if isinstance(res, str):
            print(res)
        else:
            print(json.dumps(res))
except Exception as e:
    import sys
    sys.stderr.write(f"TestRunnerError: {{str(e)}}")
"""

            res = await self.run_code(test_runner_code, language=language)
            actual_raw = (res.get("stdout") or "").strip()
            stderr = (res.get("stderr") or "").strip()
            total_time += float(res.get("execution_time") or 0.0)
            if stderr and first_error is None:
                first_error = stderr

            actual_clean = actual_raw.strip("'\"")
            passed = (res.get("exit_code") == 0) and (not stderr) and (actual_clean == expected)

            if not passed:
                all_passed = False
            else:
                passed_count += 1

            test_results.append(TestResultDetail(
                case_index=idx + 1,
                input=raw_input if not is_hidden else "[Hidden Test Case]",
                expected_output=expected if not is_hidden else "[Hidden]",
                actual_output=actual_raw if (not is_hidden or not passed) else "[Passed]",
                passed=passed,
                hidden=is_hidden
            ))

        status_desc = "Accepted" if all_passed else ("Wrong Answer" if any(r.actual_output for r in test_results) else "Runtime Error")

        return {
            "all_passed": all_passed,
            "passed_count": passed_count,
            "total_count": len(test_cases),
            "test_results": test_results,
            "status": status_desc,
            "execution_time": round(total_time, 3),
            "first_error": first_error
        }

execution_service = ExecutionService()
