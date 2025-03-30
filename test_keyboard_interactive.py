#!/usr/bin/env python3
"""
Test script to verify keyboard-interactive authentication with the mock SSH server.
"""
import sys
import logging
import time
from utils.ssh_client import SSHClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='keyboard_interactive_test.log',
    filemode='w'
)

# Add console handler
logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

def test_keyboard_interactive_auth():
    """Test connecting to the mock SSH server using keyboard-interactive auth"""
    logger.info("Testing keyboard-interactive authentication to mock SSH server")
    
    # Create SSH client
    client = SSHClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$"
    )
    
    try:
        # Connect to the server
        client.connect()
        logger.info("Connection successful!")
        
        # Test executing a command
        success, output = client.execute_command("show version")
        if success:
            logger.info("Command execution successful")
            logger.info(f"Command output: {output}")
        else:
            logger.error(f"Command execution failed: {output}")
        
        # Test more complex command
        success, output = client.execute_command("show circuit id TEST-001")
        if success:
            logger.info("Circuit command execution successful")
            logger.info(f"Command output: {output}")
        else:
            logger.error(f"Circuit command execution failed: {output}")
        
        # Disconnect
        client.disconnect()
        return True
    except Exception as e:
        logger.error(f"SSH connection test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Starting keyboard-interactive authentication test")
    logger.info("=" * 80)
    
    start_time = time.time()
    success = test_keyboard_interactive_auth()
    elapsed = time.time() - start_time
    
    logger.info("=" * 80)
    logger.info(f"Test {'succeeded' if success else 'failed'} in {elapsed:.2f} seconds")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)