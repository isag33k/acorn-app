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
    
    # Simulate processing delay for long-running commands
    if any(keyword in command_str for keyword in ["show run", "show configuration", "show tech-support"]):
        logging.info("Processing long-running command - adding delay")
        time.sleep(5)  # Simulate longer processing time
    
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
    elif command_str.startswith("show run") or command_str.startswith("show configuration"):
        # Generate a very large configuration output to test timeout handling
        output = "! ACORN Mock Router Configuration\n"
        output += "! Generated on 2025-03-28\n"
        output += "!\n"
        output += "hostname mock-router\n"
        output += "!\n"
        
        # Add a lot of interface configurations to make the output large
        for i in range(1, 101):  # 100 interfaces
            output += f"!\n"
            output += f"interface GigabitEthernet0/{i}\n"
            output += f" description Test Interface {i}\n"
            output += f" ip address 10.0.{i//256}.{i%256} 255.255.255.0\n"
            output += f" no shutdown\n"
        
        # Add a lot of routing configurations
        output += "!\n! Routing Configuration\n!\n"
        for i in range(1, 101):  # 100 routes
            output += f"ip route 192.168.{i}.0 255.255.255.0 10.0.0.1\n"
        
        # Add more configuration sections
        output += "!\n! Access Control Lists\n!\n"
        for i in range(1, 21):  # 20 ACLs
            output += f"ip access-list extended ACL-{i}\n"
            for j in range(1, 11):  # 10 rules per ACL
                output += f" permit ip host 10.1.{i}.{j} any\n"
        
        # SNMP configuration
        output += "!\n! SNMP Configuration\n!\n"
        output += "snmp-server community public RO\n"
        output += "snmp-server community private RW\n"
        output += "snmp-server location ACORN Test Lab\n"
        output += "snmp-server contact admin@acorn.example.com\n"
        
        # User configuration
        output += "!\n! User Configuration\n!\n"
        output += "username admin privilege 15 secret AdminP@ss123\n"
        output += "username operator privilege 10 secret OperP@ss456\n"
        
        # Add circuit configurations
        output += "!\n! Circuit Configuration\n!\n"
        for i in range(1, 21):  # 20 circuits
            output += f"circuit TEST-{i:03d}\n"
            output += f" description Customer Circuit {i}\n"
            output += f" bandwidth 100M\n"
            output += f" interface GigabitEthernet0/{i}\n"
            output += f" service-level gold\n"
        
        # End configuration
        output += "!\n! End of configuration\n"
        
        # Return the very large configuration (should trigger timeout handling if not properly configured)
        return output
    
    else:
        return "Command not recognized. Try 'show version', 'show interface', 'show run', or 'show circuit id TEST-001'."

def handle_client(client, addr):
    """Handle a client connection"""
    logging.info(f"Connection from {addr}")
    
    # Initialize transport to None to ensure it's defined for finally block
    transport = None
    
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
        logging.error(f"Error in client handler: {str(e)}")
    finally:
        # Clean up transport
        if transport:
            try:
                transport.close()
            except Exception as e:
                logging.error(f"Error closing transport: {str(e)}")
        
        logging.info(f"Connection from {addr} closed")

def start_server(port=2222, bind='0.0.0.0'):
    """Start the SSH server"""
    # Initialize socket to None to ensure it's defined for finally block
    sock = None
    
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
        logging.error(f"Error in server: {str(e)}")
    finally:
        # Clean up socket
        if sock:
            try:
                sock.close()
                logging.info("Server socket closed")
            except Exception as e:
                logging.error(f"Error closing socket: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting Simple SSH Server")
    start_server()