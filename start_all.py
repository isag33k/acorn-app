#!/usr/bin/env python3
"""
Script to start both the main application and the mock SSH server.
This allows you to test the SSH functionality.
"""

import os
import subprocess
import sys
import time
import threading
import signal
import atexit

# Add the mock SSH server to the database
print("Setting up the mock SSH server in the database...")
try:
    from add_mock_ssh_server import add_mock_ssh_server
    add_mock_ssh_server()
except Exception as e:
    print(f"Error setting up the database: {e}")
    # Continue anyway, it might already be set up

# Function to run the mock SSH server
def run_ssh_server():
    print("Starting mock SSH server on port 2222...")
    subprocess.run([sys.executable, "mock_ssh_server.py"])

# Start the SSH server in a background thread
ssh_thread = threading.Thread(target=run_ssh_server, daemon=True)
ssh_thread.start()

# Wait a moment for the SSH server to start
time.sleep(2)

# Start the main application
print("Starting main application...")
os.system("gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app")