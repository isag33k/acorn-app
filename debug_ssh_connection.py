#!/usr/bin/env python3
"""
Debug specific issues with SSH connection by trying to reproduce them directly.
"""

import paramiko
import socket
import time
import logging
import sys
from flask import Flask, flash
from app import app, db
from models import Equipment, CircuitMapping, User

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ssh_connection_debug.log',
    filemode='w'  # Overwrite the file each time for clean logs
)
logger = logging.getLogger(__name__)

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

class DebugSSHClient:
    """A specialized version of SSHClient for debugging"""
    
    def __init__(self, hostname, port=22, username=None, password=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        
    def connect(self):
        """Connect with paramiko to the SSH server"""
        try:
            # Create a socket connection directly first to debug raw socket issues
            logger.info(f"Testing raw socket to {self.hostname}:{self.port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.hostname, self.port))
            logger.info("Socket connection successful!")
            sock.close()
            
            # Now use paramiko to connect
            logger.info(f"Connecting via paramiko to {self.hostname}:{self.port} as {self.username}...")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try to connect with verbose logging
            self.client.connect(
                hostname=self.hostname, 
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=15,
                allow_agent=False,
                look_for_keys=False,
                banner_timeout=15
            )
            
            logger.info("Paramiko connection successful!")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            if self.client:
                self.client.close()
                self.client = None
            return False
    
    def execute_command(self, command):
        """Execute a command and log the results"""
        if not self.client:
            logger.error("Cannot execute command - not connected")
            return "ERROR: Not connected. Call connect() first."
        
        try:
            logger.info(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=10)
            
            # Get output and error
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                logger.warning(f"Command produced error: {error}")
            
            logger.info(f"Command output: {output}")
            return f"OUTPUT:\n{output}\n\nERROR:\n{error}"
            
        except Exception as e:
            logger.error(f"Command execution error: {str(e)}")
            return f"EXCEPTION: {str(e)}"
    
    def disconnect(self):
        """Close the connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info(f"Disconnected from {self.hostname}")

def simulate_circuit_check(circuit_id):
    """Simulate what happens when checking a circuit"""
    with app.app_context():
        logger.info(f"Looking up circuit ID: {circuit_id}")
        
        # Find any circuit mappings with this ID
        mappings = CircuitMapping.query.filter_by(circuit_id=circuit_id).all()
        
        if not mappings:
            logger.error(f"No mappings found for circuit ID: {circuit_id}")
            return
        
        logger.info(f"Found {len(mappings)} mappings for circuit ID: {circuit_id}")
        
        # Process each mapping
        for mapping in mappings:
            equipment = mapping.equipment
            logger.info(f"Processing equipment: {equipment.name}")
            logger.info(f"IP address: {equipment.ip_address}")
            logger.info(f"SSH port: {equipment.ssh_port}")
            logger.info(f"Username: {equipment.username}")
            logger.info(f"Password: {'*' * len(equipment.password)}")
            
            # Get commands
            commands = mapping.get_commands_list()
            logger.info(f"Commands to execute: {commands}")
            
            # Directly connect and execute
            ssh_client = DebugSSHClient(
                hostname=equipment.ip_address,
                port=equipment.ssh_port,
                username=equipment.username,
                password=equipment.password
            )
            
            if ssh_client.connect():
                for cmd in commands:
                    result = ssh_client.execute_command(cmd)
                    logger.info(f"Result of '{cmd}': {result}")
                
                ssh_client.disconnect()
            else:
                logger.error("Failed to connect to SSH server")

def test_mock_server_direct():
    """Test connecting directly to the mock server"""
    logger.info("=== TESTING DIRECT CONNECTION TO MOCK SERVER ===")
    
    # Connect directly to our mock server with hardcoded credentials
    ssh_client = DebugSSHClient(
        hostname="127.0.0.1",
        port=2222,
        username="test",
        password="Ac0rN$"
    )
    
    if ssh_client.connect():
        # Try a few commands
        for cmd in ["show version", "show circuit id TEST-001", "show interface ge-0/0/0"]:
            result = ssh_client.execute_command(cmd)
            logger.info(f"Result: {result}")
        
        ssh_client.disconnect()
        return True
    else:
        logger.error("Direct connection to mock server failed")
        return False
        
def run_all_tests():
    """Run all tests to debug SSH connection issues"""
    logger.info("Starting SSH connection debugging")
    
    # First test direct connection to mock server
    if test_mock_server_direct():
        # If direct connection works, try simulating circuit checks
        for circuit_id in ["TEST-001", "TEST-002", "TEST-MULTI"]:
            logger.info(f"\n=== SIMULATING CIRCUIT CHECK FOR {circuit_id} ===")
            simulate_circuit_check(circuit_id)
    
    logger.info("Debug completed. Check ssh_connection_debug.log for detailed logs.")
    
if __name__ == "__main__":
    run_all_tests()