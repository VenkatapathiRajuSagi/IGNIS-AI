import subprocess
import sys
import os
import time
import webbrowser
import threading

def open_browser():
    # Wait a moment for server to start
    time.sleep(3)
    print("🌍 Opening Wildfire Dashboard...")
    webbrowser.open("http://localhost:8000")

def check_dependencies():
    print("Checking dependencies...")
    try:
        import uvicorn
        import fastapi
        import ultralytics
        import cv2
        import gtts
        import pygame
        import twilio
    except ImportError as e:
        print(f"Missing dependency: {e.name}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def run_app():
    print("--- Starting IGNIS Wildfire Detection System ---")
    
    # Disable Mac fork safety warnings and fix SDL conflict
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    
    # Auto-open browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn server
    # We exclude 'venv' and 'models' from reload to prevent infinite restart loops
    cmd = [
        sys.executable, "-m", "uvicorn", "backend.main:app", 
        "--reload", 
        "--reload-exclude", "venv/*",
        "--reload-exclude", "models/*",
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutting down system...")

if __name__ == "__main__":
    check_dependencies()
    run_app()
