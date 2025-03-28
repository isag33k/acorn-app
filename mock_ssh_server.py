#!/usr/bin/env python3
"""
Mock SSH Server for testing ACORN application

This script creates a simple SSH server that responds to commands
with predefined outputs to simulate network equipment.
"""

import socket
import threading
import paramiko
import sys
import traceback
import os
import logging
from binascii import hexlify

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mock_ssh_server.log',
    filemode='a'
)

# SSH server host key
host_key = paramiko.RSAKey.generate(2048)
print(f"Server key fingerprint: {hexlify(host_key.get_fingerprint())}")

class Server(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()
        # Define command responses based on input
        self.command_responses = {
            "show interface ge-0/0/0": """
Physical interface: ge-0/0/0, Enabled, Physical link is Up
  Interface index: 149, SNMP ifIndex: 526
  Link-level type: Ethernet, MTU: 1514, MRU: 1522, LAN-PHY mode, Speed: 1000mbps, 
  BPDU Error: None, Loop Detect PDU Error: None, MAC-REWRITE Error: None, Loopback: Disabled, 
  Source filtering: Disabled, Flow control: Enabled, Auto-negotiation: Enabled, Remote fault: Online
  Input rate     : 487944 bps (617 pps)
  Output rate    : 3358392 bps (738 pps)

  Active alarms  : None
  Active defects : None
  Interface transmit statistics: Disabled
""",
            "show circuit id TEST-001": """
Circuit ID: TEST-001
Status: Active
Type: Fiber
Speed: 10 Gbps
Customer: ACME Corp
Last updated: 2023-03-15

No errors detected
""",
            "show service TEST-002": """
Service ID: TEST-002
Customer: XYZ Industries
Status: Active
Bandwidth: 100 Mbps
SLA: Premium (99.999%)
""",
            "show interface xe-0/1/0": """
Physical interface: xe-0/1/0, Enabled, Physical link is Up
  Interface index: 175, SNMP ifIndex: 552
  Link-level type: Ethernet, MTU: 1514, MRU: 1522, LAN-PHY mode, Speed: 10Gbps, 
  BPDU Error: None, Loop Detect PDU Error: None, MAC-REWRITE Error: None, Loopback: Disabled, 
  Source filtering: Disabled, Flow control: Enabled, Auto-negotiation: Enabled, Remote fault: Online
  Input rate     : 1487944 bps (1617 pps)
  Output rate    : 13358392 bps (1738 pps)

  Active alarms  : None
  Active defects : None
  Interface transmit statistics: Disabled
""",
            "show version": """
ACORN Mock Router v1.0
Model: Virtual-1000
Serial: VM12345678
Build date: 2025-03-28
Last boot: 2025-03-27 08:00:00
Uptime: 1 day, 4 hours, 45 minutes
"""
        }
        
        # Default response for unknown commands
        self.default_response = "Command not recognized. Try 'show version', 'show interface ge-0/0/0', or 'show circuit id TEST-001'."

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return 0  # OPEN_SUCCEEDED
        return 1  # OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Accept only test/Ac0rN$ credentials
        if (username == 'test' and password == 'Ac0rN$'):
            return 0  # AUTH_SUCCESSFUL
        return 1  # AUTH_FAILED

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        # This is where we handle command execution
        print(f"Command received: {command}")
        
        # Clean the command string
        command = command.decode('utf-8').strip()
        
        # Look for matching command and send response
        response = self.command_responses.get(command, self.default_response)
        
        channel.send(response.encode('utf-8'))
        channel.send(b'\r\n')
        channel.send(b'mock-router> ')
        channel.shutdown(2)  # close the channel
        return True

def handle_connection(client, addr):
    print(f'Connection from {addr}')
    transport = None
    
    try:
        transport = paramiko.Transport(client)
        transport.add_server_key(host_key)
        server = Server()
        
        transport.start_server(server=server)
        
        # Wait for auth
        channel = transport.accept(20)
        if channel is None:
            print('*** No channel!')
            return
        
        server.event.wait(10)
        
        # Send a welcome message
        channel.send(b'Welcome to ACORN Mock SSH Server\r\n')
        channel.send(b'mock-router> ')
        
        # Start interactive shell
        f = channel.makefile('rU')
        while True:
            command = f.readline().strip('\r\n')
            if not command:
                continue
                
            print(f"Command received: {command}")
            
            # Look for matching command and send response
            response = server.command_responses.get(command, server.default_response)
            channel.send(response.encode('utf-8'))
            channel.send(b'\r\n')
            channel.send(b'mock-router> ')
            
            # Check if client wants to exit
            if command == 'exit':
                break
        
    except Exception as e:
        print(f'*** Caught exception: {e.__class__.__name__}: {e}')
        traceback.print_exc()
    finally:
        if transport is not None:
            try:
                transport.close()
            except Exception:
                pass

def start_server(port=2222, bind='0.0.0.0'):
    """Start the mock SSH server"""
    # Create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to port
    try:
        sock.bind((bind, port))
    except Exception as e:
        print(f'*** Bind failed: {e}')
        traceback.print_exc()
        sys.exit(1)
    
    # Start listening
    try:
        sock.listen(100)
        print(f'Listening for connections on {bind}:{port}...')
        
        # Accept client connections
        while True:
            client, addr = sock.accept()
            thread = threading.Thread(target=handle_connection, args=(client, addr))
            thread.daemon = True
            thread.start()
            
    except KeyboardInterrupt:
        print('Server shutting down...')
        sock.close()
    except Exception as e:
        print(f'*** Listen/accept failed: {e}')
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    start_server()