#!/usr/bin/env python3
"""
Improved Mock SSH Server for testing ACORN application

This script creates a more robust SSH server that handles connections
more reliably and provides better error handling.
"""

import socket
import threading
import paramiko
import sys
import os
import traceback
import logging
import time
from binascii import hexlify

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='improved_ssh_server.log',
    filemode='w'
)

logger = logging.getLogger('ssh_server')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Generate a host key if it doesn't exist
HOST_KEY_PATH = 'mock_ssh_host_key'
if not os.path.exists(HOST_KEY_PATH):
    logger.info("Generating new host key...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_PATH)
    logger.info(f"Host key written to {HOST_KEY_PATH}")
else:
    logger.info(f"Using existing host key from {HOST_KEY_PATH}")

# Load host key
try:
    host_key = paramiko.RSAKey.from_private_key_file(HOST_KEY_PATH)
    logger.info("Host key loaded successfully")
except Exception as e:
    logger.error(f"Failed to load host key: {str(e)}")
    logger.error(traceback.format_exc())
    raise

class MockSSHServer(paramiko.ServerInterface):
    """SSH server implementation"""
    
    def __init__(self):
        self.event = threading.Event()
        logger.debug("Server interface initialized")
        
    def check_channel_request(self, kind, chanid):
        logger.debug(f"Channel request: {kind}, {chanid}")
        if kind == 'session':
            return 0  # OPEN_SUCCEEDED
        return 1  # OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
        
    def check_auth_password(self, username, password):
        logger.debug(f"Password auth attempt: {username}")
        
        # Accept only specific credentials
        if username == 'test' and password == 'Ac0rN$':
            logger.info(f"Successful login: {username}")
            return 0  # AUTH_SUCCESSFUL
            
        logger.warning(f"Failed login attempt: {username}")
        return 1  # AUTH_FAILED
        
    def check_channel_shell_request(self, channel):
        logger.debug("Shell request")
        self.event.set()
        return True
        
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        logger.debug(f"PTY request: {term}, {width}x{height}")
        return True
        
    def check_channel_exec_request(self, channel, command):
        logger.debug(f"Command received: {command}")
        
        # The command handling is done in the handle_client function
        # This just signals that the command is accepted
        self.event.set()
        return True

def handle_client(client, addr):
    """Handle SSH client connections"""
    logger.info(f"Connection from {addr}")
    
    try:
        # Create transport
        transport = paramiko.Transport(client)
        transport.set_gss_host(socket.getfqdn(""))
        
        # Add server host key
        transport.add_server_key(host_key)
        
        # Start server
        server = MockSSHServer()
        try:
            transport.start_server(server=server)
        except paramiko.SSHException as e:
            logger.error(f"SSH negotiation failed: {str(e)}")
            client.close()
            return
            
        # Wait for auth
        channel = transport.accept(20)
        if channel is None:
            logger.error("No channel established")
            transport.close()
            return
            
        # Wait for shell or exec request
        server.event.wait(10)
        if not server.event.is_set():
            logger.error("Client never asked for shell/exec")
            transport.close()
            return
            
        # Handle commands
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8')
            logger.debug(f"Received data: {data}")
        
        # Get the command from the session
        command = ""
        if hasattr(channel, 'get_command'):
            command = channel.get_command().decode('utf-8')
            logger.info(f"Command received: {command}")

        # Send banner
        channel.send(b"Welcome to ACORN Mock Router\r\n")
        
        # Process commands
        if command:
            # Direct command execution (SSH client.exec_command)
            process_command(channel, command)
        else:
            # Interactive session
            channel.send(b"mock-router> ")
            
            while True:
                # Check if channel is closed
                if channel.closed or not channel.recv_ready():
                    if not channel.recv_ready():
                        time.sleep(0.1)
                        continue
                    break
                
                # Get command from channel
                command = channel.recv(1024).decode('utf-8').strip()
                logger.debug(f"Interactive command: {command}")
                
                # Process the command
                process_command(channel, command)
                
                # Send prompt
                channel.send(b"mock-router> ")
        
        # Close channel
        channel.close()
        
    except Exception as e:
        logger.error(f"Error handling client: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        try:
            transport.close()
        except:
            pass
        
        logger.info(f"Connection from {addr} closed")

def process_command(channel, command):
    """Process a command and send response to channel"""
    # Log the command
    logger.info(f"Processing command: {command}")
    
    # Define responses based on command
    if command.startswith("show version"):
        response = """
ACORN Mock Router v1.0
Model: Virtual-1000
Serial: VM12345678
Build date: 2025-03-28
Last boot: 2025-03-27 08:00:00
Uptime: 1 day, 4 hours, 45 minutes
"""
    elif command.startswith("show interface ge-0/0/0"):
        response = """
Interface ge-0/0/0, Enabled, Physical link is Up
  Description: Uplink to Provider
  MAC address: 00:00:5e:00:53:01
  MTU: 1500 bytes
  Last flapped: 2025-03-27 08:00:00
  Input rate: 5.2 Mbps (3200 pps)
  Output rate: 2.1 Mbps (1500 pps)
"""
    elif command.startswith("show circuit id TEST-001"):
        response = """
Circuit ID: TEST-001
  Status: Active
  Type: Ethernet
  Customer: ACORN Test Customer
  Bandwidth: 100 Mbps
  Last checked: 2025-03-28 08:00:00
  Input errors: 0
  Output errors: 0
  Uptime: 99.998%
"""
    elif command.startswith("show circuit id TEST-002"):
        response = """
Circuit ID: TEST-002
  Status: Active (Warning)
  Type: Ethernet
  Customer: ACORN Test Customer 2
  Bandwidth: 50 Mbps
  Last checked: 2025-03-28 08:00:00
  Input errors: 52
  Output errors: 12
  Uptime: 99.95%
  Notes: Intermittent errors detected
"""
    elif command.startswith("show circuit id TEST-"):
        circuit_id = command.split("TEST-")[1].strip()
        response = f"""
Circuit ID: TEST-{circuit_id}
  Status: Unknown
  Type: Ethernet
  Customer: Unknown
  Bandwidth: Unknown
  Last checked: Never
  Notes: This circuit is not fully configured
"""
    else:
        response = f"Command not recognized. Try 'show version', 'show interface ge-0/0/0', or 'show circuit id TEST-001'."
    
    # Send response (converting string to bytes)
    channel.send((response.strip() + "\r\n").encode('utf-8'))

def start_server(port=2222, bind='0.0.0.0'):
    """Start the mock SSH server"""
    # Create socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))
    except Exception as e:
        logger.error(f"Socket bind failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    
    # Start listening
    try:
        sock.listen(100)
        logger.info(f"Listening for connections on {bind}:{port}")
    except Exception as e:
        logger.error(f"Socket listen failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
        
    # Accept connections
    while True:
        try:
            client, addr = sock.accept()
            logger.debug(f"Accepted connection from {addr}")
            
            # Handle client in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(client, addr))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")
            break
    
    # Close socket
    try:
        sock.close()
    except:
        pass

if __name__ == "__main__":
    start_server()