#!/usr/bin/env python3
"""
Mock SSH Server for ACORN Application Testing

NOTE: This mock server is maintained for legacy testing purposes only.
The application now supports connections to real SSH servers.

For new development and testing, please use actual network equipment
or dedicated test servers with SSH access.
"""

import sys
import os
import logging
import time

# Import the simple SSH server code
from simple_ssh_server import start_server

# Display transitional message
print("=" * 80)
print("NOTICE: Mock SSH Server for ACORN Application")
print("=" * 80)
print("This mock server is maintained for legacy testing purposes only.")
print("The ACORN application now supports connections to real SSH servers.")
print("")
print("For production deployments, please use actual network equipment")
print("or dedicated SSH servers with proper credentials.")
print("=" * 80)
print("")

# Start the server directly from our simple implementation
if __name__ == "__main__":
    print("Starting mock SSH server on port 2222...")
    try:
        # Restart the SSH server to ensure we have the latest code changes
        print("Restarting SSH server with enhanced OLT simulation...")
        start_server()
    except KeyboardInterrupt:
        print("\nSSH server stopped by user")
    except Exception as e:
        print(f"SSH server error: {str(e)}")
        print("Attempting to restart server...")
        time.sleep(2)
        try:
            start_server()
        except Exception as e2:
            print(f"Failed to restart server: {str(e2)}")
            sys.exit(1)