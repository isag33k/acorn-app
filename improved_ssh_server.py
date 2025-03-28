#!/usr/bin/env python3
"""
Improved Mock SSH Server for testing ACORN application

This script creates a more robust SSH server that handles connections
more reliably and provides better error handling.
"""

import socket
import sys
import threading
import paramiko
import os
import time
import logging
from binascii import hexlify

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='improved_ssh_server.log',
    filemode='w'
)
logger = logging.getLogger("SSH_SERVER")

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

# Generate a host key or use an existing one
HOST_KEY_PATH = "mock_ssh_host_key"
if os.path.exists(HOST_KEY_PATH):
    host_key = paramiko.RSAKey(filename=HOST_KEY_PATH)
    logger.info(f"Using existing host key: {HOST_KEY_PATH}")
else:
    host_key = paramiko.RSAKey.generate(2048)
    host_key.write_private_key_file(HOST_KEY_PATH)
    logger.info(f"Generated new host key: {HOST_KEY_PATH}")

# Print the key fingerprint
print(f"Server key fingerprint: {hexlify(host_key.get_fingerprint())}")

# Mock command responses
COMMAND_RESPONSES = {
    "show version": """
ACORN Mock Router v1.0
Model: Virtual-1000
Serial: VM12345678
Build date: 2025-03-28
Last boot: 2025-03-27 08:00:00
Uptime: 1 day, 4 hours, 45 minutes

mock-router> 
""",
    "show interface ge-0/0/0": """
Interface ge-0/0/0, Physical link is Up
  Description: Uplink to Provider A
  MAC address: 00:11:22:33:44:55
  Bandwidth: 1000mbps
  Duplex: Full
  Auto-negotiation: Enabled
  Statistics:
    Input packets: 15483901
    Output packets: 12399423
    Input errors: 0
    Output errors: 0
  Last flap: 2025-03-27 08:00:00
  Input rate     : 487944 bps (617 pps)
  Output rate    : 3358392 bps (738 pps)

mock-router> 
""",
    "show circuit id TEST-001": """
Circuit ID: TEST-001
  Status: ACTIVE
  Type: Ethernet
  Provider: Mock Provider
  Bandwidth: 100 Mbps
  Customer VLAN: 100
  Provider VLAN: 1000
  Last status change: 2025-03-27 09:15:33
  Last error: None
  Notes: This is a test circuit for demo purposes

mock-router> 
""",
    "show service TEST-002": """
Service ID: TEST-002
  Customer: ACME Corporation
  Status: ACTIVE
  SLA: 99.95%
  Monitoring: Enabled
  Alert threshold: 90%
  Current utilization: 45%
  POC: John Doe (jdoe@acme.com)

mock-router> 
""",
    "help": """
Available commands:
  show version - Display router version information
  show interface <name> - Display interface status
  show circuit id <id> - Display circuit information
  show service <id> - Display service information
  help - Display this help message
  exit - Close the connection

mock-router> 
""",
    "exit": "Goodbye!\n"
}

DEFAULT_RESPONSE = """
Unknown command. Type 'help' for a list of available commands.

mock-router> 
"""

class MockSSHServer(paramiko.ServerInterface):
    """SSH server implementation"""
    
    def __init__(self):
        self.event = threading.Event()
        self.command_responses = COMMAND_RESPONSES
        self.default_response = DEFAULT_RESPONSE
        self.username = "test"
        self.password = "Ac0rN$"
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return 0  # OPEN_SUCCEEDED
        return 1  # OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        logger.info(f"Auth attempt: username={username}")
        if username == self.username and password == self.password:
            logger.info("Authentication successful")
            return 0  # AUTH_SUCCESSFUL
        logger.warning(f"Authentication failed for {username}")
        return 2  # AUTH_FAILED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
        
    def check_channel_exec_request(self, channel, command):
        logger.info(f"Exec request: {command}")
        
        # Decode the command
        cmd = command.decode('utf8').strip()
        
        # Get the response for this command
        response = self.command_responses.get(cmd, self.default_response)
        
        # Send response
        channel.send(response.encode('utf-8'))
        channel.send_exit_status(0)
        channel.close()
        return True

def handle_client(client, addr):
    """Handle SSH client connections"""
    
    logger.info(f"Connection from {addr}")
    
    try:
        # Create a transport for this client
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        
        # Set up server interface
        server = MockSSHServer()
        
        try:
            # Start the server
            transport.start_server(server=server)
        except paramiko.SSHException as e:
            logger.error(f"SSH negotiation failed: {str(e)}")
            return
        
        # Wait for authentication
        chan = transport.accept(20)
        if chan is None:
            logger.error("No channel received within timeout")
            return
            
        # Wait for shell request
        server.event.wait(10)
        if not server.event.is_set():
            logger.warning("Client never asked for a shell")
            
        # Send welcome message
        try:
            chan.send(b"Welcome to ACORN Mock SSH Server\r\n")
            chan.send(b"Type 'help' for available commands\r\n")
            chan.send(b"mock-router> ")
            
            # Handle interactive commands
            f = chan.makefile('r')
            while True:
                # Read a command
                command = f.readline().strip('\r\n')
                if not command:
                    # Empty command, just send prompt
                    chan.send(b"mock-router> ")
                    continue
                    
                logger.info(f"Received command: {command}")
                
                # Check for exit command
                if command == "exit":
                    chan.send(b"Goodbye!\r\n")
                    break
                    
                # Get response for this command
                response = COMMAND_RESPONSES.get(command, DEFAULT_RESPONSE)
                
                # Send response
                chan.send(response.encode('utf-8'))
                    
        except Exception as e:
            logger.error(f"Error in SSH session: {str(e)}")
            
        # Close the channel when done
        if chan:
            chan.close()
            
    except Exception as e:
        logger.error(f"Error handling client: {str(e)}")
        
    finally:
        # Make sure the client socket is closed
        try:
            client.close()
        except:
            pass

def start_server(port=2222, bind='0.0.0.0'):
    """Start the mock SSH server"""
    
    try:
        # Create a socket and bind it to the specified port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))
        sock.listen(5)
        
        logger.info(f"Listening for connections on {bind}:{port}...")
        
        # Handle client connections
        while True:
            try:
                client, addr = sock.accept()
                # Set a timeout on the socket
                client.settimeout(30)
                # Start a new thread to handle this client
                threading.Thread(target=handle_client, args=(client, addr)).start()
            except Exception as e:
                logger.error(f"Error accepting client: {str(e)}")
                
    except KeyboardInterrupt:
        logger.info("Server stopping...")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    print("Starting improved SSH server on port 2222...")
    start_server()