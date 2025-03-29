#!/usr/bin/env python3
"""
Simple SSH Server for testing ACORN application

This is a very basic SSH server that handles connections with minimal complexity
for better reliability in testing environments.
"""

import socket
import threading
import paramiko
import sys
import os
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='simple_ssh_server.log',
    filemode='w'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Host key path
HOST_KEY_PATH = 'mock_ssh_host_key'

# Generate a host key if it doesn't exist
if not os.path.exists(HOST_KEY_PATH):
    logging.info("Generating new host key...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_PATH)
    logging.info(f"Host key written to {HOST_KEY_PATH}")
else:
    logging.info(f"Using existing host key from {HOST_KEY_PATH}")

# Load the host key
host_key = paramiko.RSAKey.from_private_key_file(HOST_KEY_PATH)
logging.info("Host key loaded")

class SimpleSSHServer(paramiko.ServerInterface):
    """Simplified SSH server implementation"""
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return 0  # OPEN_SUCCEEDED
        return 1  # OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username, password):
        # Accept test/Ac0rN$ credentials
        if username == 'test' and password == 'Ac0rN$':
            logging.info(f"Authentication successful for user: {username}")
            return 0  # AUTH_SUCCESSFUL
        logging.warning(f"Authentication failed for user: {username}")
        return 1  # AUTH_FAILED
    
    def check_channel_shell_request(self, channel):
        logging.info("Shell request received")
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        logging.info(f"PTY request received: {term}")
        return True
    
    def check_channel_exec_request(self, channel, command):
        logging.info(f"Exec request received: {command.decode('utf-8')}")
        # Store the command so we can process it in handle_client
        setattr(channel, "_exec_command", command)
        return True

def handle_command(command):
    """Generate a response for a specific command"""
    command_str = command.decode('utf-8').strip() if isinstance(command, bytes) else command.strip()
    logging.info(f"Processing command: {command_str}")
    
    if command_str.startswith("show version"):
        return """
ACORN Mock Router v1.0
Model: Virtual-1000
Serial: VM12345678
Build date: 2025-03-28
Last boot: 2025-03-27 08:00:00
Uptime: 1 day, 4 hours, 45 minutes
"""
    elif command_str.startswith("show interface"):
        return """
Interface ge-0/0/0, Enabled, Physical link is Up
  Description: Uplink to Provider
  MAC address: 00:00:5e:00:53:01
  MTU: 1500 bytes
  Last flapped: 2025-03-27 08:00:00
  Input rate: 5.2 Mbps (3200 pps)
  Output rate: 2.1 Mbps (1500 pps)
"""
    elif command_str.startswith("show circuit id TEST-001"):
        return """
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
    elif command_str.startswith("show circuit id TEST-002"):
        return """
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
    elif command_str.startswith("show circuit id TEST-"):
        circuit_id = command_str.split("TEST-")[1].strip()
        return f"""
Circuit ID: TEST-{circuit_id}
  Status: Unknown
  Type: Ethernet
  Customer: Unknown
  Bandwidth: Unknown
  Last checked: Never
  Notes: This circuit is not fully configured
"""
    else:
        return "Command not recognized. Try 'show version', 'show interface', or 'show circuit id TEST-001'."

def handle_client(client, addr):
    """Handle a client connection"""
    logging.info(f"Connection from {addr}")
    
    try:
        # Set up the transport
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        
        # Start the server
        server = SimpleSSHServer()
        transport.start_server(server=server)
        
        # Accept a channel
        channel = transport.accept(20)
        if channel is None:
            logging.error("No channel established")
            return
        
        # Get session
        session = transport.open_session()
        
        # Handle exec command if provided
        if hasattr(channel, '_exec_command'):
            cmd = getattr(channel, '_exec_command')
            response = handle_command(cmd)
            channel.send(response.encode('utf-8'))
            channel.send_exit_status(0)
            channel.close()
        else:
            # Interactive shell session
            channel.send(b"Welcome to ACORN Mock Router\r\n")
            channel.send(b"mock-router> ")
            
            f = channel.makefile('rU')
            while True:
                command = f.readline().strip('\r\n')
                if not command:
                    continue
                
                response = handle_command(command)
                channel.send(response.encode('utf-8'))
                channel.send(b"mock-router> ")
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
    finally:
        try:
            transport.close()
        except:
            pass
        logging.info(f"Connection from {addr} closed")

def start_server(port=2222, bind='0.0.0.0'):
    """Start the SSH server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind, port))
        sock.listen(100)
        logging.info(f"Listening for connections on {bind}:{port}")
        
        while True:
            client, addr = sock.accept()
            client_thread = threading.Thread(target=handle_client, args=(client, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logging.info("Server shutting down")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    logging.info("Starting Simple SSH Server")
    start_server()