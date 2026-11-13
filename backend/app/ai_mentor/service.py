import json
import httpx
import ast
import re
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.schemas.all_schemas import (
    AIMentorResponse,
    AutopsyResponse,
    LoopIterationAnalysis
)

class AIMentorService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower().strip()
        self.api_key = settings.AI_API_KEY.strip()
        self.model = settings.AI_MODEL.strip()
        self.ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.ollama_model = getattr(settings, "OLLAMA_MODEL", "gemma3:latest")

    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return bool(self.ollama_url)
        return bool(self.api_key and self.api_key != "your_ai_api_key_here")

    async def get_mentor_response(
        self,
        code: str,
        mode: str = "learning",
        language: str = "python",
        prompt: Optional[str] = None,
        challenge_title: Optional[str] = None,
        execution_output: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AIMentorResponse:
        """
        Routes to configured LLM (Gemini / OpenAI / Groq) if API key is provided,
        otherwise uses the built-in Offline Pedagogical Mentor Engine.
        """
        if self.is_configured():
            try:
                llm_res = await self._call_llm_mentor(code, mode, language, prompt, challenge_title, execution_output, error_message)
                if llm_res:
                    return llm_res
            except Exception as e:
                # Log error and gracefully fall back
                pass

        # Use Built-in Pedagogical Mentor Engine
        return self._generate_rule_based_mentor_response(code, mode, language, prompt, challenge_title, execution_output, error_message)

    async def run_code_autopsy(
        self,
        code: str,
        language: str = "python",
        challenge_title: Optional[str] = None,
        expected_behavior: Optional[str] = None,
        actual_output: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> AutopsyResponse:
        """
        Performs AI Code Autopsy explaining WHY code failed and mapping the misconception.
        """
        if self.is_configured():
            try:
                llm_autopsy = await self._call_llm_autopsy(code, language, challenge_title, expected_behavior, actual_output, error_message)
                if llm_autopsy:
                    return llm_autopsy
            except Exception:
                pass

        return self._generate_rule_based_autopsy(code, expected_behavior, actual_output, error_message)

    async def _call_llm_mentor(
        self,
        code: str,
        mode: str,
        language: str,
        prompt: Optional[str],
        challenge_title: Optional[str],
        execution_output: Optional[str],
        error_message: Optional[str]
    ) -> Optional[AIMentorResponse]:
        system_instruction = f"""
You are the AI Coding Mentor for beginner & intermediate programmers.
Do NOT simply give away complete solutions or do the work for the student.
Guide them through reasoning, concept explanations, and progressive hints.
Current Mode: {mode.upper()}
Always respond in strictly valid JSON conforming to this schema:
{{
  "mode": "{mode}",
  "summary": "Brief 1-sentence summary",
  "explanation": "Clear friendly pedagogical explanation",
  "hints": ["Hint 1", "Hint 2"],
  "suggested_fix": "Optional targeted code snippet or null",
  "conceptual_takeaway": "Key algorithmic or syntax principle to remember",
  "related_topics": ["Topic A", "Topic B"]
}}
"""
        user_message = f"""
Challenge: {challenge_title or 'General Practice'}
Language: {language}
Student Code:
```
{code}
```
Execution Output: {execution_output or 'None'}
Error Message: {error_message or 'None'}
Student Question: {prompt or 'Please analyze my code and guide me.'}
"""
        raw_text = await self._send_llm_request(system_instruction, user_message)
        if not raw_text:
            return None

        clean_json = self._extract_json(raw_text)
        data = json.loads(clean_json)
        return AIMentorResponse(
            mode=mode,
            summary=data.get("summary", "Code Analysis Complete"),
            explanation=data.get("explanation", ""),
            hints=data.get("hints", []),
            suggested_fix=data.get("suggested_fix"),
            conceptual_takeaway=data.get("conceptual_takeaway", "Focus on stepwise problem-solving."),
            related_topics=data.get("related_topics", ["Python Basics"]),
            is_simulated=False
        )

    async def _call_llm_autopsy(
        self,
        code: str,
        language: str,
        challenge_title: Optional[str],
        expected_behavior: Optional[str],
        actual_output: Optional[str],
        error_message: Optional[str]
    ) -> Optional[AutopsyResponse]:
        system_instruction = """
You are an expert AI Forensic Code Analyst. Your job is to dissect failed code and explain WHY it failed.
Do not just provide corrected code. Uncover the root conceptual misconception.
Always respond in strictly valid JSON:
{
  "primary_failure_reason": "High-level diagnosis",
  "syntax_vs_logic": "Logical Error (or Syntax Error)",
  "misconception_identified": "Specific conceptual confusion (e.g. Index vs Value, Early Return)",
  "detailed_walkthrough": "Step-by-step breakdown of how the machine executed it vs what was expected",
  "loop_timeline": [
    {"iteration": 1, "variable_states": {"i": 0, "total": 0}, "what_happened": "Assigned index 0 instead of list value", "expected_state": "total should be 2"}
  ],
  "guiding_hint": "Question or clue to guide the student to fix it themselves",
  "practice_prompt": "A similar practice question to test this concept"
}
"""
        user_message = f"""
Challenge: {challenge_title or 'Code Autopsy'}
Code:
```
{code}
```
Expected Output / Behavior: {expected_behavior or 'Unknown'}
Actual Output: {actual_output or 'None'}
Error: {error_message or 'None'}
"""
        raw_text = await self._send_llm_request(system_instruction, user_message)
        if not raw_text:
            return None

        clean_json = self._extract_json(raw_text)
        data = json.loads(clean_json)
        timeline = []
        for item in data.get("loop_timeline", []):
            timeline.append(LoopIterationAnalysis(**item))

        return AutopsyResponse(
            primary_failure_reason=data.get("primary_failure_reason", "Logical Misconception"),
            syntax_vs_logic=data.get("syntax_vs_logic", "Logical Error"),
            misconception_identified=data.get("misconception_identified", "Index vs Value Confusion"),
            detailed_walkthrough=data.get("detailed_walkthrough", ""),
            loop_timeline=timeline if timeline else None,
            guiding_hint=data.get("guiding_hint", "Think about what each variable represents."),
            practice_prompt=data.get("practice_prompt", "Try summing numbers using a direct for-each loop."),
            is_simulated=False
        )

    async def _send_llm_request(self, system_instruction: str, user_content: str) -> Optional[str]:
        if self.provider == "ollama":
            url = f"{self.ollama_url}/api/chat"
            payload = {
                "model": self.ollama_model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2}
            }
            async with httpx.AsyncClient(timeout=45.0) as client:
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        resp_data = res.json()
                        return resp_data.get("message", {}).get("content")
                except Exception as exc:
                    print(f"Ollama local LLM connection error: {exc}")
                    return None
        elif self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{system_instruction}\n\n{user_content}"}]}
                ],
                "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    resp_data = res.json()
                    return resp_data["candidates"][0]["content"]["parts"][0]["text"]
        elif self.provider in ("openai", "groq"):
            base_url = "https://api.openai.com/v1/chat/completions" if self.provider == "openai" else "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model if self.provider == "groq" else "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(base_url, json=payload, headers=headers)
                if res.status_code == 200:
                    resp_data = res.json()
                    return resp_data["choices"][0]["message"]["content"]
        return None

    async def generate_json(
        self,
        system_instruction: str,
        user_content: str,
        required_keys: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Shared entry point for the learning extensions (roadmap, hints, memory replay).
        Returns a parsed JSON object, or None when no provider is configured, the
        provider is unreachable, or the reply is not valid JSON with the required keys.
        Callers must always have a deterministic fallback.
        """
        if not self.is_configured():
            return None
        try:
            raw_text = await self._send_llm_request(system_instruction, user_content)
            if not raw_text:
                return None
            data = json.loads(self._extract_json(raw_text))
            if not isinstance(data, dict):
                return None
            for key in required_keys or []:
                value = data.get(key)
                if value is None or (isinstance(value, str) and not value.strip()):
                    return None
            return data
        except Exception as exc:
            print(f"[ai_mentor] LLM JSON generation failed ({self.provider}): {exc}")
            return None

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _generate_rule_based_mentor_response(
        self,
        code: str,
        mode: str,
        language: str,
        prompt: Optional[str],
        challenge_title: Optional[str],
        execution_output: Optional[str],
        error_message: Optional[str]
    ) -> AIMentorResponse:
        """
        Offline Pedagogical Rule Engine:
        Provides high-quality contextual guidance without requiring an external AI API key.
        """
        summary = "Code Guidance Ready"
        explanation = ""
        hints = []
        takeaway = "Always trace how variables evolve across every line."
        topics = ["Control Flow", "Debugging Strategies"]

        # Check for syntax error
        if error_message and ("SyntaxError" in error_message or "IndentationError" in error_message):
            summary = "Syntax Issue Detected"
            explanation = (
                "Python was unable to parse your code into an executable program. "
                "This usually happens when a colon `:` is missing at the end of an `if`, `for`, or `def` statement, "
                "or when indentation spaces are inconsistent."
            )
            hints = [
                "Examine the line indicated in the error message for missing punctuation (like `:`) or unclosed parentheses `()`, `[]`.",
                "Ensure consistent 4-space indentation across all nested blocks."
            ]
            takeaway = "Syntax errors prevent execution entirely. Check punctuation and structure first."
            topics = ["Python Syntax", "Indentation"]

        # Check for accumulator reset inside loop
        elif re.search(r"for\s+\w+\s+in.*:\n\s+total\s*=\s*\w+", code):
            summary = "Variable Overwrite inside Loop"
            explanation = (
                "Notice that inside your loop, you are using the assignment operator `=` instead of the in-place addition operator `+=`. "
                "Every time the loop runs, the previous calculation is erased and replaced by the current value."
            )
            hints = [
                "Did you mean to accumulate values? Use `total += ...` or `total = total + ...`.",
                "Initialize your accumulator variable *before* entering the loop."
            ]
            takeaway = "Assignment (`=`) replaces state. Accumulation (`+=`) preserves prior history."
            topics = ["Loops", "Accumulator Pattern"]

        # Check for index assignment mistake: total = i
        elif "range(len(" in code and ("total = i" in code or "sum = i" in code):
            summary = "Index vs Value Misconception"
            explanation = (
                "When looping with `for i in range(len(numbers)):`, `i` represents the position (index: 0, 1, 2, ...), "
                "NOT the actual element inside the list! To access the element, you need `numbers[i]`."
            )
            hints = [
                "Notice that `i` is just an integer index counter.",
                "To get the item at that position, use subscription indexing: `numbers[i]`.",
                "Better yet in Python, iterate directly over the list items: `for num in numbers:`!"
            ]
            takeaway = "Separate the container's address (index) from the container's contents (value)."
            topics = ["Lists", "Indexing", "Loops"]

        # Check for early return inside loop
        elif re.search(r"for\s+.*:\n\s+(?:if\s+.*:\n\s+)?return\b", code):
            summary = "Premature Loop Termination"
            explanation = (
                "Your `return` statement is located inside the loop body. A `return` immediately exits the entire function, "
                "meaning your loop will only ever process the very first element!"
            )
            hints = [
                "Check your indentation. Should the `return` be outside the loop?",
                "Only place `return` inside a loop when you want to exit early upon finding a specific match."
            ]
            takeaway = "The `return` keyword is final; it halts both the enclosing loop and function instantly."
            topics = ["Functions", "Control Flow"]

        else:
            if mode == "hint":
                summary = "Progressive Hint"
                explanation = "Break down your algorithm into small verifiable milestones: inputs -> state transformations -> expected output."
                hints = [
                    "Identify your edge cases (e.g. what if the input list or string is empty?).",
                    "Print your variables at each iteration to observe their values in real time."
                ]
            elif mode == "debugging":
                summary = "Debugging Checklist"
                explanation = "Your code passed initial syntax checks. Let's verify variable types, conditions, and boundary values."
                hints = [
                    "Check boundary conditions: first item, last item, and 0-length inputs.",
                    "Verify your variable names match throughout the function."
                ]
            else: # learning mode
                summary = "Conceptual Overview"
                explanation = (
                    "In Python, writing clean code involves keeping functions focused on doing one single task well. "
                    "Use descriptive variable names, handle edge cases gracefully, and verify your output with test cases."
                )
                hints = [
                    "Trace the execution path manually on paper before running.",
                    "Use the Visual Debugger tab below to inspect variable values step-by-step!"
                ]

        return AIMentorResponse(
            mode=mode,
            summary=summary,
            explanation=explanation,
            hints=hints,
            suggested_fix=None,
            conceptual_takeaway=takeaway,
            related_topics=topics,
            is_simulated=True
        )

    def _generate_rule_based_autopsy(
        self,
        code: str,
        expected_behavior: Optional[str],
        actual_output: Optional[str],
        error_message: Optional[str]
    ) -> AutopsyResponse:
        """
        Specialized forensic autopsy engine covering the canonical beginner misconceptions.
        """
        # Canonical Example: numbers = [2, 4, 6, 8]; total = i
        if ("range(len(" in code or "range(" in code) and re.search(r"(?:total|sum)\s*=\s*i", code):
            timeline = [
                LoopIterationAnalysis(
                    iteration=1,
                    variable_states={"i": 0, "numbers[i]": 2, "total": 0},
                    what_happened="i is 0. Assigned total = 0. The actual number 2 was ignored.",
                    expected_state="total should accumulate 2 (total = 2)"
                ),
                LoopIterationAnalysis(
                    iteration=2,
                    variable_states={"i": 1, "numbers[i]": 4, "total": 1},
                    what_happened="i is 1. Overwrote total with 1. Previous total was discarded.",
                    expected_state="total should accumulate 4 (total = 6)"
                ),
                LoopIterationAnalysis(
                    iteration=3,
                    variable_states={"i": 2, "numbers[i]": 6, "total": 2},
                    what_happened="i is 2. Overwrote total with 2.",
                    expected_state="total should accumulate 6 (total = 12)"
                ),
                LoopIterationAnalysis(
                    iteration=4,
                    variable_states={"i": 3, "numbers[i]": 8, "total": 3},
                    what_happened="i is 3. Final total ends up as 3 (the last index), not 20!",
                    expected_state="total should accumulate 8 (total = 20)"
                )
            ]
            return AutopsyResponse(
                primary_failure_reason="Assigned loop index instead of accumulating list element values.",
                syntax_vs_logic="Logical Misconception",
                misconception_identified="Index vs Value Confusion",
                detailed_walkthrough=(
                    "In `for i in range(len(numbers)):`, `i` steps through the integers [0, 1, 2, 3]. "
                    "When writing `total = i`, the program updates `total` to the index number itself rather than adding `numbers[i]`. "
                    "Furthermore, using `=` instead of `+=` replaces the value on every iteration instead of adding to it."
                ),
                loop_timeline=timeline,
                guiding_hint="How can you both: 1) access the element `numbers[i]`, and 2) add it to the running `total` rather than replacing it?",
                practice_prompt="Given a list of prices `[10, 25, 40]`, write a loop that correctly accumulates the sum using `for price in prices:`.",
                is_simulated=True
            )

        # Early return inside loop
        elif re.search(r"for\s+.*:\n\s+return\b", code):
            return AutopsyResponse(
                primary_failure_reason="Function terminated prematurely on first iteration.",
                syntax_vs_logic="Logical / Control Flow Error",
                misconception_identified="Premature Loop Termination via Inner Return",
                detailed_walkthrough=(
                    "A `return` statement immediately ends the function execution and returns control to the caller. "
                    "Because your `return` is indented inside the loop, the loop never executes past iteration #1."
                ),
                loop_timeline=[
                    LoopIterationAnalysis(
                        iteration=1,
                        variable_states={"loop_progress": "Started element 1"},
                        what_happened="Hit return statement on line inside loop. Function terminated immediately.",
                        expected_state="Loop should continue to process remaining elements."
                    )
                ],
                guiding_hint="What happens if you outdent the `return` statement so it sits outside the loop block?",
                practice_prompt="Write a function that counts how many negative numbers exist in a list before returning.",
                is_simulated=True
            )

        # Generic Diagnostic Autopsy
        return AutopsyResponse(
            primary_failure_reason=error_message or "Output discrepancy detected during test execution.",
            syntax_vs_logic="Syntax / Runtime Error" if error_message else "Logical Discrepancy",
            misconception_identified="State Evolution Mismatch",
            detailed_walkthrough=(
                f"Your code produced: '{actual_output or 'no output'}', whereas the expected result was: '{expected_behavior or 'different output'}'. "
                "Step through your variable mutations using the Visual Debugger below to pinpoint the exact line where state diverged."
            ),
            loop_timeline=None,
            guiding_hint="Inspect intermediate variable states before the final return or print statement.",
            practice_prompt="Try writing a simplified version of the logic with a tiny input (e.g. 2 elements) on paper first.",
            is_simulated=True
        )

ai_mentor_service = AIMentorService()
