#!/usr/bin/env python3
"""
Test script for SSH connection to identify and fix issues
"""

import paramiko
import socket
import time
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Print to console
)

# Test connectivity using a socket
def test_socket(hostname, port):
    try:
        print(f"Testing raw socket connection to {hostname}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((hostname, port))
        print("✓ Socket connection successful!")
        sock.close()
        return True
    except Exception as e:
        print(f"✗ Socket connection failed: {str(e)}")
        return False

# Test SSH connectivity using paramiko
def test_ssh(hostname, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Testing SSH connection to {hostname}:{port} as {username}...")
        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        print("✓ SSH connection successful!")
        
        print("\nTesting command execution...")
        stdin, stdout, stderr = client.exec_command('show version')
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if error:
            print(f"✗ Command execution failed: {error}")
        else:
            print("✓ Command execution successful!")
            print(f"Output: {output}")
        
        client.close()
        return True
    except Exception as e:
        print(f"✗ SSH connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False
        
# Utility function to create a transport without client
def test_transport(hostname, port, username, password):
    try:
        print(f"\nTesting direct transport to {hostname}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
        
        # Create transport
        transport = paramiko.Transport(sock)
        transport.start_client()
        
        # Authenticate
        transport.auth_password(username, password)
        
        if transport.is_authenticated():
            print("✓ Transport authentication successful!")
            
            # Try to open a channel and execute a command
            channel = transport.open_session()
            channel.exec_command('show version')
            
            # Get output
            output = channel.recv(4096).decode('utf-8')
            print(f"Output: {output}")
            
            channel.close()
            transport.close()
            return True
        else:
            print("✗ Transport authentication failed")
            transport.close()
            return False
    except Exception as e:
        print(f"✗ Transport connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

# Update host file for localhost aliases
def update_hosts_file():
    print("\nChecking if we need to update /etc/hosts...")
    try:
        # Check if we have write permission
        if not os.access('/etc/hosts', os.W_OK):
            print("✗ Cannot write to /etc/hosts - skipping this step")
            return
            
        with open('/etc/hosts', 'r') as f:
            hosts_content = f.read()
            
        if '127.0.0.1 localhost' not in hosts_content:
            with open('/etc/hosts', 'a') as f:
                f.write('\n127.0.0.1 localhost\n')
            print("✓ Added localhost to /etc/hosts")
        else:
            print("✓ /etc/hosts already has localhost entry")
    except Exception as e:
        print(f"✗ Error updating hosts file: {str(e)}")

if __name__ == "__main__":
    # Configuration
    hostname = "127.0.0.1"
    port = 2222
    username = "test"
    password = "Ac0rN$"
    
    # Run tests
    socket_ok = test_socket(hostname, port)
    if socket_ok:
        ssh_ok = test_ssh(hostname, port, username, password)
        if not ssh_ok:
            # Try transport directly
            transport_ok = test_transport(hostname, port, username, password)
        
    print("\nSummary:")
    print(f"Socket connection: {'✓' if socket_ok else '✗'}")
    print(f"SSH connection: {'✓' if 'ssh_ok' in locals() and ssh_ok else '✗'}")
    
    # Provide potential fixes
    if not socket_ok:
        print("\nPossible fixes for socket issues:")
        print("1. Check if the SSH server is running")
        print("2. Check if the port is correct")
        print("3. Check if there's a firewall blocking the connection")
    
    if socket_ok and not ('ssh_ok' in locals() and ssh_ok):
        print("\nPossible fixes for SSH issues:")
        print("1. Check if the SSH server is properly configured")
        print("2. Check if the username and password are correct")
        print("3. Check if the SSH server supports the SSH protocol version")
        print("4. Try using a transport directly instead of the high-level client")