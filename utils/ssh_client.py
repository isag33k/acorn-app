import paramiko
import logging
import sys
import os
import socket
import time
import traceback

# Configure enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ssh_client.log',
    filemode='a'  # Append to log file instead of overwriting
)

# Add console handler
logger = logging.getLogger(__name__)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

# Add timestamp to log header
logger.info("=" * 80)
logger.info(f"SSH Client Initialized at {time.strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("=" * 80)

# Enable paramiko detailed logging
paramiko_logger = logging.getLogger("paramiko")
paramiko_logger.setLevel(logging.DEBUG)
paramiko_handler = logging.FileHandler('paramiko_debug.log', mode='a')
paramiko_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
paramiko_logger.addHandler(paramiko_handler)

class SSHClient:
    """Improved utility class for SSH connections to network equipment"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        """Initialize the SSH client with connection parameters"""
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self.reconnect_attempts = 5  # increased from 3 to 5 attempts
        self.reconnect_delay = 5  # seconds (increased from 2 to 5 seconds)
    
    def check_socket(self):
        """Check if the SSH port is open before attempting to connect"""
        max_attempts = 3  # Try up to 3 times
        retry_delay = 2   # 2 seconds between attempts
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Testing socket connection to {self.hostname}:{self.port} (attempt {attempt}/{max_attempts})")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(20)  # increased from 10 to 20 seconds for real network equipment
                result = sock.connect_ex((self.hostname, self.port))
                sock.close()
                
                if result == 0:
                    logger.debug(f"Socket connection to {self.hostname}:{self.port} successful")
                    return True
                else:
                    logger.warning(f"Socket connection to {self.hostname}:{self.port} failed with code {result} (attempt {attempt}/{max_attempts})")
                    
                    # If not the last attempt, wait and retry
                    if attempt < max_attempts:
                        logger.debug(f"Retrying socket connection in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Socket connection to {self.hostname}:{self.port} failed after {max_attempts} attempts")
                        return False
            except Exception as e:
                logger.error(f"Socket test error on attempt {attempt}: {str(e)}")
                
                # If not the last attempt, wait and retry
                if attempt < max_attempts:
                    logger.debug(f"Retrying socket connection in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return False
        
        return False  # Should never reach here, but added as a safeguard
    
    def connect(self):
        """Establish an SSH connection to the equipment with retry mechanism"""
        if self.connected and self.client:
            logger.debug("Already connected")
            return True
            
        # Check socket connection first
        if not self.check_socket():
            raise ConnectionError(f"Cannot connect to {self.hostname} on port {self.port} - port is closed or unreachable")
        
        # Try to connect with retries
        for attempt in range(1, self.reconnect_attempts + 1):
            try:
                logger.debug(f"Connection attempt {attempt} to {self.hostname}:{self.port} as {self.username}")
                
                # Create a new client for each attempt
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Use verbose transport logging for debug purposes
                # Only enable on debug builds
                if logger.level == logging.DEBUG:
                    paramiko_logger = logging.getLogger("paramiko")
                    paramiko_logger.setLevel(logging.DEBUG)
                
                # Connect with more generous timeouts for real network equipment
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30,  # increased from 15 to 30 seconds
                    allow_agent=False,
                    look_for_keys=False,
                    banner_timeout=30,  # increased from 15 to 30 seconds
                    auth_timeout=30,  # increased from 15 to 30 seconds
                    # Removed disabled_algorithms as it may be preventing connections
                )
                
                # Test the connection with a simple command
                transport = self.client.get_transport()
                if transport:
                    transport.set_keepalive(15)  # 15 second keepalive (reduced from 30 for more frequent keepalives)
                
                logger.info(f"Successfully connected to {self.hostname}")
                self.connected = True
                return True
                
            except paramiko.SSHException as e:
                logger.error(f"SSH error on attempt {attempt}: {str(e)}")
                if "Error reading SSH protocol banner" in str(e):
                    logger.error("SSH protocol banner error - possible connectivity issue")
                # Show full stack trace for SSH exceptions
                logger.error(traceback.format_exc())
                
            except socket.error as e:
                logger.error(f"Socket error on attempt {attempt}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Connection error on attempt {attempt}: {str(e)}")
                logger.error(traceback.format_exc())
            
            # Clean up failed attempt
            if self.client:
                self.client.close()
                self.client = None
            
            # Retry after delay if not the last attempt
            if attempt < self.reconnect_attempts:
                logger.info(f"Retrying in {self.reconnect_delay} seconds...")
                time.sleep(self.reconnect_delay)
        
        # If we get here, all attempts failed
        raise ConnectionError(f"Failed to connect to {self.hostname} on port {self.port} after {self.reconnect_attempts} attempts. Please check network connectivity and SSH server availability.")
    
    def execute_command(self, command):
        """Execute a command on the connected equipment with timeout handling
        
        Returns:
            tuple: (success, output) where success is a boolean and output is the command output
        """
        if not self.connected or not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        
        try:
            logger.debug(f"Executing command on {self.hostname}: {command}")
            
            # Execute with 60-second timeout for real network equipment
            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)
            
            # Read the output with timeout tracking and chunking for large outputs
            start_time = time.time()
            
            # Use chunked reading approach for very large outputs
            buffer_size = 32768  # 32KB chunks for faster reading
            stdout_chunks = []
            stderr_chunks = []
            chunk_count = 0
            
            # Set the channel timeout to 60 seconds for real network equipment
            stdout.channel.settimeout(60)  # 60-second timeout for channel operations
            
            # Read stdout in chunks
            while not stdout.channel.exit_status_ready() or stdout.channel.recv_ready():
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(buffer_size)
                    if not chunk:
                        break
                    stdout_chunks.append(chunk.decode('utf-8', errors='replace'))
                    chunk_count += 1
                else:
                    time.sleep(0.1)  # Small sleep to prevent CPU spinning
                    
                # Safety check - abort if taking too long (60 seconds max for real network equipment)
                if time.time() - start_time > 60:
                    logger.warning(f"Command execution taking too long (>60 sec), forcing completion: {command}")
                    break
            
            # Read stderr if available
            while stderr.channel.recv_stderr_ready():
                chunk = stderr.channel.recv_stderr(buffer_size)
                if not chunk:
                    break
                stderr_chunks.append(chunk.decode('utf-8', errors='replace'))
            
            # Join all the chunks
            stdout_data = ''.join(stdout_chunks)
            stderr_data = ''.join(stderr_chunks)
            
            elapsed = time.time() - start_time
            
            # Get exit status if available
            exit_status = stdout.channel.recv_exit_status() if stdout.channel.exit_status_ready() else -1
            
            logger.debug(f"Command completed in {elapsed:.2f}s with status {exit_status}")
            logger.debug(f"Output size: {len(stdout_data)} bytes in {chunk_count} chunks")
            
            if stderr_data:
                logger.warning(f"Command error on {self.hostname}: {stderr_data}")
            
            # Return success=True and formatted output
            if stderr_data:
                return (True, f"OUTPUT:\n{stdout_data}\n\nERROR:\n{stderr_data}")
            else:
                return (True, stdout_data)
                
        except socket.timeout:
            logger.error(f"Command timed out after timeout period: {command}")
            return (False, "ERROR: Command execution timed out. The device may be busy or the command produces too much output.")
            
        except paramiko.SSHException as e:
            logger.error(f"SSH error during command execution: {str(e)}")
            # Connection may be broken, mark as disconnected
            self.connected = False
            return (False, f"SSH ERROR: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            logger.error(traceback.format_exc())
            return (False, f"ERROR: {str(e)}")
    
    def disconnect(self):
        """Close the SSH connection"""
        if self.client:
            try:
                self.client.close()
                logger.debug(f"Disconnected from {self.hostname}")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")
            finally:
                self.client = None
                self.connected = False
