#!/usr/bin/env python3
"""
Startup script for the fixed SSH server
"""

import logging
import sys
import os
from fixed_ssh_server import start_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fixed_ssh_server.log',
    filemode='a'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

if __name__ == "__main__":
    print("=" * 80)
    print("ACORN Fixed SSH Server - Workflow Version")
    print("=" * 80)
    
    # Get port from environment or use default
    port = int(os.environ.get("SSH_SERVER_PORT", 2223))
    bind = os.environ.get("SSH_SERVER_BIND", "0.0.0.0")
    
    print(f"Starting SSH server on {bind}:{port}...")
    
    try:
        # Start the server (this will run indefinitely)
        start_server(port=port, bind=bind)
    except KeyboardInterrupt:
        print("\nSSH server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        sys.exit(1)