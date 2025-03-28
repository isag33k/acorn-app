import paramiko
import logging

logger = logging.getLogger(__name__)

class SSHClient:
    """Utility class for SSH connections to network equipment"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        """Initialize the SSH client with connection parameters"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None
    
    def connect(self):
        """Establish an SSH connection to the equipment"""
        try:
            self.client = paramiko.SSHClient()
            
            # Add to known hosts automatically
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.debug(f"Connecting to {self.hostname}:{self.port} as {self.username}")
            
            # Connect to the host
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            logger.debug(f"Successfully connected to {self.hostname}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to {self.hostname}: {str(e)}")
            if self.client:
                self.client.close()
                self.client = None
            raise
    
    def execute_command(self, command):
        """Execute a command on the connected equipment"""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            logger.debug(f"Executing command on {self.hostname}: {command}")
            
            # Execute the command
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            
            # Read the output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Command error on {self.hostname}: {error}")
                return f"STDOUT:\n{output}\n\nSTDERR:\n{error}"
            
            return output
            
        except Exception as e:
            logger.error(f"Error executing command on {self.hostname}: {str(e)}")
            raise
    
    def disconnect(self):
        """Close the SSH connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.debug(f"Disconnected from {self.hostname}")
