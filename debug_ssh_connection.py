#!/usr/bin/env python3
"""
Debug specific issues with SSH connection by trying to reproduce them directly.
"""

import paramiko
import socket
import time
import logging
import sys
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='debug_ssh_connection.log',
    filemode='w'
)

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class DebugSSHClient:
    """A specialized version of SSHClient for debugging"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        """Initialize the SSH client with connection parameters"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        
    def connect(self):
        """Connect with paramiko to the SSH server"""
        logger.info(f"Attempting connection to {self.hostname}:{self.port} as {self.username}")
        
        # Socket connection test
        try:
            logger.debug(f"Testing socket connection to {self.hostname}:{self.port}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.hostname, self.port))
            sock.close()
            
            if result == 0:
                logger.info(f"Socket connection to {self.hostname}:{self.port} successful")
            else:
                logger.error(f"Socket connection to {self.hostname}:{self.port} failed with code {result}")
                return False
        except Exception as e:
            logger.error(f"Socket connection error: {str(e)}")
            return False
            
        # SSH connection
        try:
            # Create client with detailed logging
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Set extra verbose logging for paramiko
            paramiko_logger = logging.getLogger("paramiko")
            paramiko_logger.setLevel(logging.DEBUG)
            
            logger.info("Trying SSH connection...")
            # Do connection with various retry techniques
            max_retries = 3
            retry_count = 0
            last_exception = None
            
            while retry_count < max_retries:
                try:
                    retry_count += 1
                    logger.info(f"Connection attempt {retry_count}/{max_retries}")
                    
                    # Try with different algorithms disabled
                    connection_args = {
                        "hostname": self.hostname,
                        "port": self.port,
                        "username": self.username,
                        "password": self.password,
                        "timeout": 10,
                        "allow_agent": False,
                        "look_for_keys": False,
                        "banner_timeout": 10,
                        "auth_timeout": 10,
                        "disabled_algorithms": {
                            "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"],
                            "kex": [],
                            "cipher": [],
                            "mac": [],
                            "compress": [],
                            "server_host_key": []
                        }
                    }
                    
                    # On higher retry counts, disable more algorithms
                    if retry_count >= 2:
                        connection_args["disabled_algorithms"]["kex"] = ["diffie-hellman-group-exchange-sha1"]
                    
                    self.client.connect(**connection_args)
                    break  # If we get here, the connection was successful
                    
                except paramiko.ssh_exception.SSHException as e:
                    last_exception = e
                    logger.warning(f"SSH Exception on attempt {retry_count}: {str(e)}")
                    time.sleep(1)  # Wait a bit before retrying
                    
                except Exception as e:
                    last_exception = e
                    logger.error(f"Generic error on attempt {retry_count}: {str(e)}")
                    logger.error(traceback.format_exc())
                    time.sleep(1)  # Wait a bit before retrying
            
            # If we exited the loop due to max retries
            if retry_count >= max_retries and last_exception:
                logger.error(f"Failed after {max_retries} attempts. Last error: {str(last_exception)}")
                return False
                
            # If we get here without returning, the connection succeeded
            logger.info("Connection established successfully!")
            
            logger.info("SSH connection successful!")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"SSH connection error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def execute_command(self, command):
        """Execute a command and log the results"""
        if not self.connected or not self.client:
            logger.error("Not connected, cannot execute command")
            return "ERROR: Not connected"
            
        try:
            logger.info(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=10)
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            logger.debug(f"Command output: {output}")
            if error:
                logger.error(f"Command stderr: {error}")
                
            return output or error or "Command executed successfully with no output"
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return f"ERROR: {str(e)}"
    
    def disconnect(self):
        """Close the connection"""
        if self.client:
            logger.info("Disconnecting")
            self.client.close()
            self.connected = False

def simulate_circuit_check(circuit_id):
    """Simulate what happens when checking a circuit"""
    logger.info(f"Simulating circuit check for: {circuit_id}")
    
    # These are the parameters for the mock SSH server
    ssh_client = DebugSSHClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$"
    )
    
    if ssh_client.connect():
        # For TEST-001, use the show version command
        if circuit_id == "TEST-001":
            command = "show version"
        # For TEST-002, use the show interface command
        elif circuit_id == "TEST-002":
            command = "show interface"
        # For others, use a default command
        else:
            command = "show circuit"
            
        result = ssh_client.execute_command(command)
        logger.info(f"Circuit check result: {result}")
        ssh_client.disconnect()
        return result
    else:
        logger.error("Failed to connect to SSH server")
        return "ERROR: Failed to connect to SSH server"

def test_mock_server_direct():
    """Test connecting directly to the mock server"""
    logger.info("Testing direct connection to mock SSH server")
    
    ssh_client = DebugSSHClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$"
    )
    
    if ssh_client.connect():
        # Try a few different commands
        commands = [
            "show version",
            "show interface",
            "show circuit"
        ]
        
        for cmd in commands:
            result = ssh_client.execute_command(cmd)
            logger.info(f"Command '{cmd}' result: {result}")
            
        ssh_client.disconnect()
        return True
    else:
        logger.error("Direct test failed")
        return False

def run_all_tests():
    """Run all tests to debug SSH connection issues"""
    logger.info("=" * 50)
    logger.info("Starting SSH connection debugging")
    logger.info("=" * 50)
    
    # First test - direct connection
    logger.info("\n\nTEST 1: Direct connection to mock SSH server")
    result1 = test_mock_server_direct()
    
    # Second test - simulate circuit check
    logger.info("\n\nTEST 2: Simulated circuit check for TEST-001")
    result2 = simulate_circuit_check("TEST-001")
    
    # Third test - simulate circuit check with different command
    logger.info("\n\nTEST 3: Simulated circuit check for TEST-002")
    result3 = simulate_circuit_check("TEST-002")
    
    logger.info("=" * 50)
    logger.info("SSH debugging complete")
    logger.info(f"Test 1 (Direct connection): {'SUCCESS' if result1 else 'FAILURE'}")
    logger.info(f"Test 2 (Circuit TEST-001): {'SUCCESS' if result2 != 'ERROR: Failed to connect to SSH server' else 'FAILURE'}")
    logger.info(f"Test 3 (Circuit TEST-002): {'SUCCESS' if result3 != 'ERROR: Failed to connect to SSH server' else 'FAILURE'}")
    logger.info("=" * 50)
    
    print("\nDebugging complete. Check debug_ssh_connection.log for details.")

if __name__ == "__main__":
    run_all_tests()