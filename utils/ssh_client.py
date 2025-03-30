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
    
    def __init__(self, hostname, port=22, username=None, password=None, key_filename=None):
        """Initialize the SSH client with connection parameters
        
        Args:
            hostname (str): Host IP or hostname to connect to
            port (int, optional): SSH port number. Defaults to 22.
            username (str, optional): SSH username. Defaults to None.
            password (str, optional): SSH password. Defaults to None.
            key_filename (str, optional): Path to private key file. Defaults to None.
        """
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
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
                
                # Set connection parameters
                connect_params = {
                    'hostname': self.hostname,
                    'port': self.port,
                    'username': self.username,
                    'timeout': 60,  # Timeout in seconds for establishing a connection
                    'banner_timeout': 60,  # Timeout for the SSH banner
                    'auth_timeout': 60,  # Timeout for authentication
                }
                
                # Handle authentication methods
                if self.key_filename:
                    # Use key-based authentication if key file is provided
                    logger.info(f"Using key-based authentication with key file: {self.key_filename}")
                    connect_params['key_filename'] = self.key_filename
                    # Still include password as some keys require passphrase
                    if self.password:
                        connect_params['password'] = self.password
                    
                    # When using a key file, we don't need to look for other keys
                    connect_params['allow_agent'] = False
                    connect_params['look_for_keys'] = False
                elif self.password:
                    # Use password authentication if password is provided and no key file
                    logger.info("Using password authentication")
                    connect_params['password'] = self.password
                    connect_params['allow_agent'] = False
                    connect_params['look_for_keys'] = False
                    
                    # Use custom auth_timeout for slow equipment
                    connect_params['auth_timeout'] = 60
                    
                    # Disable certain pubkey algorithms that might not be supported
                    connect_params['disabled_algorithms'] = dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
                    
                    # Set up a custom keyboard-interactive handler for servers that require it
                    def interactive_handler(title, instructions, fields):
                        logger.debug(f"Keyboard-interactive auth request: {title}")
                        if instructions:
                            logger.debug(f"Instructions: {instructions}")
                        
                        responses = []
                        for field in fields:
                            prompt, echo = field
                            logger.debug(f"Prompt: {prompt}, echo: {echo}")
                            # Always return the password for any prompt
                            responses.append(self.password)
                        
                        return responses
                    
                    # Store the handler for use by transport after connection
                    self._interactive_handler = interactive_handler
                    
                    # Special handling for known OLT devices that require keyboard-interactive auth
                    # Check if this is one of the known OLT devices by IP address
                    olt_devices = ['10.160.15.4', '10.160.15.5', '10.160.15.6']
                    if self.hostname in olt_devices:
                        logger.info(f"Detected OLT device {self.hostname}, using specialized authentication approach")
                        
                        # For OLT devices, skip the standard connect and use transport directly
                        # with keyboard-interactive from the beginning
                        self._connect_with_keyboard_interactive()
                        return True
                        
                else:
                    # If no explicit auth method provided, try to use SSH agent or default keys
                    logger.info("No explicit credentials provided, trying SSH agent and default keys")
                    connect_params['allow_agent'] = True
                    connect_params['look_for_keys'] = True
                
                # Connect with our parameters
                self.client.connect(**connect_params)
                
                # Get the transport
                transport = self.client.get_transport()
                if transport:
                    # Set keepalive for long-running connections
                    transport.set_keepalive(15)  # 15 second keepalive (reduced from 30 for more frequent keepalives)
                    
                    # Try keyboard-interactive auth if we have a handler and password auth failed
                    if hasattr(self, '_interactive_handler') and not transport.is_authenticated():
                        logger.info("Trying keyboard-interactive authentication as fallback")
                        try:
                            transport.auth_interactive(
                                username=self.username,
                                handler=self._interactive_handler
                            )
                            if transport.is_authenticated():
                                logger.info("Keyboard-interactive authentication succeeded")
                        except Exception as e:
                            logger.error(f"Keyboard-interactive authentication failed: {str(e)}")
                            # Continue anyway - we'll catch connection failures later if auth didn't work
                
                logger.info(f"Successfully connected to {self.hostname}")
                self.connected = True
                return True
                
            except paramiko.SSHException as e:
                logger.error(f"SSH error on attempt {attempt}: {str(e)}")
                if "Error reading SSH protocol banner" in str(e):
                    logger.error("SSH protocol banner error - possible connectivity issue")
                # Show full stack trace for SSH exceptions
                logger.error(traceback.format_exc())
                
                # For authentication failures with password, try keyboard-interactive as a fallback
                if "Authentication failed" in str(e) and self.password:
                    logger.info(f"Password authentication failed, attempting keyboard-interactive auth...")
                    try:
                        success = self._connect_with_keyboard_interactive()
                        if success:
                            return True
                    except Exception as ki_e:
                        logger.error(f"Keyboard-interactive authentication also failed: {str(ki_e)}")
                
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
        
    def _connect_with_keyboard_interactive(self):
        """Connect using keyboard-interactive authentication directly
        This method is specifically designed for OLT devices that require keyboard-interactive auth
        """
        logger.info(f"Trying direct keyboard-interactive authentication for {self.hostname}")
        
        try:
            # Create a socket to the server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)  # 30-second timeout
            sock.connect((self.hostname, self.port))
            
            # Create transport directly
            transport = paramiko.Transport(sock)
            transport.start_client()
            
            # Function to handle interactive authentication prompts
            def handler(title, instructions, prompt_list):
                logger.debug(f"Interactive auth: {title}, {instructions}")
                responses = []
                for prompt, echo in prompt_list:
                    logger.debug(f"Prompt: {prompt}, echo: {echo}")
                    responses.append(self.password)
                return responses
            
            # Try keyboard-interactive authentication
            transport.auth_interactive(self.username, handler)
            
            if transport.is_authenticated():
                logger.info(f"Keyboard-interactive authentication succeeded for {self.hostname}")
                
                # Create a client and assign the authenticated transport
                self.client = paramiko.SSHClient()
                self.client._transport = transport
                self.connected = True
                
                # Set keepalive
                transport.set_keepalive(15)
                
                return True
            else:
                logger.error(f"Keyboard-interactive authentication failed for {self.hostname}")
                transport.close()
                return False
                
        except Exception as e:
            logger.error(f"Error during keyboard-interactive authentication: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
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
