#!/usr/bin/env python3
"""
A specialized SSH client for devices that require keyboard-interactive authentication.
"""

import paramiko
import socket
import time
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='keyboard_interactive.log',
    filemode='w'
)

logger = logging.getLogger()
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class KeyboardInteractiveClient:
    """SSH client with special support for keyboard-interactive authentication"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        """Initialize the SSH client with connection parameters"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.transport = None
        self.chan = None
        
    def _keyboard_interactive_handler(self, title, instructions, prompt_list):
        """Handler for keyboard-interactive authentication"""
        logger.info(f"Keyboard Interactive Auth: {title}")
        logger.info(f"Instructions: {instructions}")
        
        # Return password for all prompts
        answers = []
        for prompt, echo in prompt_list:
            logger.info(f"Prompt: {prompt} (echo: {echo})")
            answers.append(self.password)
        
        return answers
        
    def connect(self):
        """Connect to the server using transport directly"""
        logger.info(f"Connecting to {self.hostname}:{self.port} with keyboard-interactive auth")
        
        # First verify socket connection
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.hostname, self.port))
            logger.info("Socket connection successful")
        except Exception as e:
            logger.error(f"Socket connection failed: {str(e)}")
            return False
            
        try:
            # Create transport directly
            self.transport = paramiko.Transport(sock)
            self.transport.start_client()
            
            # Try detecting available auth methods
            available_auth = self.transport.auth_none(self.username)
            logger.info(f"Available authentication methods: {available_auth}")
            
            authenticated = False
            
            # Try password auth first if it's allowed
            if 'password' in available_auth:
                logger.info("Trying password authentication")
                try:
                    self.transport.auth_password(
                        username=self.username,
                        password=self.password
                    )
                    authenticated = self.transport.is_authenticated()
                    if authenticated:
                        logger.info("Password authentication successful")
                except Exception as e:
                    logger.error(f"Password authentication error: {str(e)}")
            
            # If password auth failed or wasn't available, try keyboard-interactive
            if not authenticated and 'keyboard-interactive' in available_auth:
                logger.info("Trying keyboard-interactive authentication")
                try:
                    self.transport.auth_interactive(
                        username=self.username,
                        handler=self._keyboard_interactive_handler
                    )
                    authenticated = self.transport.is_authenticated()
                    if authenticated:
                        logger.info("Keyboard-interactive authentication successful")
                except Exception as e:
                    logger.error(f"Keyboard-interactive authentication error: {str(e)}")
            
            if self.transport.is_authenticated():
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            if self.transport:
                self.transport.close()
                self.transport = None
            return False
    
    def execute_command(self, command):
        """Execute a command on the server"""
        if not self.transport or not self.transport.is_authenticated():
            logger.error("Not connected or not authenticated")
            return {"exit_status": -1, "output": "", "error": "Not connected"}
            
        try:
            logger.info(f"Executing command: {command}")
            self.chan = self.transport.open_session()
            self.chan.settimeout(60)  # 60-second timeout
            self.chan.exec_command(command)
            
            # Read output
            output = ""
            while True:
                data = self.chan.recv(4096)
                if len(data) == 0:
                    break
                output += data.decode('utf-8', errors='replace')
            
            # Read error
            error = ""
            if self.chan.recv_stderr_ready():
                error = self.chan.recv_stderr(4096).decode('utf-8', errors='replace')
                
            # Get exit status
            exit_status = self.chan.recv_exit_status()
            
            logger.info(f"Command completed with status {exit_status}")
            
            return {
                "exit_status": exit_status,
                "output": output,
                "error": error
            }
                
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return {
                "exit_status": -1,
                "output": "",
                "error": str(e)
            }
        finally:
            if self.chan:
                self.chan.close()
                self.chan = None
    
    def disconnect(self):
        """Close the connection"""
        if self.transport:
            try:
                self.transport.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self.transport = None
                
def test_keyboard_interactive():
    """Test the keyboard-interactive client with the mock server"""
    client = KeyboardInteractiveClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$"
    )
    
    if client.connect():
        logger.info("Connection successful!")
        
        # Test a simple command
        result = client.execute_command("show version")
        logger.info(f"Command result: {result}")
        
        # Test a circuit command
        result = client.execute_command("show circuit id TEST-001")
        logger.info(f"Circuit command result: {result}")
        
        # Disconnect
        client.disconnect()
        return True
    else:
        logger.error("Connection failed")
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Testing SSH connection with keyboard-interactive auth")
    logger.info("=" * 80)
    
    success = test_keyboard_interactive()
    
    logger.info("=" * 80)
    logger.info(f"Test {'succeeded' if success else 'failed'}")
    logger.info("=" * 80)
    
    sys.exit(0 if success else 1)