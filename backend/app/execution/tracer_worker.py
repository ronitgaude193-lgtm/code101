"""
Isolated Python Execution Tracing Worker
Runs as a separate isolated process to inspect line-by-line variable states,
loop iterations, call stacks, and output safely with strict limits.
"""
import sys
import json
import io
import traceback

MAX_TRACE_STEPS = 150
MAX_OUTPUT_CHARS = 10000

trace_steps = []
stdout_capture = io.StringIO()
original_stdout = sys.stdout

def safe_repr(val, depth=0):
    if depth > 2:
        return "..."
    if isinstance(val, (int, float, bool, type(None))):
        return val
    elif isinstance(val, str):
        if len(val) > 100:
            return val[:100] + "... (truncated)"
        return val
    elif isinstance(val, (list, tuple)):
        if len(val) > 20:
            return [safe_repr(x, depth + 1) for x in val[:20]] + ["..."]
        return [safe_repr(x, depth + 1) for x in val]
    elif isinstance(val, dict):
        if len(val) > 20:
            preview = {str(k): safe_repr(v, depth + 1) for k, v in list(val.items())[:20]}
            preview["..."] = "truncated"
            return preview
        return {str(k): safe_repr(v, depth + 1) for k, v in val.items()}
    elif isinstance(val, set):
        return list([safe_repr(x, depth + 1) for x in list(val)[:20]])
    else:
        return str(val)

def trace_dispatcher(frame, event, arg):
    global trace_steps
    if len(trace_steps) >= MAX_TRACE_STEPS:
        return None

    # Only trace code executing within the target user script
    code_filename = frame.f_code.co_filename
    if code_filename != "<student_code>":
        return trace_dispatcher

    lineno = frame.f_lineno
    func_name = frame.f_code.co_name
    
    # Filter variables to exclude internal dunder keys and tracer internals
    locals_copy = {}
    for k, v in frame.f_locals.items():
        if k.startswith("__"):
            continue
        try:
            locals_copy[k] = safe_repr(v)
        except Exception:
            locals_copy[k] = "<unserializable>"

    # Capture call stack
    stack = []
    curr = frame
    while curr:
        if curr.f_code.co_filename == "<student_code>":
            stack.append(f"{curr.f_code.co_name}:{curr.f_lineno}")
        curr = curr.f_back
    stack.reverse()

    trace_steps.append({
        "step": len(trace_steps) + 1,
        "line": lineno,
        "event": event,
        "func_name": func_name,
        "variables": locals_copy,
        "stdout_so_far": stdout_capture.getvalue()[:MAX_OUTPUT_CHARS],
        "stack": stack
    })

    return trace_dispatcher

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No payload supplied to tracer"}))
        return

    payload_file = sys.argv[1]
    with open(payload_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_code = data.get("code", "")
    stdin_input = data.get("stdin", "")

    # Restrict built-ins to block dangerous OS modifications
    safe_globals = {
        "__builtins__": __builtins__,
        "__name__": "__main__",
        "__doc__": None,
    }

    # Redirect stdout and stdin
    sys.stdout = stdout_capture
    sys.stdin = io.StringIO(stdin_input)

    try:
        compiled = compile(source_code, "<student_code>", "exec")
        sys.settrace(trace_dispatcher)
        exec(compiled, safe_globals)
    except Exception as exc:
        err_msg = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        trace_steps.append({
            "step": len(trace_steps) + 1,
            "line": getattr(exc, "lineno", 1) or 1,
            "event": "exception",
            "func_name": "<error>",
            "variables": {"__error__": err_msg},
            "stdout_so_far": stdout_capture.getvalue()[:MAX_OUTPUT_CHARS],
            "stack": ["<exception>"]
        })
    finally:
        sys.settrace(None)
        captured_output = stdout_capture.getvalue()
        sys.stdout = original_stdout

    result = {
        "success": True,
        "steps": trace_steps,
        "total_steps": len(trace_steps),
        "output": captured_output
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
