"""
AI Coding Mentor - Application Runner
Launches the unified full-stack application on port 8000.
"""
import sys
import os
import glob

# Ensure Windows 11 Smart App Control & libpq resolution helper
if sys.platform == "win32":
    libs_dir = os.path.join(sys.prefix, "Lib", "site-packages", "psycopg2_binary.libs")
    if os.path.exists(libs_dir):
        libpq_dll = os.path.join(libs_dir, "libpq.dll")
        if not os.path.exists(libpq_dll):
            matches = glob.glob(os.path.join(libs_dir, "libpq*.dll"))
            if matches:
                import shutil
                shutil.copyfile(matches[0], libpq_dll)
        if libs_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = libs_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ.setdefault("PSYCOPG_IMPL", "python")

# Set backend in Python path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings

def main():
    print("=" * 65)
    print("  AI CODING MENTOR - INTELLIGENT ADAPTIVE LEARNING PLATFORM")
    print("=" * 65)

    if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
        print("\n[!] SUPABASE DATABASE REQUIRED:")
        print("    DATABASE_URL is not set in backend/.env")
        print("    Please follow the instructions in SUPABASE_AND_OLLAMA_SETUP_GUIDE.md:")
        print("    1. Create a Supabase project at https://supabase.com")
        print("    2. Copy your Connection string (URI) from Connect -> URI")
        print("    3. Paste into backend/.env: DATABASE_URL=postgresql://...")
        print("    4. Run 'python run_app.py' again.\n")
        sys.exit(1)

    from app.database.session import init_database
    print("[1/2] Connecting to Supabase PostgreSQL and initializing schema...")
    try:
        init_database()
        print("      -> Supabase connection verified successfully.")
    except Exception as e:
        print(f"      -> Warning during schema initialization: {e}")

    print(f"[2/2] Local LLM: Ollama ({settings.OLLAMA_MODEL} at {settings.OLLAMA_BASE_URL})")
    print("      -> Starting server on http://127.0.0.1:8000")
    print("      -> Open your browser at: http://127.0.0.1:8000")
    print("      -> Interactive API Docs at: http://127.0.0.1:8000/docs")
    print("=" * 65)

    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
