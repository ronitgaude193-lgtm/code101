"""
Coding Academy MVP curriculum: C Programming and DBMS & SQL.

Each course has 5 levels. Each level has 3 lessons (each with one practice task)
and one level assessment; the level-5 assessment is the course's final assessment.

Reference solutions / answers stay server-side and are never returned by the API.
To add a course later, append another dict to COURSES - no schema change needed.
"""
import json

# ---------------------------------------------------------------------------
# Shared SQL practice dataset (loaded into a fresh in-memory DB for every run)
# ---------------------------------------------------------------------------
SQL_DATASET = """
CREATE TABLE departments (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE employees (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    dept_id   INTEGER REFERENCES departments(id),
    salary    INTEGER NOT NULL,
    hire_year INTEGER NOT NULL
);
CREATE TABLE projects (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    dept_id INTEGER REFERENCES departments(id),
    budget  INTEGER NOT NULL
);
INSERT INTO departments VALUES (1,'Engineering'),(2,'Marketing'),(3,'Sales'),(4,'HR');
INSERT INTO employees VALUES
 (1,'Asha',1,85000,2016),(2,'Ravi',1,92000,2014),(3,'Meera',2,61000,2019),
 (4,'John',3,55000,2013),(5,'Priya',1,78000,2020),(6,'Karan',3,58000,2017),
 (7,'Sara',2,64000,2015),(8,'Leo',4,50000,2018),(9,'Nina',3,60000,2021),
 (10,'Omar',NULL,47000,2022);
INSERT INTO projects VALUES
 (1,'Apollo',1,120000),(2,'Beacon',2,45000),(3,'Comet',3,30000),(4,'Delta',1,80000);
""".strip()

SQL_SCHEMA_NOTE = (
    "**Practice dataset**\n"
    "- `departments(id, name)`\n"
    "- `employees(id, name, dept_id, salary, hire_year)` (Omar has no department: `dept_id` is NULL)\n"
    "- `projects(id, name, dept_id, budget)`"
)


def q(question, options, answer, explain, concept):
    return {"q": question, "options": options, "answer": answer, "explain": explain, "concept": concept}


# ---------------------------------------------------------------------------
# COURSE 1: C PROGRAMMING
# ---------------------------------------------------------------------------
C_COURSE = {
    "id": "course_c",
    "slug": "c-programming",
    "title": "C Programming",
    "description": "Learn C from your first program to pointers, structures and file handling. Every coding task is compiled and tested with real input/output.",
    "language": "c",
    "icon": "Cpu",
    "sort_order": 1,
    "completion_xp": 200,
    "completion_achievement_id": "ach_course_c",
    "levels": [
        {
            "number": 1,
            "title": "Fundamentals",
            "description": "Program structure, variables, data types, input/output and operators.",
            "lessons": [
                {
                    "id": "c_l1_intro",
                    "title": "Introduction to C & Program Structure",
                    "concept": "Program Structure",
                    "summary": "Every C program starts in main(), uses #include to pull in libraries and ends statements with semicolons.",
                    "minutes": 15,
                    "content": """## Why C?
C is a compiled language: the compiler turns your source code into a machine program before it runs. It is fast, close to the hardware and the foundation of operating systems, embedded devices and many other languages.

## Anatomy of a C program
```c
#include <stdio.h>   // gives us printf and scanf

int main(void) {     // execution always starts here
    printf("Hello!\\n");
    return 0;        // 0 tells the OS the program succeeded
}
```
- `#include <stdio.h>` is a **preprocessor directive** that includes the standard input/output library.
- `int main(void)` is the **entry point**. Its body lives between `{` and `}`.
- Every statement ends with a **semicolon** `;`. Forgetting one is the most common beginner compile error.
- `\\n` inside a string prints a **newline**.

## Compile, then run
Unlike Python, C code must compile without errors before it can run. Read compiler messages from the top: the first error is usually the real one.""",
                    "task": {
                        "id": "c_t1_hello",
                        "title": "Your first C program",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 25,
                        "prompt": "Write a complete C program that prints exactly `Hello, C!` followed by a newline.",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    // print Hello, C!\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    printf(\"Hello, C!\\n\");\n    return 0;\n}\n",
                        "tests": [{"stdin": "", "expected_output": "Hello, C!", "hidden": False}],
                        "hints": [
                            "Output in C goes through a function from the stdio.h library.",
                            "Use printf with the exact text inside double quotes - capitalisation and punctuation matter.",
                            "Inside main, write printf(\"...\\n\"); with your message, and keep the semicolon at the end.",
                        ],
                    },
                },
                {
                    "id": "c_l1_vars_io",
                    "title": "Variables, Data Types & Input/Output",
                    "concept": "Input/Output",
                    "summary": "Variables have a fixed type (int, float, char). printf writes values out; scanf reads them in using format specifiers and the & address operator.",
                    "minutes": 20,
                    "content": """## Declaring variables
In C every variable has a **type** that never changes:
```c
int age = 20;        // whole numbers
float price = 9.5;   // decimals (double gives more precision)
char grade = 'A';    // a single character, in single quotes
```

## Format specifiers
| Type | printf / scanf |
|---|---|
| int | `%d` |
| float | `%f` |
| double | `%lf` (scanf) / `%f` (printf) |
| char | `%c` |

## Reading input with scanf
```c
int a, b;
scanf("%d %d", &a, &b);   // note the & before each variable
printf("%d\\n", a + b);
```
`scanf` needs the **address** of the variable so it can write into it - that is what `&` means. Forgetting `&` compiles (with a warning) but crashes or reads garbage at runtime.""",
                    "task": {
                        "id": "c_t2_sum",
                        "title": "Add two numbers",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 15,
                        "xp": 25,
                        "prompt": "Read two integers from standard input (separated by a space) and print their sum.\n\nExample input: `3 4`  \nExample output: `7`",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    // read a and b, then print a + b\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf(\"%d %d\", &a, &b);\n    printf(\"%d\\n\", a + b);\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "3 4", "expected_output": "7", "hidden": False},
                            {"stdin": "-5 10", "expected_output": "5", "hidden": False},
                            {"stdin": "1000000 2000000", "expected_output": "3000000", "hidden": True},
                        ],
                        "hints": [
                            "Reading input in C needs a function that writes into your variables' memory.",
                            "scanf with \"%d %d\" reads two integers - but it needs each variable's address.",
                            "Call scanf(\"%d %d\", &a, &b); then printf(\"%d\\n\", a + b);",
                        ],
                    },
                },
                {
                    "id": "c_l1_operators",
                    "title": "Operators",
                    "concept": "Operators",
                    "summary": "Arithmetic (+ - * / %), relational (== != < >) and logical (&& || !) operators. Integer division drops the remainder; % gives the remainder.",
                    "minutes": 15,
                    "content": """## Arithmetic operators
`+  -  *  /  %`

With two `int`s, `/` performs **integer division** and throws away the fractional part:
```c
printf("%d\\n", 17 / 5);   // 3
printf("%d\\n", 17 % 5);   // 2  (remainder)
```
To get a decimal result, at least one operand must be floating point: `17 / 5.0` gives `3.4`.

## Relational and logical operators
- Relational: `==  !=  <  >  <=  >=` produce 1 (true) or 0 (false).
- Logical: `&&` (and), `||` (or), `!` (not).
- `=` assigns, `==` compares. Writing `if (x = 5)` is a classic bug.

## Precedence
`*`, `/`, `%` bind tighter than `+` and `-`. Use parentheses when in doubt: `(a + b) * c`.""",
                    "task": {
                        "id": "c_t3_divmod",
                        "title": "Quotient and remainder",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 15,
                        "xp": 25,
                        "prompt": "Read two positive integers `a` and `b`. Print the integer quotient `a / b` and the remainder `a % b` on one line, separated by a space.\n\nExample input: `17 5`  \nExample output: `3 2`",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf(\"%d %d\", &a, &b);\n    // print quotient and remainder\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int a, b;\n    scanf(\"%d %d\", &a, &b);\n    printf(\"%d %d\\n\", a / b, a % b);\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "17 5", "expected_output": "3 2", "hidden": False},
                            {"stdin": "20 4", "expected_output": "5 0", "hidden": False},
                            {"stdin": "7 9", "expected_output": "0 7", "hidden": True},
                        ],
                        "hints": [
                            "C has separate operators for 'how many times does b fit into a' and 'what is left over'.",
                            "With two ints, / already drops the fraction; % gives the remainder.",
                            "One printf with two %d placeholders: printf(\"%d %d\\n\", a / b, a % b);",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "c_a1",
                "title": "Level 1 Assessment: Fundamentals",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("Where does a C program start executing?", ["The first line of the file", "The main function", "The first #include", "Any function named start"], 1, "Execution always begins in main().", "Program Structure"),
                    q("Which format specifier reads an int with scanf?", ["%f", "%c", "%d", "%s"], 2, "%d is used for int in both printf and scanf.", "Input/Output"),
                    q("What does 17 / 5 evaluate to when both are ints?", ["3.4", "3", "4", "2"], 1, "Integer division discards the fractional part.", "Operators"),
                    q("Why does scanf(\"%d\", &x) need the & ?", ["It is optional style", "It passes the address of x so scanf can store the value", "It converts x to a pointer type permanently", "It prints x"], 1, "scanf writes into memory, so it needs the variable's address.", "Input/Output"),
                ],
            },
        },
        {
            "number": 2,
            "title": "Control Statements",
            "description": "Making decisions with if-else and switch, and repeating work with loops and nested loops.",
            "lessons": [
                {
                    "id": "c_l2_ifelse",
                    "title": "If-Else Statements",
                    "concept": "Conditions",
                    "summary": "if / else if / else choose which block runs based on a condition that evaluates to non-zero (true) or zero (false).",
                    "minutes": 15,
                    "content": """## Making decisions
```c
if (marks >= 90) {
    printf("A\\n");
} else if (marks >= 75) {
    printf("B\\n");
} else {
    printf("C\\n");
}
```
- The condition goes in **parentheses**.
- Conditions are checked **top to bottom**; only the first true branch runs.
- Any non-zero value counts as true.

## Even or odd?
A number is even when dividing by 2 leaves no remainder: `n % 2 == 0`. Be careful with negative numbers: in C, `-3 % 2` is `-1`, so test `== 0` rather than `== 1` for the odd case.

## Common mistakes
- `if (x = 0)` assigns instead of comparing - use `==`.
- A stray `;` after `if (cond);` ends the if immediately.""",
                    "task": {
                        "id": "c_t4_evenodd",
                        "title": "Even or odd",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 15,
                        "xp": 30,
                        "prompt": "Read one integer `n` and print `Even` if it is even, otherwise print `Odd`. Negative numbers and zero are possible.",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    // print Even or Odd\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    if (n % 2 == 0) {\n        printf(\"Even\\n\");\n    } else {\n        printf(\"Odd\\n\");\n    }\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "4", "expected_output": "Even", "hidden": False},
                            {"stdin": "7", "expected_output": "Odd", "hidden": False},
                            {"stdin": "0", "expected_output": "Even", "hidden": True},
                            {"stdin": "-3", "expected_output": "Odd", "hidden": True},
                        ],
                        "hints": [
                            "Evenness is about the remainder after dividing by 2.",
                            "Compare n % 2 with 0 - that test also works for negative numbers.",
                            "if (n % 2 == 0) print Even, else print Odd.",
                        ],
                    },
                },
                {
                    "id": "c_l2_switch",
                    "title": "Switch Statements",
                    "concept": "Conditions",
                    "summary": "switch jumps to the case label that matches an integer value; break stops execution from falling through to the next case.",
                    "minutes": 15,
                    "content": """## Choosing among many fixed values
```c
switch (choice) {
    case 1:
        printf("Start\\n");
        break;
    case 2:
        printf("Stop\\n");
        break;
    default:
        printf("Unknown\\n");
}
```
- The expression must be an **integer** (or char).
- Each `case` needs a **constant** value.
- `break` exits the switch. Without it, execution **falls through** into the next case - a frequent bug.
- `default` runs when no case matches.

## When to use switch vs if-else
Use `switch` for one variable compared against many exact values; use `if-else` for ranges (`x > 10`) or complex conditions.""",
                    "task": {
                        "id": "c_t5_weekday",
                        "title": "Day of the week",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 15,
                        "xp": 30,
                        "prompt": "Read an integer from 1 to 7 and print the matching day name (`1` = `Monday` ... `7` = `Sunday`) using a `switch`. For any other number print `Invalid`.",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int d;\n    scanf(\"%d\", &d);\n    switch (d) {\n        // add your cases\n    }\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int d;\n    scanf(\"%d\", &d);\n    switch (d) {\n        case 1: printf(\"Monday\\n\"); break;\n        case 2: printf(\"Tuesday\\n\"); break;\n        case 3: printf(\"Wednesday\\n\"); break;\n        case 4: printf(\"Thursday\\n\"); break;\n        case 5: printf(\"Friday\\n\"); break;\n        case 6: printf(\"Saturday\\n\"); break;\n        case 7: printf(\"Sunday\\n\"); break;\n        default: printf(\"Invalid\\n\");\n    }\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "1", "expected_output": "Monday", "hidden": False},
                            {"stdin": "7", "expected_output": "Sunday", "hidden": False},
                            {"stdin": "9", "expected_output": "Invalid", "hidden": False},
                            {"stdin": "3", "expected_output": "Wednesday", "hidden": True},
                        ],
                        "hints": [
                            "A switch compares one value against several fixed cases - remember what stops a case from running into the next.",
                            "Write case 1 through case 7, each ending with break, and a default for everything else.",
                            "Pattern: case 1: printf(\"Monday\\n\"); break;  ...  default: printf(\"Invalid\\n\");",
                        ],
                    },
                },
                {
                    "id": "c_l2_loops",
                    "title": "Loops & Nested Loops",
                    "concept": "Loop Boundaries",
                    "summary": "for, while and do-while repeat code. The loop condition decides exactly how many times the body runs - off-by-one errors come from wrong boundaries.",
                    "minutes": 20,
                    "content": """## The three loops
```c
for (int i = 1; i <= n; i++) { ... }   // known number of repetitions
while (x > 0) { ... }                  // repeat while a condition holds
do { ... } while (again);              // body runs at least once
```
A `for` loop has three parts: **initialise; condition; update**.

## Counting precisely
- `for (i = 0; i < n; i++)` runs **n** times (0 .. n-1).
- `for (i = 1; i <= n; i++)` runs **n** times (1 .. n).
- `for (i = 0; i <= n; i++)` runs **n + 1** times - the classic **off-by-one** error.

## Nested loops
An inner loop runs completely for every single iteration of the outer loop:
```c
for (int row = 1; row <= 3; row++) {
    for (int col = 1; col <= row; col++) {
        printf("*");
    }
    printf("\\n");
}
```
prints
```
*
**
***
```
Notice the inner bound depends on `row`: that is how each line gets longer.""",
                    "task": {
                        "id": "c_t6_triangle",
                        "title": "Star triangle",
                        "type": "code",
                        "difficulty": "Beginner",
                        "minutes": 20,
                        "xp": 35,
                        "prompt": "Read a positive integer `n` and print a right-angled triangle of `*` with `n` rows: row 1 has 1 star, row 2 has 2 stars, ... row n has n stars. No spaces.\n\nExample input: `3`  \nExample output:\n```\n*\n**\n***\n```",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    // nested loops here\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    for (int row = 1; row <= n; row++) {\n        for (int col = 1; col <= row; col++) {\n            printf(\"*\");\n        }\n        printf(\"\\n\");\n    }\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "3", "expected_output": "*\n**\n***", "hidden": False},
                            {"stdin": "1", "expected_output": "*", "hidden": False},
                            {"stdin": "5", "expected_output": "*\n**\n***\n****\n*****", "hidden": True},
                        ],
                        "hints": [
                            "You need one loop for the rows and a second loop inside it for the stars on each row.",
                            "The number of stars on a row equals the row number - so the inner loop's limit should depend on the outer loop variable. Check that you get exactly n rows.",
                            "Outer: row from 1 to n inclusive. Inner: col from 1 to row inclusive printing '*'. After the inner loop, print a newline.",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "c_a2",
                "title": "Level 2 Assessment: Control Statements",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("How many times does for (i = 0; i <= 5; i++) run?", ["4", "5", "6", "Forever"], 2, "i takes the values 0,1,2,3,4,5 - six iterations. This is the classic off-by-one.", "Loop Boundaries"),
                    q("What happens if a case in a switch has no break?", ["Compile error", "Execution falls through into the next case", "The switch restarts", "Nothing - break is optional with no effect"], 1, "Without break, the following cases run too (fall-through).", "Conditions"),
                    q("Which loop always executes its body at least once?", ["for", "while", "do-while", "None of them"], 2, "do-while checks its condition after the body.", "Loop Boundaries"),
                    q("What is wrong with: if (x = 10) { ... }", ["Nothing", "It assigns 10 to x instead of comparing", "Parentheses are not allowed", "if needs a semicolon"], 1, "= assigns; == compares. The condition is always true here.", "Conditions"),
                ],
            },
        },
        {
            "number": 3,
            "title": "Functions & Arrays",
            "description": "Breaking programs into functions and storing collections of values in 1-D and 2-D arrays.",
            "lessons": [
                {
                    "id": "c_l3_functions",
                    "title": "Functions & Function Arguments",
                    "concept": "Functions",
                    "summary": "A function has a return type, a name and typed parameters. Arguments are passed by value: the function gets a copy.",
                    "minutes": 20,
                    "content": """## Defining and calling a function
```c
int add(int x, int y) {   // return type, name, parameters
    return x + y;
}

int main(void) {
    int s = add(2, 3);    // call with arguments
    printf("%d\\n", s);
}
```
- Declare (or define) a function **before** you call it, otherwise the compiler reports an *implicit declaration*.
- `void` means the function returns nothing.
- The value after `return` is sent back to the caller.

## Pass by value
C copies each argument into the parameter. Changing `x` inside `add` does **not** change the caller's variable. (Pointers, in Level 4, are how a function changes the caller's data.)

## Prototypes
```c
int square(int x);   // prototype: lets main() call square before its full definition
```""",
                    "task": {
                        "id": "c_t7_square",
                        "title": "Write a square function",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 15,
                        "xp": 35,
                        "prompt": "Write a function `int square(int x)` that returns `x * x`. In `main`, read one integer, call `square` and print the result.",
                        "starter": "#include <stdio.h>\n\n// define square here\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    // print square(n)\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint square(int x) {\n    return x * x;\n}\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    printf(\"%d\\n\", square(n));\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "4", "expected_output": "16", "hidden": False},
                            {"stdin": "-3", "expected_output": "9", "hidden": False},
                            {"stdin": "0", "expected_output": "0", "hidden": True},
                        ],
                        "hints": [
                            "A function needs a return type, a name, a parameter list and a return statement.",
                            "Define square above main so the compiler knows about it, and make it return the product.",
                            "int square(int x) { return x * x; }  then in main: printf(\"%d\\n\", square(n));",
                        ],
                    },
                },
                {
                    "id": "c_l3_arrays1d",
                    "title": "One-Dimensional Arrays",
                    "concept": "Arrays",
                    "summary": "An array stores a fixed number of same-type values in consecutive memory. Valid indexes run from 0 to size-1.",
                    "minutes": 20,
                    "content": """## Declaring and using arrays
```c
int marks[5] = {70, 82, 91, 64, 77};
printf("%d\\n", marks[0]);   // first element: 70
printf("%d\\n", marks[4]);   // last element: 77
```
- Indexes start at **0**. An array of size 5 has indexes 0-4.
- Reading `marks[5]` is **out of bounds**: C does not stop you, it just reads whatever memory is there.

## Reading n values
```c
int n, a[100];
scanf("%d", &n);
for (int i = 0; i < n; i++) {
    scanf("%d", &a[i]);
}
```

## Finding the maximum
Start your "best so far" with the **first element**, not with 0 - otherwise a list of all-negative numbers gives the wrong answer.""",
                    "task": {
                        "id": "c_t8_max",
                        "title": "Largest element",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 20,
                        "xp": 35,
                        "prompt": "The first line contains `n` (1 to 100). The second line contains `n` integers. Print the largest one. Values can be negative.\n\nExample input:\n```\n5\n3 9 2 7 4\n```\nExample output: `9`",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int n, a[100];\n    scanf(\"%d\", &n);\n    // read n values and print the maximum\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int n, a[100];\n    scanf(\"%d\", &n);\n    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n    int best = a[0];\n    for (int i = 1; i < n; i++) if (a[i] > best) best = a[i];\n    printf(\"%d\\n\", best);\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "5\n3 9 2 7 4", "expected_output": "9", "hidden": False},
                            {"stdin": "3\n-5 -2 -8", "expected_output": "-2", "hidden": False},
                            {"stdin": "1\n42", "expected_output": "42", "hidden": True},
                        ],
                        "hints": [
                            "Keep track of the best value seen so far while you walk through the array.",
                            "Initialise the tracker with a[0], not 0 - think about an array of only negative numbers. Loop indexes go from 0 to n-1.",
                            "Read all values in a loop with i < n, set best = a[0], then loop again and update best whenever a[i] > best.",
                        ],
                    },
                },
                {
                    "id": "c_l3_arrays2d",
                    "title": "Two-Dimensional Arrays",
                    "concept": "Arrays",
                    "summary": "A 2-D array is a table of rows and columns, accessed as a[row][col]. Nested loops visit every cell.",
                    "minutes": 20,
                    "content": """## Tables of values
```c
int m[2][3] = {
    {1, 2, 3},
    {4, 5, 6}
};
printf("%d\\n", m[1][2]);   // row 1, column 2 -> 6
```
The first index is the **row**, the second is the **column**. Both start at 0.

## Visiting every cell
```c
for (int r = 0; r < rows; r++) {
    for (int c = 0; c < cols; c++) {
        printf("%d ", m[r][c]);
    }
    printf("\\n");
}
```
The outer loop picks the row; the inner loop walks across that row.

## Row totals
Reset the running total to 0 **at the start of each row** (inside the outer loop) - if you reset it once before both loops, the totals accumulate across rows.""",
                    "task": {
                        "id": "c_t9_rowsums",
                        "title": "Row sums of a matrix",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 25,
                        "xp": 40,
                        "prompt": "The first line has `r c` (rows and columns, each 1-10). Then `r` lines follow with `c` integers each. Print the sum of each row on its own line.\n\nExample input:\n```\n2 3\n1 2 3\n4 5 6\n```\nExample output:\n```\n6\n15\n```",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int r, c, m[10][10];\n    scanf(\"%d %d\", &r, &c);\n    // read the matrix and print each row's sum\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int r, c, m[10][10];\n    scanf(\"%d %d\", &r, &c);\n    for (int i = 0; i < r; i++)\n        for (int j = 0; j < c; j++)\n            scanf(\"%d\", &m[i][j]);\n    for (int i = 0; i < r; i++) {\n        int sum = 0;\n        for (int j = 0; j < c; j++) sum += m[i][j];\n        printf(\"%d\\n\", sum);\n    }\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "2 3\n1 2 3\n4 5 6", "expected_output": "6\n15", "hidden": False},
                            {"stdin": "1 1\n7", "expected_output": "7", "hidden": False},
                            {"stdin": "3 2\n-1 1\n10 20\n0 0", "expected_output": "0\n30\n0", "hidden": True},
                        ],
                        "hints": [
                            "Two nested loops read the matrix; two more nested loops can add up each row.",
                            "The running total must start again at 0 for every row - where should that line go?",
                            "for each row i: sum = 0; for each column j: sum += m[i][j]; then print sum before moving to the next row.",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "c_a3",
                "title": "Level 3 Assessment: Functions & Arrays",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("For int a[5]; which index is valid for the last element?", ["5", "4", "6", "-1"], 1, "Indexes run 0..size-1.", "Arrays"),
                    q("C passes function arguments by...", ["reference", "value (a copy)", "name", "pointer automatically"], 1, "The parameter is a copy of the argument.", "Functions"),
                    q("What does the compiler warning 'implicit declaration of function' usually mean?", ["The function is called before it is declared", "The function returns void", "The file has too many functions", "A semicolon is missing"], 0, "Declare a prototype or define the function above its first call.", "Functions"),
                    q("In m[2][3], what does the 3 mean?", ["Number of rows", "Number of columns", "Total cells", "Starting index"], 1, "First dimension = rows, second = columns.", "Arrays"),
                ],
            },
        },
        {
            "number": 4,
            "title": "Pointers & Strings",
            "description": "Addresses, dereferencing, pointer arithmetic and character strings.",
            "lessons": [
                {
                    "id": "c_l4_pointers",
                    "title": "Pointers",
                    "concept": "Pointers & Memory",
                    "summary": "A pointer stores a memory address. & takes an address, * reads or writes the value at that address. Pointers let functions modify the caller's variables.",
                    "minutes": 25,
                    "content": """## Address and value
```c
int x = 10;
int *p = &x;      // p holds the address of x
printf("%d\\n", *p);   // 10  (dereference: value at that address)
*p = 25;          // changes x through the pointer
```
- `&x` -> "address of x"
- `*p` -> "value stored where p points"
- A pointer's type says what it points to: `int *`, `char *`, ...

## Why pointers matter: swap
A normal function only gets copies, so it cannot swap the caller's variables. With pointers it can:
```c
void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}
swap(&x, &y);   // pass addresses
```

## Danger zone
Dereferencing an uninitialised or `NULL` pointer causes a **segmentation fault** (SIGSEGV). Always point a pointer at something valid before using `*`.""",
                    "task": {
                        "id": "c_t10_swap",
                        "title": "Swap with pointers",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 20,
                        "xp": 40,
                        "prompt": "Write `void swap(int *a, int *b)` that swaps the two values. In `main`, read two integers `x y`, call `swap(&x, &y)` and print `x y` (which should now be in swapped order).\n\nExample input: `3 8`  \nExample output: `8 3`",
                        "starter": "#include <stdio.h>\n\nvoid swap(int *a, int *b) {\n    // swap the values a and b point to\n}\n\nint main(void) {\n    int x, y;\n    scanf(\"%d %d\", &x, &y);\n    swap(&x, &y);\n    printf(\"%d %d\\n\", x, y);\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nvoid swap(int *a, int *b) {\n    int t = *a;\n    *a = *b;\n    *b = t;\n}\n\nint main(void) {\n    int x, y;\n    scanf(\"%d %d\", &x, &y);\n    swap(&x, &y);\n    printf(\"%d %d\\n\", x, y);\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "3 8", "expected_output": "8 3", "hidden": False},
                            {"stdin": "-1 5", "expected_output": "5 -1", "hidden": False},
                            {"stdin": "7 7", "expected_output": "7 7", "hidden": True},
                        ],
                        "hints": [
                            "Swapping needs somewhere to keep one value while you overwrite it.",
                            "Work with the values the pointers point to (*a, *b), not the pointers themselves.",
                            "int t = *a; *a = *b; *b = t;",
                        ],
                    },
                },
                {
                    "id": "c_l4_ptrops",
                    "title": "Pointer Operations",
                    "concept": "Pointers & Memory",
                    "summary": "Adding 1 to a pointer moves it to the next element. An array name behaves like a pointer to its first element, so *(a + i) is a[i].",
                    "minutes": 20,
                    "content": """## Pointer arithmetic
```c
int a[4] = {10, 20, 30, 40};
int *p = a;          // same as &a[0]
printf("%d\\n", *(p + 2));   // 30
p++;                 // now points at a[1]
```
`p + 1` moves by **one element**, not one byte - the compiler scales by the element size.

## Arrays and pointers
- `a[i]` is exactly `*(a + i)`.
- `&a[i]` is exactly `a + i`.

## Walking backwards
```c
for (int *q = a + n - 1; q >= a; q--) {
    printf("%d ", *q);
}
```
Start at the **last** element `a + n - 1`. Starting at `a + n` reads one past the end.""",
                    "task": {
                        "id": "c_t11_reverse",
                        "title": "Print an array in reverse",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 20,
                        "xp": 40,
                        "prompt": "Read `n` (1 to 100) and then `n` integers. Print them in reverse order on one line, separated by single spaces. Try using a pointer to walk the array.\n\nExample input:\n```\n4\n1 2 3 4\n```\nExample output: `4 3 2 1`",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    int n, a[100];\n    scanf(\"%d\", &n);\n    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n    // print in reverse\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    int n, a[100];\n    scanf(\"%d\", &n);\n    for (int i = 0; i < n; i++) scanf(\"%d\", &a[i]);\n    for (int *p = a + n - 1; p >= a; p--) {\n        printf(\"%d\", *p);\n        if (p > a) printf(\" \");\n    }\n    printf(\"\\n\");\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "4\n1 2 3 4", "expected_output": "4 3 2 1", "hidden": False},
                            {"stdin": "1\n9", "expected_output": "9", "hidden": False},
                            {"stdin": "5\n-1 0 3 3 8", "expected_output": "8 3 3 0 -1", "hidden": True},
                        ],
                        "hints": [
                            "Reversing output just means visiting the elements from the last one to the first.",
                            "The last element is at index n-1 (or pointer a + n - 1). Make sure you stop after index 0.",
                            "for (int *p = a + n - 1; p >= a; p--) print *p, adding a space between numbers but not after the last.",
                        ],
                    },
                },
                {
                    "id": "c_l4_strings",
                    "title": "Strings & Basic String Operations",
                    "concept": "Strings",
                    "summary": "A C string is a char array ending in the null character '\\0'. Its length is the number of characters before '\\0'.",
                    "minutes": 20,
                    "content": """## Strings are char arrays
```c
char word[20] = "hello";   // stored as h e l l o \\0
printf("%s\\n", word);
```
The compiler adds the **null terminator** `'\\0'` automatically. Your array must have room for it.

## Reading a word
```c
char s[101];
scanf("%100s", s);   // no & : an array name is already an address
```
`%s` stops at whitespace, so it reads one word.

## Length without strlen
```c
int len = 0;
while (s[len] != '\\0') len++;
```

## Useful <string.h> functions
`strlen`, `strcpy`, `strcmp`, `strcat`. Compare strings with `strcmp(a, b) == 0`, never with `a == b` (that compares addresses).""",
                    "task": {
                        "id": "c_t12_strrev",
                        "title": "Length and reverse of a word",
                        "type": "code",
                        "difficulty": "Intermediate",
                        "minutes": 20,
                        "xp": 40,
                        "prompt": "Read one word (no spaces, at most 100 characters). On the first line print its length, computed **without** `strlen`. On the second line print the word reversed.\n\nExample input: `hello`  \nExample output:\n```\n5\nolleh\n```",
                        "starter": "#include <stdio.h>\n\nint main(void) {\n    char s[101];\n    scanf(\"%100s\", s);\n    // count characters until '\\0', then print reversed\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint main(void) {\n    char s[101];\n    scanf(\"%100s\", s);\n    int len = 0;\n    while (s[len] != '\\0') len++;\n    printf(\"%d\\n\", len);\n    for (int i = len - 1; i >= 0; i--) printf(\"%c\", s[i]);\n    printf(\"\\n\");\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "hello", "expected_output": "5\nolleh", "hidden": False},
                            {"stdin": "C", "expected_output": "1\nC", "hidden": False},
                            {"stdin": "racecar", "expected_output": "7\nracecar", "hidden": True},
                        ],
                        "hints": [
                            "Every C string ends with a special character that marks where it stops.",
                            "Count characters until you reach '\\0'. The last real character is at index len - 1.",
                            "while (s[len] != '\\0') len++; print len; then loop i from len-1 down to 0 printing s[i].",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "c_a4",
                "title": "Level 4 Assessment: Pointers & Strings",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("If int x = 5; int *p = &x; what is *p?", ["The address of x", "5", "p itself", "Undefined"], 1, "*p dereferences the pointer and gives the value of x.", "Pointers & Memory"),
                    q("For int a[4]; what is *(a + 2)?", ["a[2]", "a[0] + 2", "The address of a[2]", "a[3]"], 0, "*(a + i) is equivalent to a[i].", "Pointers & Memory"),
                    q("What marks the end of a C string?", ["A newline", "The '\\0' null character", "A space", "Its declared size"], 1, "C strings are null-terminated.", "Strings"),
                    q("How should you check whether two C strings are equal?", ["a == b", "strcmp(a, b) == 0", "a = b", "strlen(a) == strlen(b)"], 1, "== compares addresses; strcmp compares characters.", "Strings"),
                    q("A program crashes with SIGSEGV. The most likely cause is...", ["Integer overflow", "Dereferencing an invalid pointer or reading out of bounds", "A missing printf", "Using a for loop"], 1, "Segmentation faults come from invalid memory access.", "Pointers & Memory"),
                ],
            },
        },
        {
            "number": 5,
            "title": "Structures & Practical Programming",
            "description": "Grouping data with structs and unions, basic file handling, and a complete practical problem. Ends with the final course assessment.",
            "lessons": [
                {
                    "id": "c_l5_structs",
                    "title": "Structures & Unions",
                    "concept": "Structures",
                    "summary": "A struct groups related fields of different types into one record. A union lets fields share the same memory, so only one is valid at a time.",
                    "minutes": 20,
                    "content": """## Defining a structure
```c
struct Student {
    char name[50];
    int marks;
};

struct Student s;
scanf("%49s %d", s.name, &s.marks);
printf("%s scored %d\\n", s.name, s.marks);
```
- Access fields with the **dot** operator: `s.marks`.
- Through a pointer, use the **arrow**: `p->marks` (same as `(*p).marks`).
- Arrays of structs are common: `struct Student list[100];`

## Unions
```c
union Value {
    int i;
    float f;
};
```
All fields of a union share **one** memory location: the union is as big as its largest field, and writing `f` overwrites `i`. Use it when a value can be one of several types but never more than one at once.""",
                    "task": {
                        "id": "c_t13_topper",
                        "title": "Find the top student",
                        "type": "code",
                        "difficulty": "Advanced",
                        "minutes": 25,
                        "xp": 45,
                        "prompt": "Read `n` (1 to 50). Then `n` lines follow, each with a name (one word) and integer marks. Store them in an array of `struct Student` and print the name of the student with the highest marks. If there is a tie, print the first one.\n\nExample input:\n```\n3\nAsha 82\nRavi 91\nMeera 77\n```\nExample output: `Ravi`",
                        "starter": "#include <stdio.h>\n\nstruct Student {\n    char name[50];\n    int marks;\n};\n\nint main(void) {\n    int n;\n    struct Student list[50];\n    scanf(\"%d\", &n);\n    // read students and print the top scorer's name\n\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nstruct Student {\n    char name[50];\n    int marks;\n};\n\nint main(void) {\n    int n;\n    struct Student list[50];\n    scanf(\"%d\", &n);\n    for (int i = 0; i < n; i++) scanf(\"%49s %d\", list[i].name, &list[i].marks);\n    int best = 0;\n    for (int i = 1; i < n; i++) if (list[i].marks > list[best].marks) best = i;\n    printf(\"%s\\n\", list[best].name);\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "3\nAsha 82\nRavi 91\nMeera 77", "expected_output": "Ravi", "hidden": False},
                            {"stdin": "1\nLeo 50", "expected_output": "Leo", "hidden": False},
                            {"stdin": "3\nA 90\nB 95\nC 95", "expected_output": "B", "hidden": True},
                        ],
                        "hints": [
                            "This is the 'find the maximum' pattern again - but each element is a record with a name and marks.",
                            "Track the index of the best student, compare list[i].marks, and only replace on a strictly greater score so ties keep the first.",
                            "Read with scanf(\"%49s %d\", list[i].name, &list[i].marks); best = 0; update best when list[i].marks > list[best].marks; print list[best].name.",
                        ],
                    },
                },
                {
                    "id": "c_l5_files",
                    "title": "Basic File Handling",
                    "concept": "File Handling",
                    "summary": "fopen opens a file and returns a FILE pointer (or NULL on failure). Use fprintf/fscanf to write/read and always fclose when done.",
                    "minutes": 20,
                    "content": """## Opening and closing files
```c
FILE *fp = fopen("scores.txt", "w");   // "r" read, "w" write, "a" append
if (fp == NULL) {
    printf("Could not open file\\n");
    return 1;
}
fprintf(fp, "%d\\n", 95);
fclose(fp);
```
- `fopen` returns `NULL` when it fails - **always check**.
- `"w"` creates the file or erases an existing one; `"a"` adds to the end.
- `fclose` flushes buffered data to disk and releases the file.

## Reading until the end
```c
int value, total = 0;
FILE *in = fopen("scores.txt", "r");
while (fscanf(in, "%d", &value) == 1) {
    total += value;
}
fclose(in);
```
`fscanf` returns how many items it read; checking `== 1` stops cleanly at end of file.""",
                    "task": {
                        "id": "c_t14_files_quiz",
                        "title": "File handling check",
                        "type": "quiz",
                        "difficulty": "Intermediate",
                        "minutes": 10,
                        "xp": 30,
                        "pass_mark": 100,
                        "questions": [
                            q("What does fopen return if the file cannot be opened?", ["0 bytes", "NULL", "-1", "An empty FILE"], 1, "Always compare the FILE* with NULL before using it.", "File Handling"),
                            q("Which mode adds to the end of an existing file without erasing it?", ["\"w\"", "\"r\"", "\"a\"", "\"x\""], 2, "\"a\" appends; \"w\" truncates the file.", "File Handling"),
                            q("Why is checking fscanf(...) == 1 a good loop condition?", ["It runs exactly once", "It stops when no more values can be read", "It skips the first value", "fscanf always returns 1"], 1, "fscanf returns the number of items successfully read.", "File Handling"),
                        ],
                        "hints": [
                            "Think about what each function returns when something goes wrong.",
                            "fopen gives a pointer - what pointer value means 'nothing'? Compare the meanings of the w and a modes.",
                            "fopen returns NULL on failure, \"a\" appends, and fscanf returns how many values it read.",
                        ],
                    },
                },
                {
                    "id": "c_l5_practical",
                    "title": "Practical Programming: Prime Numbers",
                    "concept": "Problem Solving",
                    "summary": "Combine loops, conditions and functions to solve a complete problem: test whether a number is prime efficiently and handle edge cases.",
                    "minutes": 25,
                    "content": """## Problem-solving checklist
1. Restate the problem and list the **edge cases** first.
2. Solve it by hand for a small input.
3. Write the simplest correct version, then improve it.

## Prime numbers
A prime is an integer **greater than 1** whose only divisors are 1 and itself.
- Edge cases: 0 and 1 are **not** prime; 2 **is** prime (the only even prime).
- You only need to test divisors up to the square root: if `n = a * b` then one of `a` or `b` is at most `sqrt(n)`.

```c
int is_prime(int n) {
    if (n < 2) return 0;
    for (int d = 2; d * d <= n; d++) {
        if (n % d == 0) return 0;
    }
    return 1;
}
```
Using `d * d <= n` avoids floating point `sqrt()` and the need to link the math library.""",
                    "task": {
                        "id": "c_t15_prime",
                        "title": "Prime checker",
                        "type": "code",
                        "difficulty": "Advanced",
                        "minutes": 25,
                        "xp": 45,
                        "prompt": "Read a non-negative integer `n` and print `Prime` if it is a prime number, otherwise `Not Prime`.",
                        "starter": "#include <stdio.h>\n\nint is_prime(int n) {\n    // return 1 if n is prime, 0 otherwise\n    return 0;\n}\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    printf(\"%s\\n\", is_prime(n) ? \"Prime\" : \"Not Prime\");\n    return 0;\n}\n",
                        "solution": "#include <stdio.h>\n\nint is_prime(int n) {\n    if (n < 2) return 0;\n    for (int d = 2; d * d <= n; d++) if (n % d == 0) return 0;\n    return 1;\n}\n\nint main(void) {\n    int n;\n    scanf(\"%d\", &n);\n    printf(\"%s\\n\", is_prime(n) ? \"Prime\" : \"Not Prime\");\n    return 0;\n}\n",
                        "tests": [
                            {"stdin": "7", "expected_output": "Prime", "hidden": False},
                            {"stdin": "1", "expected_output": "Not Prime", "hidden": False},
                            {"stdin": "12", "expected_output": "Not Prime", "hidden": False},
                            {"stdin": "2", "expected_output": "Prime", "hidden": True},
                            {"stdin": "97", "expected_output": "Prime", "hidden": True},
                        ],
                        "hints": [
                            "Start with the edge cases: which small numbers are not prime by definition?",
                            "Numbers below 2 are not prime. For the rest, try divisors starting at 2 - you can stop once d * d is bigger than n.",
                            "if (n < 2) return 0; for d from 2 while d * d <= n: if n % d == 0 return 0; after the loop return 1.",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "c_final",
                "title": "Final Assessment: C Programming",
                "kind": "final",
                "minutes": 15,
                "xp": 100,
                "pass_mark": 80,
                "questions": [
                    q("Which declaration creates a pointer to an int?", ["int p;", "int *p;", "int &p;", "pointer int p;"], 1, "The * in a declaration makes a pointer type.", "Pointers & Memory"),
                    q("How do you access the marks field through struct Student *p?", ["p.marks", "p->marks", "*p.marks", "p[marks]"], 1, "-> dereferences the pointer and selects the field.", "Structures"),
                    q("for (i = 1; i < n; i++) runs how many times for n = 5?", ["5", "4", "6", "1"], 1, "i = 1,2,3,4 - four iterations.", "Loop Boundaries"),
                    q("What is the size of a union with an int (4 bytes) and a double (8 bytes)?", ["4 bytes", "8 bytes (its largest member, possibly padded)", "12 bytes", "Depends on which field was written last"], 1, "Union members share memory; the union is as large as its largest member.", "Structures"),
                    q("Which is the safest way to read a word into char s[20]?", ["scanf(\"%s\", &s)", "scanf(\"%19s\", s)", "scanf(\"%c\", s)", "scanf(\"%d\", s)"], 1, "A width limit leaves room for '\\0' and prevents overflow; arrays need no &.", "Strings"),
                ],
            },
        },
    ],
}

# ---------------------------------------------------------------------------
# COURSE 2: DBMS & SQL
# ---------------------------------------------------------------------------
SQL_COURSE = {
    "id": "course_sql",
    "slug": "dbms-sql",
    "title": "DBMS & SQL",
    "description": "Understand how relational databases work and write real SQL: queries, data changes, aggregates, joins, subqueries, normalization and indexing. Every query is run and checked against the expected result.",
    "language": "sql",
    "icon": "Database",
    "sort_order": 2,
    "completion_xp": 200,
    "completion_achievement_id": "ach_course_sql",
    "levels": [
        {
            "number": 1,
            "title": "Database Fundamentals",
            "description": "What a DBMS is, how tables, rows and columns model data, and how keys connect tables.",
            "lessons": [
                {
                    "id": "sql_l1_dbms",
                    "title": "Introduction to DBMS & Database Concepts",
                    "concept": "DBMS Concepts",
                    "summary": "A DBMS stores, protects and queries data for many users at once. Relational databases organise data into tables and are queried with SQL.",
                    "minutes": 15,
                    "content": """## What is a DBMS?
A **Database Management System** is software that stores data and lets many users and applications read and change it **safely**. Examples: PostgreSQL, MySQL, SQLite, Oracle.

Compared with saving data in plain files, a DBMS gives you:
- **Integrity** - rules (constraints) that keep data valid.
- **Concurrency** - many users at once without corrupting data.
- **Transactions** - a group of changes either fully happens or not at all (ACID).
- **Querying** - ask questions with a declarative language, SQL.

## The relational model
Data lives in **relations** (tables). You describe *what* you want with SQL and the DBMS works out *how* to get it.

## Key vocabulary
- **Schema** - the structure: tables, columns, types, constraints.
- **Instance** - the actual data stored at a moment in time.
- **DDL** (CREATE, ALTER, DROP) defines structure; **DML** (SELECT, INSERT, UPDATE, DELETE) works with data.""",
                    "task": {
                        "id": "sql_t1_dbms_quiz",
                        "title": "DBMS concepts check",
                        "type": "quiz",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 25,
                        "pass_mark": 100,
                        "questions": [
                            q("Which of these is a DBMS?", ["Excel formula", "PostgreSQL", "HTML", "JSON"], 1, "PostgreSQL is a relational database management system.", "DBMS Concepts"),
                            q("CREATE TABLE belongs to which category of SQL?", ["DML", "DDL", "DCL", "TCL"], 1, "DDL (Data Definition Language) defines structure.", "DBMS Concepts"),
                            q("What does a transaction guarantee?", ["Faster queries", "A group of changes happens completely or not at all", "Automatic backups", "Unlimited storage"], 1, "Atomicity: all-or-nothing.", "DBMS Concepts"),
                        ],
                        "hints": [
                            "Think about which items are software for storing and managing data.",
                            "DDL defines structure, DML manipulates the data inside it.",
                            "PostgreSQL is the DBMS; CREATE TABLE is DDL; transactions are all-or-nothing.",
                        ],
                    },
                },
                {
                    "id": "sql_l1_tables",
                    "title": "Tables, Rows & Columns",
                    "concept": "Tables & Rows",
                    "summary": "A table has named, typed columns. Each row is one record. SELECT * FROM table returns every row and column.",
                    "minutes": 15,
                    "content": f"""## Tables
A **table** stores one kind of thing (employees, departments...).
- Each **column** (attribute) has a name and a data type: `INTEGER`, `TEXT`, `DATE`...
- Each **row** (tuple/record) is one employee, one department...

## Your first query
```sql
SELECT * FROM employees;
```
`*` means *all columns*. SQL keywords are not case-sensitive, but writing them in capitals keeps queries readable. End statements with `;`.

{SQL_SCHEMA_NOTE}

Use **Run** to explore the tables before submitting - for example `SELECT * FROM projects;`.""",
                    "task": {
                        "id": "sql_t2_select_all",
                        "title": "List every department",
                        "type": "sql",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 25,
                        "prompt": "Return every column and every row of the `departments` table.",
                        "starter": "-- Return all departments\nSELECT ",
                        "reference_sql": "SELECT * FROM departments;",
                        "hints": [
                            "There is a shorthand for 'all columns'.",
                            "Use SELECT with * and name the table after FROM.",
                            "SELECT * FROM departments;",
                        ],
                    },
                },
                {
                    "id": "sql_l1_keys",
                    "title": "Primary Keys & Foreign Keys",
                    "concept": "Keys & Relationships",
                    "summary": "A primary key uniquely identifies each row. A foreign key references another table's primary key and links the two tables together.",
                    "minutes": 15,
                    "content": """## Primary key
A **primary key** uniquely identifies each row. It must be **unique** and **not NULL**.
```sql
CREATE TABLE departments (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
```

## Foreign key
A **foreign key** in one table points at the primary key of another:
```sql
CREATE TABLE employees (
    id      INTEGER PRIMARY KEY,
    name    TEXT,
    dept_id INTEGER REFERENCES departments(id)
);
```
`employees.dept_id` links each employee to a department. The DBMS can refuse values that do not exist in `departments` (**referential integrity**).

## Candidate and composite keys
- A **candidate key** is any column set that could be the primary key (e.g. email).
- A **composite key** uses more than one column, e.g. `(student_id, course_id)` in an enrolments table.""",
                    "task": {
                        "id": "sql_t3_keys_quiz",
                        "title": "Keys check",
                        "type": "quiz",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 25,
                        "pass_mark": 100,
                        "questions": [
                            q("Which property must a primary key have?", ["It must be TEXT", "Unique and not NULL", "It must be the first column", "It must be a foreign key"], 1, "Primary keys uniquely identify rows and cannot be NULL.", "Keys & Relationships"),
                            q("In our dataset, employees.dept_id is...", ["A primary key", "A foreign key referencing departments.id", "A composite key", "Not a key"], 1, "It references the departments table.", "Keys & Relationships"),
                            q("An enrolments table keyed by (student_id, course_id) uses a...", ["Composite key", "Foreign key only", "Surrogate index", "Candidate view"], 0, "Two columns together form the key.", "Keys & Relationships"),
                        ],
                        "hints": [
                            "A primary key's job is to identify exactly one row.",
                            "A foreign key's value points at another table's primary key.",
                            "Unique and not NULL; dept_id is a foreign key; two columns together = composite key.",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "sql_a1",
                "title": "Level 1 Assessment: Database Fundamentals",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("A single record in a table is called a...", ["Column", "Row", "Schema", "Key"], 1, "Rows are records; columns are attributes.", "Tables & Rows"),
                    q("What does referential integrity prevent?", ["Duplicate column names", "Foreign key values that do not exist in the referenced table", "Slow queries", "Lower-case keywords"], 1, "Foreign keys must match an existing primary key (or be NULL).", "Keys & Relationships"),
                    q("Which statement is DML?", ["CREATE TABLE", "DROP TABLE", "UPDATE", "ALTER TABLE"], 2, "UPDATE changes data; the others change structure.", "DBMS Concepts"),
                    q("Why can a primary key not be NULL?", ["NULL is too slow", "NULL cannot identify a specific row", "SQL forbids NULL everywhere", "Only foreign keys allow NULL in SQLite"], 1, "A key must identify exactly one row.", "Keys & Relationships"),
                ],
            },
        },
        {
            "number": 2,
            "title": "SQL Fundamentals",
            "description": "Retrieving data with SELECT, filtering with WHERE, sorting with ORDER BY, removing duplicates with DISTINCT and limiting results.",
            "lessons": [
                {
                    "id": "sql_l2_where",
                    "title": "SELECT & WHERE",
                    "concept": "Filtering (WHERE)",
                    "summary": "List the columns you want after SELECT and filter rows with WHERE conditions combined with AND / OR.",
                    "minutes": 15,
                    "content": f"""## Choosing columns
```sql
SELECT name, salary FROM employees;
```

## Filtering rows
```sql
SELECT name FROM employees WHERE salary > 60000;
SELECT name FROM employees WHERE dept_id = 1 AND hire_year >= 2016;
```
- Comparison: `=  <>  <  >  <=  >=`
- Combine with `AND`, `OR`, `NOT`; use parentheses to group.
- Text values go in **single quotes**: `WHERE name = 'Asha'`.
- `NULL` is not equal to anything - test it with `IS NULL` / `IS NOT NULL`.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t4_where",
                        "title": "Marketing team salaries",
                        "type": "sql",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 30,
                        "prompt": "Return the `name` and `salary` of every employee whose `dept_id` is `2`.",
                        "starter": "SELECT name, salary\nFROM employees\n",
                        "reference_sql": "SELECT name, salary FROM employees WHERE dept_id = 2;",
                        "hints": [
                            "You need to keep only some rows - which clause filters rows?",
                            "Add a WHERE condition on the dept_id column.",
                            "SELECT name, salary FROM employees WHERE dept_id = 2;",
                        ],
                    },
                },
                {
                    "id": "sql_l2_order",
                    "title": "ORDER BY & DISTINCT",
                    "concept": "Sorting & DISTINCT",
                    "summary": "ORDER BY sorts results (ASC by default, DESC for descending). DISTINCT removes duplicate rows from the result.",
                    "minutes": 15,
                    "content": f"""## Sorting
```sql
SELECT name, salary FROM employees ORDER BY salary DESC;
SELECT name FROM employees ORDER BY hire_year, name;   -- tie-breaker
```
Without `ORDER BY`, the database may return rows in **any** order - never rely on it.

## Removing duplicates
```sql
SELECT DISTINCT dept_id FROM employees;
```
`DISTINCT` applies to the whole selected row, not just the first column.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t5_distinct",
                        "title": "Distinct hiring years",
                        "type": "sql",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 30,
                        "prompt": "Return each **different** `hire_year` that appears in `employees`, once each, sorted from oldest to newest.",
                        "starter": "SELECT ",
                        "reference_sql": "SELECT DISTINCT hire_year FROM employees ORDER BY hire_year;",
                        "order_matters": True,
                        "hints": [
                            "Two things are needed: removing repeated values and sorting.",
                            "DISTINCT goes right after SELECT; ORDER BY goes at the end (ascending is the default).",
                            "SELECT DISTINCT hire_year FROM employees ORDER BY hire_year;",
                        ],
                    },
                },
                {
                    "id": "sql_l2_limit",
                    "title": "LIMIT",
                    "concept": "Sorting & DISTINCT",
                    "summary": "LIMIT n returns at most n rows. Combined with ORDER BY it answers 'top N' questions.",
                    "minutes": 10,
                    "content": f"""## Top-N queries
```sql
SELECT name, salary
FROM employees
ORDER BY salary DESC
LIMIT 3;
```
`LIMIT` is applied **after** sorting. Without `ORDER BY`, "the first 3 rows" is not well defined.

`OFFSET` skips rows: `LIMIT 3 OFFSET 3` returns rows 4-6 (useful for pagination).

> PostgreSQL and SQLite use `LIMIT`; SQL Server uses `TOP`, and standard SQL also offers `FETCH FIRST n ROWS ONLY`.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t6_top3",
                        "title": "Three highest salaries",
                        "type": "sql",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 30,
                        "prompt": "Return the `name` and `salary` of the three highest-paid employees, highest first.",
                        "starter": "SELECT name, salary\nFROM employees\n",
                        "reference_sql": "SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 3;",
                        "order_matters": True,
                        "hints": [
                            "First put the rows in the right order, then keep only a few.",
                            "Sort by salary in descending order, then limit the number of rows.",
                            "... ORDER BY salary DESC LIMIT 3;",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "sql_a2",
                "title": "Level 2 Assessment: SQL Fundamentals",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("How do you find employees with no department?", ["WHERE dept_id = NULL", "WHERE dept_id IS NULL", "WHERE dept_id = 0", "WHERE NOT dept_id"], 1, "Comparisons with NULL are never true; use IS NULL.", "Filtering (WHERE)"),
                    q("Which clause sorts results?", ["SORT", "GROUP BY", "ORDER BY", "ARRANGE"], 2, "ORDER BY sorts; GROUP BY groups.", "Sorting & DISTINCT"),
                    q("Without ORDER BY, the row order of a result is...", ["Always by primary key", "Alphabetical", "Not guaranteed", "Reverse insertion order"], 2, "SQL makes no promise about order without ORDER BY.", "Sorting & DISTINCT"),
                    q("In SELECT ... ORDER BY salary DESC LIMIT 3, when is LIMIT applied?", ["Before sorting", "After sorting", "Instead of sorting", "Only on the first column"], 1, "Rows are sorted first, then limited.", "Sorting & DISTINCT"),
                ],
            },
        },
        {
            "number": 3,
            "title": "Data Manipulation",
            "description": "Changing data with INSERT, UPDATE and DELETE, and protecting it with constraints.",
            "lessons": [
                {
                    "id": "sql_l3_insert",
                    "title": "INSERT",
                    "concept": "Data Manipulation",
                    "summary": "INSERT INTO table (columns) VALUES (...) adds rows. Listing the columns explicitly makes the statement clear and safe.",
                    "minutes": 15,
                    "content": f"""## Adding rows
```sql
INSERT INTO departments (id, name) VALUES (5, 'Research');
```
- Name the columns, then give values **in the same order**.
- Text goes in single quotes; numbers do not.
- Several rows at once: `VALUES (6, 'Legal'), (7, 'Support');`
- Constraints still apply: inserting a duplicate primary key fails.

In this course each run starts from a **fresh copy** of the dataset, so you cannot break anything - experiment freely.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t7_insert",
                        "title": "Add the Research department",
                        "type": "sql",
                        "difficulty": "Beginner",
                        "minutes": 10,
                        "xp": 30,
                        "prompt": "Insert a new department with `id` **5** and `name` **Research**.",
                        "starter": "INSERT INTO departments ",
                        "reference_sql": "INSERT INTO departments (id, name) VALUES (5, 'Research');",
                        "check_sql": "SELECT id, name FROM departments ORDER BY id;",
                        "hints": [
                            "Adding a new row uses the INSERT statement.",
                            "List the columns (id, name) and then the VALUES in the same order; text needs single quotes.",
                            "INSERT INTO departments (id, name) VALUES (5, 'Research');",
                        ],
                    },
                },
                {
                    "id": "sql_l3_update_delete",
                    "title": "UPDATE & DELETE",
                    "concept": "Data Manipulation",
                    "summary": "UPDATE changes existing rows and DELETE removes them. Both affect every row unless a WHERE clause restricts them.",
                    "minutes": 15,
                    "content": f"""## Changing rows
```sql
UPDATE employees SET salary = salary + 5000 WHERE id = 8;
```
`SET` can use the column's current value. Several columns: `SET a = 1, b = 2`.

## Removing rows
```sql
DELETE FROM projects WHERE budget < 40000;
```

## The golden rule
**Without a WHERE clause, UPDATE and DELETE affect every row in the table.** Write the `WHERE` first, and test it as a `SELECT` before turning it into an `UPDATE`/`DELETE`:
```sql
SELECT * FROM employees WHERE dept_id = 3;   -- check which rows match
```

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t8_update",
                        "title": "Give Sales a 10% raise",
                        "type": "sql",
                        "difficulty": "Intermediate",
                        "minutes": 15,
                        "xp": 35,
                        "prompt": "Increase the `salary` of every employee in department **3** (Sales) by 10%. Nobody else's salary may change.",
                        "starter": "UPDATE employees\n",
                        "reference_sql": "UPDATE employees SET salary = salary * 1.1 WHERE dept_id = 3;",
                        "check_sql": "SELECT id, salary FROM employees ORDER BY id;",
                        "hints": [
                            "Changing existing rows uses UPDATE ... SET - and something must stop it from touching every row.",
                            "The new value can be computed from the old one; restrict the rows with WHERE dept_id = 3.",
                            "UPDATE employees SET salary = salary * 1.1 WHERE dept_id = 3;",
                        ],
                    },
                },
                {
                    "id": "sql_l3_constraints",
                    "title": "Constraints",
                    "concept": "Constraints",
                    "summary": "Constraints (PRIMARY KEY, NOT NULL, UNIQUE, CHECK, FOREIGN KEY, DEFAULT) let the database reject invalid data.",
                    "minutes": 15,
                    "content": """## Rules the database enforces
```sql
CREATE TABLE students (
    id     INTEGER PRIMARY KEY,
    email  TEXT NOT NULL UNIQUE,
    age    INTEGER CHECK (age >= 16),
    status TEXT DEFAULT 'active',
    dept_id INTEGER REFERENCES departments(id)
);
```
| Constraint | Meaning |
|---|---|
| `PRIMARY KEY` | unique + not null row identifier |
| `NOT NULL` | a value is required |
| `UNIQUE` | no two rows share the value |
| `CHECK (...)` | the condition must be true |
| `DEFAULT` | value used when none is given |
| `REFERENCES` | foreign key to another table |

Constraints move validation **into the database**, so every application that writes data is protected - not just the one that remembered to check.""",
                    "task": {
                        "id": "sql_t9_constraints_quiz",
                        "title": "Constraints check",
                        "type": "quiz",
                        "difficulty": "Intermediate",
                        "minutes": 10,
                        "xp": 30,
                        "pass_mark": 100,
                        "questions": [
                            q("Which constraint stops two students registering the same email?", ["NOT NULL", "UNIQUE", "DEFAULT", "CHECK"], 1, "UNIQUE forbids duplicate values.", "Constraints"),
                            q("INSERT INTO students (id, email, age) VALUES (1, 'a@x.com', 12) with CHECK (age >= 16) will...", ["Succeed with age 16", "Fail with a constraint error", "Succeed and set age NULL", "Succeed silently"], 1, "The CHECK condition is false, so the row is rejected.", "Constraints"),
                            q("What does DEFAULT 'active' do?", ["Forces every value to 'active'", "Uses 'active' when no value is supplied", "Makes the column unique", "Creates an index"], 1, "DEFAULT fills in a value only when none is provided.", "Constraints"),
                        ],
                        "hints": [
                            "Each constraint guards against one specific kind of bad data.",
                            "Duplicates are stopped by one constraint; conditions on values by another.",
                            "UNIQUE stops duplicates; the CHECK makes the insert fail; DEFAULT applies only when no value is given.",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "sql_a3",
                "title": "Level 3 Assessment: Data Manipulation",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("What does UPDATE employees SET salary = 0; do?", ["Nothing without WHERE", "Sets every employee's salary to 0", "Fails with an error", "Updates only the first row"], 1, "Without WHERE, every row is affected.", "Data Manipulation"),
                    q("Best practice before running a DELETE with a WHERE clause is to...", ["Drop the table", "Run the same WHERE as a SELECT first", "Remove all constraints", "Add LIMIT 1000"], 1, "Check which rows match before deleting them.", "Data Manipulation"),
                    q("Inserting a row whose primary key already exists will...", ["Replace the old row", "Fail with a constraint violation", "Create a duplicate", "Be ignored"], 1, "Primary keys must be unique.", "Constraints"),
                    q("Which keyword adds rows to a table?", ["ADD", "INSERT INTO", "APPEND", "UPDATE"], 1, "INSERT INTO ... VALUES ...", "Data Manipulation"),
                ],
            },
        },
        {
            "number": 4,
            "title": "SQL Operations",
            "description": "Summarising data with aggregate functions, grouping with GROUP BY / HAVING, and combining tables with joins.",
            "lessons": [
                {
                    "id": "sql_l4_aggregates",
                    "title": "Aggregate Functions",
                    "concept": "Aggregates & GROUP BY",
                    "summary": "COUNT, SUM, AVG, MIN and MAX reduce many rows to a single value. COUNT(*) counts rows; COUNT(column) skips NULLs.",
                    "minutes": 15,
                    "content": f"""## Summarising rows
```sql
SELECT COUNT(*) FROM employees;            -- number of rows
SELECT MAX(salary), MIN(salary) FROM employees;
SELECT AVG(salary) FROM employees WHERE dept_id = 1;
```
| Function | Returns |
|---|---|
| `COUNT(*)` | number of rows |
| `COUNT(col)` | number of non-NULL values |
| `SUM(col)` / `AVG(col)` | total / average |
| `MIN(col)` / `MAX(col)` | smallest / largest |

Give results readable names with aliases: `SELECT AVG(salary) AS avg_salary ...`

Aggregates **cannot** appear in `WHERE` (which filters individual rows) - that is what `HAVING` is for (next lesson).

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t10_aggregate",
                        "title": "Headcount and average salary",
                        "type": "sql",
                        "difficulty": "Intermediate",
                        "minutes": 10,
                        "xp": 35,
                        "prompt": "Return a single row with two columns: the total number of employees and their average salary.",
                        "starter": "SELECT \nFROM employees;",
                        "reference_sql": "SELECT COUNT(*), AVG(salary) FROM employees;",
                        "hints": [
                            "Both values summarise many rows into one - which kind of function does that?",
                            "One function counts rows, another averages a column. Put both in the SELECT list.",
                            "SELECT COUNT(*), AVG(salary) FROM employees;",
                        ],
                    },
                },
                {
                    "id": "sql_l4_groupby",
                    "title": "GROUP BY & HAVING",
                    "concept": "Aggregates & GROUP BY",
                    "summary": "GROUP BY splits rows into groups and computes aggregates per group. HAVING filters groups after aggregation; WHERE filters rows before.",
                    "minutes": 20,
                    "content": f"""## One result per group
```sql
SELECT dept_id, COUNT(*) AS headcount
FROM employees
GROUP BY dept_id;
```
Every column in `SELECT` must either be in `GROUP BY` or be inside an aggregate.

## Filtering groups
```sql
SELECT dept_id, AVG(salary)
FROM employees
GROUP BY dept_id
HAVING AVG(salary) > 60000;
```

## WHERE vs HAVING
| | Filters | Can use aggregates? |
|---|---|---|
| `WHERE` | individual rows, **before** grouping | no |
| `HAVING` | whole groups, **after** grouping | yes |

Order of clauses: `SELECT ... FROM ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT`

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t11_having",
                        "title": "Departments with more than two people",
                        "type": "sql",
                        "difficulty": "Intermediate",
                        "minutes": 15,
                        "xp": 40,
                        "prompt": "For each `dept_id` that has **more than 2** employees, return the `dept_id` and its number of employees.",
                        "starter": "SELECT dept_id, COUNT(*)\nFROM employees\n",
                        "reference_sql": "SELECT dept_id, COUNT(*) FROM employees GROUP BY dept_id HAVING COUNT(*) > 2;",
                        "hints": [
                            "You need one result row per department, then keep only some departments.",
                            "Group the rows by dept_id; a condition on COUNT(*) has to go in HAVING, not WHERE.",
                            "... GROUP BY dept_id HAVING COUNT(*) > 2;",
                        ],
                    },
                },
                {
                    "id": "sql_l4_joins",
                    "title": "Joins",
                    "concept": "Joins",
                    "summary": "JOIN combines rows from two tables that match an ON condition. INNER JOIN keeps only matches; LEFT JOIN keeps every row of the left table.",
                    "minutes": 20,
                    "content": f"""## Combining tables
```sql
SELECT e.name, d.name
FROM employees e
JOIN departments d ON e.dept_id = d.id;
```
- `e` and `d` are **table aliases** - shorter names you can use everywhere in the query.
- The `ON` condition says how rows match: usually foreign key = primary key.
- **Forgetting `ON`** (or writing a wrong condition) pairs every employee with every department - a **Cartesian product** with far too many rows.

## INNER vs LEFT JOIN
- `JOIN` / `INNER JOIN`: only employees **with** a matching department (Omar, with NULL `dept_id`, disappears).
- `LEFT JOIN`: **all** employees; department columns are NULL when there is no match.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t12_join",
                        "title": "Employees with their department",
                        "type": "sql",
                        "difficulty": "Intermediate",
                        "minutes": 15,
                        "xp": 40,
                        "prompt": "Return each employee's `name` together with their department's `name`, for employees who belong to a department. Sort by employee name (A to Z).",
                        "starter": "SELECT e.name, d.name\nFROM employees e\n",
                        "reference_sql": "SELECT e.name, d.name FROM employees e JOIN departments d ON e.dept_id = d.id ORDER BY e.name;",
                        "order_matters": True,
                        "hints": [
                            "The department name lives in a different table, so two tables must be combined.",
                            "JOIN departments and match employees.dept_id to departments.id with ON; an inner join already drops employees without a department.",
                            "... JOIN departments d ON e.dept_id = d.id ORDER BY e.name;",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "sql_a4",
                "title": "Level 4 Assessment: SQL Operations",
                "kind": "assessment",
                "minutes": 10,
                "xp": 60,
                "pass_mark": 75,
                "questions": [
                    q("Where must a condition on COUNT(*) go?", ["WHERE", "HAVING", "ORDER BY", "FROM"], 1, "Aggregates are filtered in HAVING, after grouping.", "Aggregates & GROUP BY"),
                    q("A join returns 40 rows for 10 employees and 4 departments. What is likely wrong?", ["Nothing", "The ON condition is missing, creating a Cartesian product", "The LIMIT is wrong", "DISTINCT is missing"], 1, "10 x 4 = 40: every combination was produced.", "Joins"),
                    q("Which join keeps employees that have no department?", ["INNER JOIN", "LEFT JOIN employees -> departments", "CROSS JOIN only", "None"], 1, "LEFT JOIN keeps all rows from the left table.", "Joins"),
                    q("COUNT(dept_id) on our employees table returns...", ["10", "9 - it skips the NULL", "4", "1"], 1, "COUNT(column) ignores NULL values; Omar's dept_id is NULL.", "Aggregates & GROUP BY"),
                ],
            },
        },
        {
            "number": 5,
            "title": "Advanced Database Concepts",
            "description": "Subqueries, normalization and relationships, and indexing fundamentals. Ends with the final course assessment.",
            "lessons": [
                {
                    "id": "sql_l5_subqueries",
                    "title": "Subqueries",
                    "concept": "Subqueries",
                    "summary": "A subquery is a SELECT inside another statement. Scalar subqueries return one value; IN subqueries return a list.",
                    "minutes": 20,
                    "content": f"""## Queries inside queries
**Scalar subquery** - returns one value:
```sql
SELECT name FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);
```
**IN subquery** - returns a list:
```sql
SELECT name FROM departments
WHERE id IN (SELECT dept_id FROM projects WHERE budget > 50000);
```
The inner query runs first (conceptually) and its result is used by the outer query.

## Subquery or join?
Many subqueries can be rewritten as joins. Use whichever reads more clearly; modern optimisers often run both the same way.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t13_subquery",
                        "title": "Above-average earners",
                        "type": "sql",
                        "difficulty": "Advanced",
                        "minutes": 15,
                        "xp": 45,
                        "prompt": "Return the `name` of every employee whose salary is greater than the average salary of all employees. Do not hard-code the average - compute it with a subquery.",
                        "starter": "SELECT name\nFROM employees\nWHERE ",
                        "reference_sql": "SELECT name FROM employees WHERE salary > (SELECT AVG(salary) FROM employees);",
                        "hints": [
                            "The comparison value (the average) must itself be calculated by a query.",
                            "Put SELECT AVG(salary) FROM employees in parentheses on the right side of the > comparison.",
                            "... WHERE salary > (SELECT AVG(salary) FROM employees);",
                        ],
                    },
                },
                {
                    "id": "sql_l5_normalization",
                    "title": "Normalization & Relationships",
                    "concept": "Normalization",
                    "summary": "Normalization removes redundancy by splitting data into related tables (1NF, 2NF, 3NF). Relationships are one-to-one, one-to-many or many-to-many.",
                    "minutes": 20,
                    "content": """## Why normalize?
Storing the department name on every employee row repeats data. If Marketing is renamed, every row must change - miss one and the data is **inconsistent** (an *update anomaly*).

## Normal forms (simplified)
- **1NF** - every column holds a single, atomic value; no repeating groups (no `"SQL, C, Java"` in one cell).
- **2NF** - 1NF, and every non-key column depends on the **whole** primary key (matters for composite keys).
- **3NF** - 2NF, and non-key columns do not depend on **other non-key columns** (no transitive dependencies).

## Relationships
| Type | Example | How it is stored |
|---|---|---|
| One-to-one | user - profile | FK with UNIQUE |
| One-to-many | department - employees | FK on the "many" side |
| Many-to-many | students - courses | a **junction table** with two FKs |""",
                    "task": {
                        "id": "sql_t14_norm_quiz",
                        "title": "Normalization check",
                        "type": "quiz",
                        "difficulty": "Advanced",
                        "minutes": 10,
                        "xp": 35,
                        "pass_mark": 100,
                        "questions": [
                            q("A skills column containing 'SQL, C, Java' violates...", ["1NF", "3NF only", "No normal form", "Referential integrity"], 0, "1NF requires atomic values.", "Normalization"),
                            q("How is a many-to-many relationship between students and courses stored?", ["A foreign key on students", "A junction table with two foreign keys", "One table with a list column", "Two primary keys in one table"], 1, "An enrolments table links the two.", "Normalization"),
                            q("employees(id, dept_id, dept_name): dept_name depends on dept_id, not on id. This breaks...", ["1NF", "3NF (transitive dependency)", "Primary key rules", "Nothing"], 1, "A non-key column depends on another non-key column.", "Normalization"),
                        ],
                        "hints": [
                            "Each normal form forbids one specific kind of redundancy.",
                            "Lists in a cell break the first normal form; dependencies between non-key columns break the third.",
                            "1NF; a junction table; 3NF.",
                        ],
                    },
                },
                {
                    "id": "sql_l5_indexing",
                    "title": "Indexing Fundamentals",
                    "concept": "Indexing",
                    "summary": "An index is a separate sorted structure (usually a B-tree) that makes lookups on a column fast, at the cost of extra storage and slower writes.",
                    "minutes": 15,
                    "content": f"""## What an index does
Without an index, `WHERE dept_id = 3` reads **every** row (a full table scan). An index keeps the column's values sorted with pointers back to the rows, so the database can jump straight to the matches - like a book's index.

```sql
CREATE INDEX idx_employees_dept ON employees (dept_id);
```

## Trade-offs
- Faster `WHERE`, `JOIN` and `ORDER BY` on the indexed column(s).
- Every `INSERT`/`UPDATE`/`DELETE` must also update the index - more indexes means slower writes.
- Extra storage.

## Good candidates
- Foreign key columns used in joins.
- Columns frequently filtered or sorted on.
- Primary keys and `UNIQUE` columns are indexed automatically.

{SQL_SCHEMA_NOTE}""",
                    "task": {
                        "id": "sql_t15_index",
                        "title": "Index the department column",
                        "type": "sql",
                        "difficulty": "Advanced",
                        "minutes": 10,
                        "xp": 40,
                        "prompt": "Create an index named exactly `idx_employees_dept` on the `dept_id` column of `employees`.",
                        "starter": "CREATE INDEX ",
                        "reference_sql": "CREATE INDEX idx_employees_dept ON employees (dept_id);",
                        "check_sql": "SELECT name, tbl_name FROM sqlite_master WHERE type = 'index' AND name = 'idx_employees_dept';",
                        "hints": [
                            "Indexes are created with their own DDL statement.",
                            "CREATE INDEX needs a name, the keyword ON, the table and the column in parentheses.",
                            "CREATE INDEX idx_employees_dept ON employees (dept_id);",
                        ],
                    },
                },
            ],
            "assessment": {
                "id": "sql_final",
                "title": "Final Assessment: DBMS & SQL",
                "kind": "final",
                "minutes": 15,
                "xp": 100,
                "pass_mark": 80,
                "questions": [
                    q("Which query finds departments that have at least one project?", ["SELECT name FROM departments WHERE id IN (SELECT dept_id FROM projects)", "SELECT name FROM departments, projects", "SELECT name FROM departments HAVING projects", "SELECT name FROM departments WHERE projects > 0"], 0, "An IN subquery matches department ids that appear in projects.", "Subqueries"),
                    q("What is the main cost of adding many indexes to a table?", ["Queries return wrong results", "Slower writes and extra storage", "The table becomes read-only", "Joins stop working"], 1, "Every write must maintain each index.", "Indexing"),
                    q("Clause order: which is correct?", ["SELECT, WHERE, FROM, GROUP BY", "SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY", "FROM, SELECT, HAVING, WHERE", "SELECT, FROM, HAVING, WHERE"], 1, "WHERE filters rows before GROUP BY; HAVING filters groups after.", "Aggregates & GROUP BY"),
                    q("A department-employee relationship is...", ["one-to-one", "one-to-many", "many-to-many", "not a relationship"], 1, "One department has many employees; each employee has one department.", "Normalization"),
                    q("SELECT e.name, d.name FROM employees e LEFT JOIN departments d ON e.dept_id = d.id returns how many rows here?", ["9", "10", "4", "40"], 1, "LEFT JOIN keeps all 10 employees, including Omar with a NULL department.", "Joins"),
                ],
            },
        },
    ],
}

COURSES = [C_COURSE, SQL_COURSE]


def _level_id(course_id: str, number: int) -> str:
    return f"{course_id}_lvl{number}"


def content_fingerprint() -> str:
    import hashlib
    payload = json.dumps({"courses": COURSES, "dataset": SQL_DATASET}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def seed_academy(conn) -> None:
    """Idempotently upserts all course content. Never touches student progress.
    Skipped entirely when the stored fingerprint matches (keeps startup fast)."""
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS public.app_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TIMESTAMPTZ DEFAULT now());")
    cur.execute("""
    DO $$ BEGIN
      IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.app_meta'::regclass) THEN
        ALTER TABLE public.app_meta ENABLE ROW LEVEL SECURITY;
      END IF;
    END $$;
    """)
    fingerprint = content_fingerprint()
    cur.execute("SELECT value FROM app_meta WHERE key = 'academy_content_sha256';")
    row = cur.fetchone()
    if row and row["value"] == fingerprint:
        return
    _seed_all(cur)
    cur.execute("""
    INSERT INTO app_meta (key, value) VALUES ('academy_content_sha256', %s)
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now();
    """, (fingerprint,))


def _seed_all(cur) -> None:
    for course in COURSES:
        cur.execute("""
        INSERT INTO courses (id, slug, title, description, language, icon, sort_order, completion_xp, completion_achievement_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET slug = EXCLUDED.slug, title = EXCLUDED.title, description = EXCLUDED.description,
            language = EXCLUDED.language, icon = EXCLUDED.icon, sort_order = EXCLUDED.sort_order,
            completion_xp = EXCLUDED.completion_xp, completion_achievement_id = EXCLUDED.completion_achievement_id;
        """, (course["id"], course["slug"], course["title"], course["description"], course["language"],
              course["icon"], course["sort_order"], course["completion_xp"], course["completion_achievement_id"]))

        for level in course["levels"]:
            level_id = _level_id(course["id"], level["number"])
            cur.execute("""
            INSERT INTO course_levels (id, course_id, level_number, title, description)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, description = EXCLUDED.description,
                level_number = EXCLUDED.level_number;
            """, (level_id, course["id"], level["number"], level["title"], level["description"]))

            for order, lesson in enumerate(level["lessons"], start=1):
                cur.execute("""
                INSERT INTO course_lessons (id, level_id, sort_order, title, summary, content, concept, estimated_minutes, xp_reward)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 10)
                ON CONFLICT (id) DO UPDATE SET level_id = EXCLUDED.level_id, sort_order = EXCLUDED.sort_order,
                    title = EXCLUDED.title, summary = EXCLUDED.summary, content = EXCLUDED.content,
                    concept = EXCLUDED.concept, estimated_minutes = EXCLUDED.estimated_minutes;
                """, (lesson["id"], level_id, order, lesson["title"], lesson["summary"], lesson["content"],
                      lesson["concept"], lesson["minutes"]))
                _upsert_task(cur, level_id, lesson["id"], order, lesson["task"], lesson["concept"], course["language"])

            assessment = dict(level["assessment"])
            assessment["type"] = "quiz"
            assessment.setdefault("difficulty", "Advanced" if level["number"] >= 4 else "Intermediate")
            assessment.setdefault("prompt", f"Answer the questions to complete Level {level['number']}. Pass mark: {assessment['pass_mark']}%.")
            assessment.setdefault("hints", [
                "Re-read the summaries of this level's lessons before answering.",
                "Eliminate options that contradict an example from the lessons.",
                "Each question maps to one lesson in this level - check the concept named in the lesson title.",
            ])
            _upsert_task(cur, level_id, None, 99, assessment, "Level Assessment", course["language"])


def _upsert_task(cur, level_id, lesson_id, order, task, concept, course_language):
    task_type = task["type"]
    is_sql = task_type == "sql"
    cur.execute("""
    INSERT INTO course_tasks (id, level_id, lesson_id, sort_order, title, task_type, kind, prompt, starter_code,
        solution_code, test_cases, setup_sql, reference_sql, check_sql, order_matters, questions, pass_mark,
        hints, concept, difficulty, estimated_minutes, xp_reward)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id) DO UPDATE SET level_id = EXCLUDED.level_id, lesson_id = EXCLUDED.lesson_id,
        sort_order = EXCLUDED.sort_order, title = EXCLUDED.title, task_type = EXCLUDED.task_type, kind = EXCLUDED.kind,
        prompt = EXCLUDED.prompt, starter_code = EXCLUDED.starter_code, solution_code = EXCLUDED.solution_code,
        test_cases = EXCLUDED.test_cases, setup_sql = EXCLUDED.setup_sql, reference_sql = EXCLUDED.reference_sql,
        check_sql = EXCLUDED.check_sql, order_matters = EXCLUDED.order_matters, questions = EXCLUDED.questions,
        pass_mark = EXCLUDED.pass_mark, hints = EXCLUDED.hints, concept = EXCLUDED.concept,
        difficulty = EXCLUDED.difficulty, estimated_minutes = EXCLUDED.estimated_minutes, xp_reward = EXCLUDED.xp_reward;
    """, (
        task["id"], level_id, lesson_id, order, task["title"], task_type, task.get("kind", "practice"),
        task.get("prompt") or f"Answer every question correctly to complete this task (pass mark {task.get('pass_mark', 70)}%).",
        task.get("starter"), task.get("solution"),
        json.dumps(task["tests"]) if task.get("tests") else None,
        SQL_DATASET if is_sql else None,
        task.get("reference_sql"), task.get("check_sql"), bool(task.get("order_matters", False)),
        json.dumps(task["questions"]) if task.get("questions") else None,
        task.get("pass_mark", 70),
        json.dumps(task.get("hints", [])),
        concept, task.get("difficulty", "Beginner"), task.get("minutes", 20), task.get("xp", 25),
    ))
