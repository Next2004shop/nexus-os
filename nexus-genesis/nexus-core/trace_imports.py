
import sys
import os
import time

sys.path.append(os.getcwd())

def trace(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

trace("Starting trace...")

try:
    trace("Importing fastapi...")
    from fastapi import FastAPI
    trace("FastAPI imported.")
except ImportError as e:
    trace(f"Error importing fastapi: {e}")

try:
    trace("Importing app.services.agent_council...")
    from app.services import agent_council
    trace("agent_council imported.")
except ImportError as e:
    trace(f"Error importing agent_council: {e}")

try:
    trace("Importing app.services.model_ensemble...")
    from app.services import model_ensemble
    trace("model_ensemble imported.")
except ImportError as e:
    trace(f"Error importing model_ensemble: {e}")

try:
    trace("Importing app.services.stealth_mode...")
    from app.services import stealth_mode
    trace("stealth_mode imported.")
except ImportError as e:
    trace(f"Error importing stealth_mode: {e}")

try:
    trace("Importing app.main...")
    from app import main
    trace("app.main imported.")
except ImportError as e:
    trace(f"Error importing app.main: {e}")
except Exception as e:
    trace(f"Exception importing app.main: {e}")
    import traceback
    traceback.print_exc()

trace("Trace complete.")
