#!/usr/bin/env python3
"""
Simple SSH test client for direct testing without complex paramiko configuration
Uses a simpler low-level approach for testing SSH connectivity
"""

import socket
import sys
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_socket_connection(hostname, port, timeout=5):
    """Test basic socket connectivity to a host:port"""
    logger.info(f"Testing socket connection to {hostname}:{port}")
    
    try:
        # Create a socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Start timing
        start_time = time.time()
        
        # Connect
        result = sock.connect_ex((hostname, port))
        
        # End timing
        elapsed = time.time() - start_time
        
        if result == 0:
            logger.info(f"Socket Connection: SUCCESS - Connected in {elapsed:.2f} seconds")
            
            # Try to read the SSH banner
            try:
                banner = sock.recv(1024)
                banner_str = banner.decode('utf-8', errors='ignore').strip()
                logger.info(f"Received SSH banner: {banner_str}")
                
                # Send a simple client identification string
                client_id = b"SSH-2.0-ACORN_TestClient\r\n"
                sock.sendall(client_id)
                logger.info(f"Sent client identification: {client_id.decode('utf-8').strip()}")
                
                # Try to read some more data
                resp = sock.recv(1024)
                resp_str = resp.decode('utf-8', errors='ignore').strip()
                logger.info(f"Received response: {resp_str}")
                
            except socket.timeout:
                logger.error("Socket timed out when reading banner")
            except Exception as e:
                logger.error(f"Error reading banner: {str(e)}")
                
            # Simple diagnostics
            logger.info("Socket test completed successfully")
        else:
            logger.error(f"Socket Connection: FAILED - Error code {result}")
            
        # Close socket
        sock.close()
        return result == 0
        
    except Exception as e:
        logger.error(f"Socket Connection: ERROR - {str(e)}")
        return False

def test_connection():
    """Test connection to localhost:2222"""
    hostname = "127.0.0.1"
    port = 2222
    
    print(f"Testing connection to {hostname}:{port}...")
    success = test_socket_connection(hostname, port)
    
    if success:
        print("✅ Socket connection successful!")
    else:
        print("❌ Socket connection failed!")
        
    return success

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)