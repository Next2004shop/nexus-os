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
    print("   > Launching Nexus Host (Backend API)...")
    # Using 'node server.cjs' to run the backend server
    # We use Popen so it runs in background
    node_server_process = subprocess.Popen(["node", "server.cjs"], cwd=os.getcwd())

    # 3. Start React/Vite (The Frontend - Dev Mode)
    print("   > Launching Nexus UI (Command Center)...")
    # Assuming 'npm run dev' or 'node server.cjs' depending on dev/prod. 
    # For dev environment as per user state:
    frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd=os.getcwd(), shell=True)
    
    time.sleep(5) # Wait for servers to warm up
    
    # 4. Start Secure Tunnel (God Mode Remote Access)
    try:
        import nexus_tunnel
        import qrcode
        import io
        
        print("\n🚇 INITIALIZING SECURE TUNNEL...")
        public_url = nexus_tunnel.start_tunnel(3000)
        
        if public_url:
            print(f"\n✅ NEXUS REMOTE ACCESS ONLINE: {public_url}")
            print("📱 SCAN THIS QR CODE TO CONNECT MOBILE APP:\n")
            
            # Generate QR Code
            qr = qrcode.QRCode()
            qr.add_data(public_url)
            qr.make(fit=True)
            qr.print_ascii()
            
            print("\n⚠️  KEEP THIS WINDOW OPEN TO MAINTAIN CONNECTION")
            
    except ImportError:
        print("⚠️  Tunnel modules not found. Run 'pip install pyngrok qrcode' to enable remote access.")
    except Exception as e:
        print(f"❌ Tunnel Error: {e}")

    # 5. Launch UI
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
        node_server_process.terminate()
        # Node process via shell is harder to kill cleanly in python, but this is a start
        if 'nexus_tunnel' in sys.modules:
            nexus_tunnel.close_tunnel()
        print("   Nexus Bridge Terminated.")
        print("   Nexus Host Terminated.")
        print("   Please manually close the Node terminal if it persists.")
        sys.exit(0)

if __name__ == "__main__":
    start_nexus()
