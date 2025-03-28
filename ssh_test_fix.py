#!/usr/bin/env python3
"""
Test script for SSH connection to identify and fix issues
"""

import socket
import paramiko
import sys
import time
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ssh_test_fix.log',
    filemode='w'
)

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

def test_socket(hostname, port):
    """Test basic socket connectivity"""
    print(f"Testing socket connection to {hostname}:{port}")
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Try to connect
        start_time = time.time()
        result = sock.connect_ex((hostname, port))
        elapsed = time.time() - start_time
        
        if result == 0:
            print(f"SUCCESS: Connected to {hostname}:{port} in {elapsed:.2f}s")
            socket_ok = True
        else:
            print(f"FAILURE: Could not connect to {hostname}:{port} (error code: {result})")
            socket_ok = False
            
        sock.close()
        return socket_ok
    except Exception as e:
        print(f"ERROR: Socket test failed - {str(e)}")
        return False

def test_ssh(hostname, port, username, password):
    """Test SSH connection with standard method"""
    print(f"Testing SSH connection to {hostname}:{port}")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect with tolerant settings
        client.connect(
            hostname=hostname,
            port=port,
            username=username, 
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False,
            disabled_algorithms=dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
        )
        
        # Try a simple command
        stdin, stdout, stderr = client.exec_command('show version')
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        print("Command output:")
        print(output)
        if error:
            print("Command error:")
            print(error)
            
        client.close()
        print("SUCCESS: SSH connection and command execution successful")
        return True
    except Exception as e:
        print(f"ERROR: SSH connection failed - {str(e)}")
        return False

def test_transport(hostname, port, username, password):
    """Test SSH connection at transport level"""
    print(f"Testing SSH transport to {hostname}:{port}")
    transport = None
    try:
        # Create a socket first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((hostname, port))
        
        # Create the transport
        transport = paramiko.Transport(sock)
        transport.start_client()
        
        # Try authentication
        transport.auth_password(username, password)
        
        if transport.is_authenticated():
            print("SUCCESS: SSH transport authentication successful")
            
            # Try a command
            channel = transport.open_session()
            channel.exec_command('show version')
            output = channel.recv(1024).decode('utf-8')
            print("Command output:")
            print(output)
            
            channel.close()
            return True
        else:
            print("FAILURE: SSH transport authentication failed")
            return False
            
    except Exception as e:
        print(f"ERROR: Transport test failed - {str(e)}")
        return False
        
    finally:
        if transport:
            transport.close()

def update_hosts_file():
    """Update /etc/hosts file to ensure localhost resolves properly"""
    try:
        # We can't actually modify the host file in this environment
        # This is just a placeholder for documentation
        print("In a real environment, you might need to check if localhost is properly configured")
        print("Example: Adding '127.0.0.1 localhost' to /etc/hosts")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    hostname = "127.0.0.1"
    port = 2222
    username = "test"
    password = "Ac0rN$"
    
    print("=" * 50)
    print("SSH Connection Test and Fix Utility")
    print("=" * 50)
    
    # Step 1: Test socket connection
    print("\nStep 1: Testing basic TCP socket connection")
    socket_ok = test_socket(hostname, port)
    ssh_ok = False
    transport_ok = False
    
    # Step 2: Test SSH connection
    if socket_ok:
        print("\nStep 2: Testing SSH connection")
        ssh_ok = test_ssh(hostname, port, username, password)
    else:
        print("\nSkipping SSH test as socket connection failed")
        
    # Step 3: Test low-level transport if regular SSH failed
    if socket_ok and not ssh_ok:
        print("\nStep 3: Testing SSH transport layer")
        transport_ok = test_transport(hostname, port, username, password)
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Socket Connection: {'SUCCESS' if socket_ok else 'FAILURE'}")
    print(f"SSH Connection: {'SUCCESS' if ssh_ok else 'FAILURE'}")
    if transport_ok:
        print(f"Transport Layer: {'SUCCESS' if transport_ok else 'FAILURE'}")
    
    # Tips based on results
    print("\nRecommendations:")
    if not socket_ok:
        print("- Check if the SSH server is running (run 'ps aux | grep ssh')")
        print("- Ensure port 2222 is not blocked by a firewall")
        print("- Try restarting the SSH server")
    elif not ssh_ok and not transport_ok:
        print("- Check if SSH credentials are correct")
        print("- Review SSH server logs for errors")
        print("- Try connecting with verbose logging (ssh -vvv)")
    elif ssh_ok:
        print("✅ SSH connection is working properly!")
    elif transport_ok:
        print("✅ SSH transport is working, but paramiko needs configuration")
    
    print("=" * 50)