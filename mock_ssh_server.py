#!/usr/bin/env python3
"""
Mock SSH Server for testing ACORN application

This is a wrapper script that uses the improved implementation from
improved_ssh_server.py for better reliability and debugging.
"""

import sys
import os
import logging

# Import the improved SSH server code
from improved_ssh_server import start_server

# Just start the server directly from our improved implementation
if __name__ == "__main__":
    print("Starting SSH server using improved implementation")
    start_server()