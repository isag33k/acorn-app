#!/usr/bin/env python3
"""
Utility to check if a port is open on a host
"""

import socket
import sys
import argparse
import time

def check_port(host, port):
    """Check if port is open on host"""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Try to connect
        print(f"Checking if port {port} is open on {host}...")
        start_time = time.time()
        result = sock.connect_ex((host, port))
        elapsed = time.time() - start_time
        
        if result == 0:
            print(f"SUCCESS: Port {port} is open on {host} (connected in {elapsed:.2f}s)")
            return True
        else:
            print(f"FAILURE: Port {port} is not open on {host} (error code: {result})")
            return False
    except socket.gaierror:
        print(f"ERROR: Hostname {host} could not be resolved")
        return False
    except socket.error as e:
        print(f"ERROR: {str(e)}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check if port is open on host")
    parser.add_argument("host", help="Hostname or IP address")
    parser.add_argument("port", type=int, help="Port number")
    args = parser.parse_args()
    
    success = check_port(args.host, args.port)
    sys.exit(0 if success else 1)