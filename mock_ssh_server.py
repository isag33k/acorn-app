#!/usr/bin/env python3
"""
Mock SSH Server for testing ACORN application

This is a wrapper script that now uses the simple implementation
which is more reliable than the previous version.
"""

import sys
import os
import logging

# Import the simple SSH server code
from simple_ssh_server import start_server

# Start the server directly from our simple implementation
if __name__ == "__main__":
    print("Starting SSH server using simple implementation")
    start_server()