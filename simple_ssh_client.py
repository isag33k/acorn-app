#!/usr/bin/env python3
"""
Simple SSH client for testing connection to the mock server.
"""

import paramiko
import socket
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='simple_ssh_client.log',
    filemode='w'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def test_socket(hostname, port):
    """Test simple socket connection"""
    try:
        logging.info(f"Testing socket connection to {hostname}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            logging.info(f"Socket connection successful")
            return True
        else:
            logging.error(f"Socket connection failed with code {result}")
            return False
    except Exception as e:
        logging.error(f"Socket error: {str(e)}")
        return False

def run_command(hostname, port, username, password, command):
    """Run a command via SSH and return the output"""
    logging.info(f"Connecting to {hostname}:{port} as {username}")
    logging.info(f"Command: {command}")
    
    # Test socket first
    if not test_socket(hostname, port):
        return False, "Socket connection failed"
    
    # Connect and run command
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with timeout
        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        
        logging.info("SSH connection established")
        
        # Execute command with timeout
        stdin, stdout, stderr = client.exec_command(command, timeout=10)
        
        # Read output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        # Close connection
        client.close()
        
        logging.info("Command executed successfully")
        logging.info(f"Output: {output}")
        
        if error:
            logging.warning(f"Error output: {error}")
        
        return True, output
        
    except Exception as e:
        logging.error(f"SSH error: {str(e)}")
        return False, str(e)

def test_server():
    """Test several commands on the server"""
    hostname = '127.0.0.1'
    port = 2222
    username = 'test'
    password = 'Ac0rN$'
    
    # Test version command
    success, output = run_command(hostname, port, username, password, "show version")
    if success:
        logging.info("Version command test: SUCCESS")
    else:
        logging.error(f"Version command test: FAILED - {output}")
    
    # Test interface command
    success, output = run_command(hostname, port, username, password, "show interface ge-0/0/0")
    if success:
        logging.info("Interface command test: SUCCESS")
    else:
        logging.error(f"Interface command test: FAILED - {output}")
    
    # Test circuit command
    success, output = run_command(hostname, port, username, password, "show circuit id TEST-001")
    if success:
        logging.info("Circuit command test: SUCCESS")
    else:
        logging.error(f"Circuit command test: FAILED - {output}")

if __name__ == "__main__":
    logging.info("Starting SSH client test")
    test_server()