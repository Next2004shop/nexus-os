import logging
import time
import sys
from pyngrok import ngrok, conf

# Configure Logging
logger = logging.getLogger("NexusTunnel")

def start_tunnel(port=3000):
    """
    Starts a secure Ngrok tunnel to the specified port.
    """
    try:
        logger.info(f"🚇 INITIALIZING SECURE TUNNEL TO PORT {port}...")
        
        # Check if authenticated (Optional but recommended for longer sessions)
        # conf.get_default().auth_token = "YOUR_TOKEN" 

        # Open a HTTP tunnel on the default port 80
        # <NgrokTunnel: "http://<public_sub>.ngrok.io" -> "http://localhost:80">
        public_url = ngrok.connect(port).public_url
        
        logger.info(f"✅ TUNNEL ESTABLISHED: {public_url}")
        logger.info("📱 SCAN QR CODE OR COPY URL TO ACCESS NEXUS ON MOBILE")
        
        return public_url

    except Exception as e:
        logger.error(f"❌ TUNNEL FAILED: {e}")
        return None

def close_tunnel():
    """
    Closes all active tunnels.
    """
    try:
        ngrok.kill()
        logger.info("🛑 TUNNEL CLOSED")
    except Exception as e:
        logger.error(f"Error closing tunnel: {e}")

if __name__ == "__main__":
    # Test Run
    logging.basicConfig(level=logging.INFO)
    url = start_tunnel(3000)
    if url:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            close_tunnel()
