import subprocess
import time
import os
import sys
import webbrowser

def start_nexus():
    print("🔥 NEXUS GOD MODE: INITIALIZING...")
    
    # 1. Start Python Bridge (The Core)
    print("   > Launching Nexus Bridge (Execution Layer)...")
    bridge_process = subprocess.Popen([sys.executable, "nexus_bridge.py"], cwd=os.getcwd())
    
    # 2. Start Node Server (The Host)
    print("   > Launching Nexus Host (Command Center)...")
    # Assuming 'npm run dev' or 'node server.cjs' depending on dev/prod. 
    # For dev environment as per user state:
    server_process = subprocess.Popen(["npm", "run", "dev"], cwd=os.getcwd(), shell=True)
    
    time.sleep(5) # Wait for servers to warm up
    
    # 3. Launch UI
    print("   > Accessing Command Center...")
    webbrowser.open("http://127.0.0.1:3000")
    
    print("✅ SYSTEM ONLINE. STEALTH MODE ACTIVE.")
    print("   Press Ctrl+C to kill all systems.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 SHUTDOWN SEQUENCE INITIATED...")
        bridge_process.terminate()
        # Node process via shell is harder to kill cleanly in python, but this is a start
        print("   Nexus Bridge Terminated.")
        print("   Please manually close the Node terminal if it persists.")
        sys.exit(0)

if __name__ == "__main__":
    start_nexus()
