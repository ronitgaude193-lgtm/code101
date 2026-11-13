"""
Deterministic mistake classification.

Turns a failed attempt into a stable *signature* such as "c:loop-boundary" so that
genuinely repeated mistakes can be recognised later. Python reuses the existing
AI Code Autopsy rule engine; C and SQL use compiler/runtime/result evidence.

Signatures are specific on purpose: two attempts only count as the *same* mistake
when their signatures match. Attempts that merely share a concept are reported as
*related*, never as repeats.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Mistake:
    signature: str
    category: str
    concept: str
    language: str
    explanation: str
    correction: str


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "general").lower()).strip("-")[:40] or "general"


# ---------------------------------------------------------------- C --------
_C_RULES = [
    # (regex on compiler output / status, signature, category, concept, explanation, correction)
    (r"expected\W{0,3};", "c:missing-semicolon", "Missing semicolon", "Program Structure",
     "The compiler reached a point where a statement should have ended, but no ';' was found.",
     "End every statement with ';'. Look at the line the compiler reports and the line just above it."),
    (r"undeclared|was not declared", "c:undeclared-identifier", "Undeclared variable or name", "Variables & Declarations",
     "A name was used before it was declared (or it is misspelled, or declared in a different scope).",
     "Declare the variable with its type before using it, and check the spelling and the block it was declared in."),
    (r"implicit declaration of function", "c:missing-prototype", "Function used before declaration", "Functions",
     "A function was called before the compiler had seen its declaration or the header that declares it.",
     "Add the right #include (e.g. <stdio.h>, <string.h>) or define/prototype your function above main()."),
    (r"Segmentation fault|SIGSEGV", "c:invalid-memory-access", "Invalid memory access", "Pointers & Memory",
     "The program read or wrote memory it does not own - often an out-of-bounds index, a missing & in scanf, or an uninitialised pointer.",
     "Check every array index stays within 0..size-1, every scanf argument has & (except char arrays), and every pointer points at valid memory."),
    (r"SIGFPE|Floating point exception", "c:division-by-zero", "Division by zero", "Operators",
     "An integer division or modulo by zero stopped the program.",
     "Guard divisions with a check that the divisor is not 0."),
    (r"Time Limit Exceeded", "c:non-terminating-loop", "Loop never terminates", "Loop Boundaries",
     "The program ran past the time limit - usually a loop whose condition never becomes false.",
     "Make sure the loop variable moves towards the exit condition on every iteration."),
]

_SCANF_NO_AMP = re.compile(r'scanf\s*\(\s*"[^"]*%[dfilu][^"]*"\s*,\s*(?!&)[A-Za-z_]\w*\s*[,)]')
_C_OFF_BY_ONE = re.compile(r"for\s*\([^;]*;\s*\w+\s*<=\s*\w+\s*;[^)]*\)[^{;]*\{?[^}]*\[\s*\w+\s*\]", re.S)


def classify_c(code: str, compile_output: str, status: str, stderr: str, concept_hint: str,
               actual: str = "", expected: str = "") -> Mistake:
    evidence = f"{compile_output}\n{status}\n{stderr}"
    for pattern, sig, cat, concept, expl, fix in _C_RULES:
        if re.search(pattern, evidence, re.I):
            return Mistake(sig, cat, concept, "c", expl, fix)

    if _SCANF_NO_AMP.search(code or ""):
        return Mistake("c:scanf-missing-ampersand", "scanf without &", "Input/Output", "c",
                       "scanf was given a variable instead of its address, so it cannot store the value it reads.",
                       "Pass addresses to scanf: scanf(\"%d\", &x). Only char arrays (strings) are passed without &.")

    exp_lines = [l for l in (expected or "").split("\n") if l.strip()]
    act_lines = [l for l in (actual or "").split("\n") if l.strip()]
    if exp_lines and act_lines and abs(len(exp_lines) - len(act_lines)) == 1:
        return Mistake("c:loop-boundary", "Off-by-one loop boundary", "Loop Boundaries", "c",
                       "The output has one line too many or too few - the loop ran one iteration more or less than intended.",
                       "Check the loop's start value and its condition (< vs <=) against how many times it must run.")
    if _C_OFF_BY_ONE.search(code or "") and status != "Accepted":
        return Mistake("c:loop-boundary", "Off-by-one loop boundary", "Loop Boundaries", "c",
                       "A loop uses <= with an array index, which usually visits one element past the end.",
                       "Arrays of size n use indexes 0..n-1, so the condition is normally i < n.")

    concept = concept_hint or "Problem Solving"
    return Mistake(f"c:wrong-output:{_slug(concept)}", f"Wrong output ({concept})", concept, "c",
                   "The program compiled and ran but printed something different from the expected output.",
                   "Trace the program by hand with the first example input and compare each printed line with the expected one.")


# -------------------------------------------------------------- SQL --------
def classify_sql(sql: str, error: Optional[str], reason: Optional[str], concept_hint: str) -> Mistake:
    s = (sql or "").lower()
    err = (error or "").lower()
    if error:
        if "no such column" in err:
            return Mistake("sql:unknown-column", "Unknown column name", "Tables & Rows", "sql",
                           f"The query refers to a column that does not exist ({error}).",
                           "Check the column names in the dataset (or run SELECT * FROM table LIMIT 1) and use table aliases consistently.")
        if "no such table" in err:
            return Mistake("sql:unknown-table", "Unknown table name", "Tables & Rows", "sql",
                           f"The query refers to a table that does not exist ({error}).",
                           "Use the exact table names from the dataset: departments, employees, projects.")
        if "misuse of aggregate" in err or ("where" in s and re.search(r"where[^;]*\b(count|sum|avg|min|max)\s*\(", s)):
            return Mistake("sql:aggregate-in-where", "Aggregate used in WHERE", "Aggregates & GROUP BY", "sql",
                           "An aggregate such as COUNT() was used to filter rows in WHERE, which runs before grouping.",
                           "Filter groups with HAVING after GROUP BY; keep WHERE for conditions on individual rows.")
        if "syntax error" in err or "incomplete input" in err:
            return Mistake("sql:syntax", "SQL syntax error", "SQL Syntax", "sql",
                           f"The database could not parse the statement ({error}).",
                           "Check clause order (SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT), commas between columns and quotes around text.")
        return Mistake(f"sql:error:{_slug(concept_hint)}", "SQL runtime error", concept_hint or "SQL", "sql",
                       f"The statement failed: {error}", "Read the error message carefully and run smaller parts of the query on their own.")

    has_join = " join " in f" {s} " or re.search(r"from\s+\w+(\s+\w+)?\s*,\s*\w+", s)
    if reason == "too-many-rows" and has_join and " on " not in f" {s} " and "where" not in s:
        return Mistake("sql:join-missing-condition", "JOIN without a matching condition", "Joins", "sql",
                       "Two tables were combined without an ON condition, so every row was paired with every other row (Cartesian product).",
                       "Add ON with the foreign key = primary key match, e.g. ON e.dept_id = d.id.")
    if reason == "too-many-rows":
        return Mistake("sql:missing-filter", "Missing or too-loose filter", "Filtering (WHERE)", "sql",
                       "The query returned more rows than expected - a condition is missing or too broad.",
                       "Write down which rows should be kept and express exactly that in WHERE (or HAVING for groups).")
    if reason == "too-few-rows":
        return Mistake("sql:over-filtering", "Filter removes too many rows", "Filtering (WHERE)", "sql",
                       "The query returned fewer rows than expected - a condition is too strict, or an inner join dropped rows.",
                       "Check comparison operators (> vs >=), AND vs OR, and whether a LEFT JOIN is needed.")
    if reason == "ordering":
        return Mistake("sql:ordering", "Wrong or missing ORDER BY", "Sorting & DISTINCT", "sql",
                       "The right rows came back in the wrong order.",
                       "Add or fix ORDER BY: check the column and the direction (ASC is the default, DESC for largest first).")
    if reason == "wrong-columns":
        return Mistake("sql:wrong-columns", "Wrong columns selected", "Projection (SELECT list)", "sql",
                       "The result has a different number of columns from what the task asks for.",
                       "Select exactly the columns the task names, in that order - avoid SELECT * unless asked.")
    concept = concept_hint or "SQL"
    return Mistake(f"sql:wrong-values:{_slug(concept)}", f"Wrong values ({concept})", concept, "sql",
                   "Same number of rows as expected, but some values are different.",
                   "Compare your result with the task row by row; check the calculation or the condition that produces each value.")


# ----------------------------------------------------------- Python --------
def classify_python(code: str, error: Optional[str], misconception: Optional[str], topic: str) -> Mistake:
    """`misconception` comes from the existing AI Code Autopsy rule engine."""
    err = error or ""
    if misconception and misconception != "State Evolution Mismatch":
        concept = "Loop Boundaries" if "Loop" in misconception or "Index" in misconception else topic
        return Mistake(f"python:{_slug(misconception)}", misconception, concept, "python",
                       f"The autopsy engine identified this pattern: {misconception}.",
                       "Re-run the AI Code Autopsy on this code to see the iteration-by-iteration breakdown.")
    if re.search(r"range\(\s*len\([^)]*\)\s*\+\s*1\s*\)", code or "") or "IndexError" in err:
        return Mistake("python:index-out-of-range", "Index out of range", "Loop Boundaries", "python",
                       "An index went past the end of a list or string - often range(len(x) + 1) or <= in a loop condition.",
                       "Valid indexes are 0..len(x)-1; prefer `for item in items:` when you do not need the index.")
    m = re.search(r"\b(SyntaxError|IndentationError|NameError|TypeError|ValueError|ZeroDivisionError|KeyError|AttributeError|RecursionError)\b", err)
    if m:
        name = m.group(1)
        concept = {"SyntaxError": "Syntax", "IndentationError": "Syntax", "NameError": "Variables & Declarations",
                   "TypeError": "Data Types", "ValueError": "Data Types", "ZeroDivisionError": "Operators",
                   "KeyError": "Data Structures", "AttributeError": "Data Types", "RecursionError": "Recursion"}[name]
        return Mistake(f"python:{name.lower()}", name, concept, "python",
                       f"Python raised {name}: {err.strip().splitlines()[-1][:200] if err.strip() else name}.",
                       "Read the last line of the traceback first - it names the exception and the line where it happened.")
    concept = topic or "General Programming"
    return Mistake(f"python:wrong-output:{_slug(concept)}", f"Wrong output ({concept})", concept, "python",
                   "The function ran but returned a different value from the expected one.",
                   "Trace the function with the first visible test input and compare each intermediate value.")
