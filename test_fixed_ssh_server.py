#!/usr/bin/env python3
"""
Test script to verify the fixed SSH server implementation.
"""

import logging
import sys
import time
from utils.ssh_client import SSHClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='test_fixed_ssh_server.log',
    filemode='w'
)

# Add console handler
logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

def test_ssh_connection():
    """Test connecting to the fixed SSH server"""
    logger.info("Testing connection to fixed SSH server")
    
    # Create the client with the test credentials
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
        
        # Test with a simple command
        logger.info("Testing simple command...")
        success, output = client.execute_command("show version")
        logger.info(f"Success: {success}")
        logger.info(f"Output: {output}")
        
        # Test with a circuit command
        logger.info("Testing circuit command...")
        success, output = client.execute_command("show circuit id TEST-001")
        logger.info(f"Success: {success}")
        logger.info(f"Output: {output}")
        
        # Test with a large output command
        logger.info("Testing large output command...")
        success, output = client.execute_command("show run")
        logger.info(f"Success: {success}")
        logger.info(f"Output length: {len(output)} bytes")
        logger.info(f"Output preview: {output[:200]}...")
        
        # Close the connection
        client.disconnect()
        logger.info("Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Starting test of fixed SSH server")
    logger.info("=" * 80)
    
    start_time = time.time()
    success = test_ssh_connection()
    elapsed = time.time() - start_time
    
    logger.info("=" * 80)
    logger.info(f"Test {'succeeded' if success else 'failed'} in {elapsed:.2f} seconds")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)