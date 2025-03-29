#!/usr/bin/env python3
"""
A simplified, robust SSH client for working with network devices.
This client is specifically designed to work with our mock SSH server.
"""

import paramiko
import socket
import logging
import time
import traceback
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fixed_ssh_client.log',
    filemode='w'
)

logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class FixedSSHClient:
    """A simplified SSH client that works reliably with the mock server"""
    
    def __init__(self, hostname, port=22, username=None, password=None, timeout=10):
        """Initialize the SSH client with connection parameters"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.client = None
        self.channel = None
        
    def connect(self):
        """Connect to the SSH server"""
        logger.info(f"Connecting to {self.hostname}:{self.port} as {self.username}")
        
        # First test basic socket connectivity
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
        
        # Create SSH client
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with basic options that work reliably
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            logger.info("SSH connection established")
            return True
            
        except Exception as e:
            logger.error(f"SSH connection error: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def execute_command(self, command):
        """Execute a command on the server and return the output"""
        if not self.client:
            logger.error("Not connected. Call connect() first.")
            return None
        
        try:
            logger.info(f"Executing command: {command}")
            
            # Use exec_command with a reasonable timeout
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
            
            # Read output with a timeout mechanism
            start_time = time.time()
            output = ""
            error = ""
            
            # Read stdout with timeout
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    output += stdout.channel.recv(1024).decode('utf-8')
                
                if stderr.channel.recv_stderr_ready():
                    error += stderr.channel.recv_stderr(1024).decode('utf-8')
                
                # Check if we've exceeded timeout
                if time.time() - start_time > self.timeout:
                    logger.warning("Command execution timed out")
                    break
                
                time.sleep(0.1)
            
            # Get any remaining output
            if stdout.channel.recv_ready():
                output += stdout.channel.recv(1024).decode('utf-8')
            
            if stderr.channel.recv_stderr_ready():
                error += stderr.channel.recv_stderr(1024).decode('utf-8')
            
            # Get exit status
            exit_status = stdout.channel.recv_exit_status()
            
            logger.info(f"Command completed with exit status: {exit_status}")
            logger.debug(f"Output: {output}")
            
            if error:
                logger.warning(f"Error output: {error}")
            
            return {
                "output": output,
                "error": error,
                "exit_status": exit_status
            }
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "output": "",
                "error": str(e),
                "exit_status": -1
            }
    
    def disconnect(self):
        """Close the SSH connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("SSH connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
                logger.error(traceback.format_exc())
            
            self.client = None


def test_ssh_connection():
    """Test connecting to the mock SSH server"""
    client = FixedSSHClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$",
        timeout=15
    )
    
    if client.connect():
        logger.info("Connection successful, testing command execution")
        
        # Test basic command
        result = client.execute_command("show version")
        if result["exit_status"] == 0:
            logger.info("Command execution successful")
            logger.info(f"Command output:\n{result['output']}")
        else:
            logger.error("Command execution failed")
            logger.error(f"Error: {result['error']}")
        
        # Test more complex command
        result = client.execute_command("show circuit id TEST-001")
        if result["exit_status"] == 0:
            logger.info("Circuit test command execution successful")
            logger.info(f"Command output:\n{result['output']}")
        else:
            logger.error("Circuit test command execution failed")
            logger.error(f"Error: {result['error']}")
        
        # Close connection
        client.disconnect()
        return True
    else:
        logger.error("Connection failed")
        return False


if __name__ == "__main__":
    logger.info("==================================================")
    logger.info("Starting SSH client test with fixed implementation")
    logger.info("==================================================")
    
    success = test_ssh_connection()
    
    if success:
        logger.info("Test completed successfully")
        sys.exit(0)
    else:
        logger.error("Test failed")
        sys.exit(1)