#!/usr/bin/env python3
"""
Fixed SSH Server for ACORN Application Testing

This is an improved version of the SSH server that correctly handles
exec requests with proper channel management.
"""

import socket
import threading
import paramiko
import sys
import os
import logging
import time
import select

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='fixed_ssh_server.log',
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
logging.info("Host key loaded successfully")

class FixedSSHServer(paramiko.ServerInterface):
    """Improved SSH server implementation with better channel handling"""
    
    def __init__(self):
        self.event = threading.Event()
        self.commands = {}
        self.channels = {}
    
    def check_channel_request(self, kind, chanid):
        logging.info(f"Channel request: {kind}, {chanid}")
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
        self.event.set()
        return True
    
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        logging.info(f"PTY request received: {term}")
        return True
    
    def check_channel_exec_request(self, channel, command):
        """Handle exec requests properly"""
        command_str = command.decode('utf-8')
        logging.info(f"Exec request received: {command_str}")
        
        # Store the command for this channel
        self.commands[channel] = command
        
        # Signal that we're ready to process the command
        self.event.set()
        return True

def handle_command(command):
    """Generate a response for a specific command"""
    command_str = command.decode('utf-8').strip() if isinstance(command, bytes) else command.strip()
    logging.info(f"Processing command: {command_str}")
    
    # Simulate OLT-like processing delays for different commands
    if any(keyword in command_str for keyword in ["show run", "show configuration", "show tech-support"]):
        logging.info("Processing very long-running OLT command - adding significant delay")
        # Simulate real OLT behavior with a much longer delay
        time.sleep(3)  # reduced from 15 to 3 seconds for testing
    elif any(keyword in command_str for keyword in ["show pon", "show olt", "show ont"]):
        logging.info("Processing OLT-specific command with medium delay")
        time.sleep(2)  # reduced from 8 to 2 seconds for testing
    elif "circuit id" in command_str:
        # Add variable delay based on circuit ID for more realistic simulation
        circuit_id = command_str.split("TEST-")[1].strip() if "TEST-" in command_str else "unknown"
        try:
            # Use circuit number to vary the delay - higher numbers have longer delays
            circuit_num = int(circuit_id) if circuit_id.isdigit() else 1
            delay = min(3, 1 + (circuit_num % 3))  # Between 1-3 seconds (reduced for testing)
            logging.info(f"Processing circuit command with variable delay: {delay}s")
            time.sleep(delay)
        except (ValueError, IndexError):
            # Default delay if parsing fails
            logging.info("Processing circuit command with default delay")
            time.sleep(1)
    
    if command_str.startswith("show version"):
        return """
ACORN Mock Router v1.0
Model: Virtual-1000
Serial: VM12345678
Build date: 2025-03-28
Last boot: 2025-03-30 08:00:00
Uptime: 1 day, 6 hours, 37 minutes
"""
    elif command_str.startswith("show interface"):
        return """
Interface ge-0/0/0, Enabled, Physical link is Up
  Description: Uplink to Provider
  MAC address: 00:00:5e:00:53:01
  MTU: 1500 bytes
  Last flapped: 2025-03-30 08:00:00
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
  Last checked: 2025-03-30 14:30:00
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
  Last checked: 2025-03-30 14:30:00
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
        # Generate a large configuration output to test chunked output handling
        output = "! ACORN Mock Router Configuration\n"
        output += "! Generated on 2025-03-30\n"
        output += "!\n"
        output += "hostname mock-router\n"
        output += "!\n"
        
        # Add a lot of interface configurations to make the output large
        for i in range(1, 21):  # 20 interfaces (reduced from 100 for testing)
            output += f"!\n"
            output += f"interface GigabitEthernet0/{i}\n"
            output += f" description Test Interface {i}\n"
            output += f" ip address 10.0.{i//256}.{i%256} 255.255.255.0\n"
            output += f" no shutdown\n"
        
        # Add some routing configurations
        output += "!\n! Routing Configuration\n!\n"
        for i in range(1, 21):  # 20 routes (reduced from 100 for testing)
            output += f"ip route 192.168.{i}.0 255.255.255.0 10.0.0.1\n"
        
        # End configuration
        output += "!\n! End of configuration\n"
        
        return output
    
    else:
        return "Command not recognized. Try 'show version', 'show interface', 'show run', or 'show circuit id TEST-001'."

def handle_client(client, addr):
    """Handle a client connection with proper channel management"""
    logging.info(f"Connection from {addr}")
    
    # Initialize transport to None to ensure it's defined for finally block
    transport = None
    
    try:
        # Set up the transport
        transport = paramiko.Transport(client)
        transport.set_gss_host(socket.getfqdn(""))
        transport.load_server_moduli()
        transport.add_server_key(host_key)
        
        # Start the server
        server = FixedSSHServer()
        transport.start_server(server=server)
        
        # Wait for authentication
        chan = transport.accept(20)
        if chan is None:
            logging.warning("No channel established after 20 seconds")
            return
        
        logging.info("Client authenticated and channel established")
        
        # Wait for a request (shell or exec)
        server.event.wait(10)
        if not server.event.is_set():
            logging.warning("No request received after 10 seconds")
            return
        
        # Check if this is an exec request
        if chan in server.commands:
            command = server.commands[chan]
            logging.info(f"Processing exec request: {command}")
            
            # Generate response
            response = handle_command(command)
            
            # Is this a large response that should be chunked?
            if len(response) > 4096:
                # Send in chunks to simulate real device behavior
                logging.info(f"Sending large response ({len(response)} bytes) in chunks")
                chunk_size = 1024  # 1KB chunks
                chunks = [response[i:i+chunk_size] for i in range(0, len(response), chunk_size)]
                
                for i, chunk in enumerate(chunks):
                    # Send the chunk
                    chunk_bytes = chunk.encode('utf-8')
                    chan.send(chunk_bytes)
                    
                    # Add a small delay between chunks
                    if i < len(chunks) - 1:
                        time.sleep(0.05)  # 50ms delay
            else:
                # Send the entire response at once
                chan.send(response.encode('utf-8'))
            
            # Send exit status and close the channel
            chan.send_exit_status(0)
            chan.close()
        else:
            # Assume this is a shell request
            logging.info("Processing shell request")
            
            # Send welcome message
            chan.send(b"Welcome to ACORN Mock SSH Server\r\n")
            chan.send(b"Type 'exit' to disconnect\r\n")
            chan.send(b"mock-router> ")
            
            # Interactive shell mode
            buf = ''
            while True:
                r, w, e = select.select([chan], [], [], 1)
                if chan in r:
                    data = chan.recv(1024)
                    if not data:
                        break
                    
                    buf += data.decode('utf-8')
                    if '\n' in buf or '\r' in buf:
                        # Extract command
                        lines = buf.splitlines()
                        command = lines[0].strip()
                        buf = '\r\n'.join(lines[1:]) if len(lines) > 1 else ''
                        
                        if command.lower() == 'exit':
                            chan.send(b"Goodbye!\r\n")
                            break
                        
                        # Process command
                        response = handle_command(command)
                        chan.send(response.encode('utf-8'))
                        chan.send(b"\r\nmock-router> ")
    
    except Exception as e:
        logging.error(f"Error in client handler: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
    finally:
        # Clean up
        if transport:
            try:
                transport.close()
            except Exception as e:
                logging.error(f"Error closing transport: {str(e)}")
        
        logging.info(f"Connection from {addr} closed")

def start_server(port=2223, bind='0.0.0.0'):
    """Start the SSH server"""
    # Initialize sock to None to ensure it's defined for finally block
    sock = None
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind((bind, port))
        except Exception as e:
            logging.error(f"Socket bind failed: {str(e)}")
            raise
            
        sock.listen(100)
        logging.info(f"Listening for connections on {bind}:{port}")
        
        while True:
            client, addr = sock.accept()
            logging.info(f"New connection from {addr}")
            
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logging.info("Server stopping on keyboard interrupt")
    except Exception as e:
        logging.error(f"Server error: {str(e)}")
        raise
    finally:
        if sock:
            try:
                sock.close()
                logging.info("Server socket closed")
            except Exception as e:
                logging.error(f"Error closing socket: {str(e)}")

if __name__ == "__main__":
    print("=" * 80)
    print("ACORN Fixed SSH Server")
    print("=" * 80)
    print("Starting SSH server on port 2223...")
    
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nSSH server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        sys.exit(1)