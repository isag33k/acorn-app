#!/usr/bin/env python3
"""
This is a simplified SSH client for testing password authentication with the mock SSH server.
"""

import paramiko
import logging
import sys
import time
import socket

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='simple_password_client.log',
    filemode='w'
)

logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

def test_ssh_connection():
    """Test SSH connection to the mock server with password authentication"""
    logger.info("Testing SSH connection to mock server")
    
    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect with password authentication
        logger.info("Connecting with password authentication")
        client.connect(
            hostname="127.0.0.1",
            port=2222,
            username="test",
            password="Ac0rN$",
            allow_agent=False,
            look_for_keys=False,
            timeout=10
        )
        
        # Test the connection with a simple command
        logger.info("Connection successful! Testing command execution...")
        stdin, stdout, stderr = client.exec_command("show version")
        
        # Read output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        logger.info(f"Command output: {output}")
        if error:
            logger.error(f"Command error: {error}")
        
        # Test a circuit command
        logger.info("Testing circuit command...")
        stdin, stdout, stderr = client.exec_command("show circuit id TEST-001")
        
        # Read output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        logger.info(f"Circuit command output: {output}")
        if error:
            logger.error(f"Circuit command error: {error}")
        
        # Close connection
        client.close()
        logger.info("Connection closed")
        return True
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if client:
            client.close()
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Starting simple password authentication test")
    logger.info("=" * 80)
    
    start_time = time.time()
    success = test_ssh_connection()
    elapsed = time.time() - start_time
    
    logger.info("=" * 80)
    logger.info(f"Test {'succeeded' if success else 'failed'} in {elapsed:.2f} seconds")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)