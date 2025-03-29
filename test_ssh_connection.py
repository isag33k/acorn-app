import paramiko
import sys
import time

def ssh_connect(hostname, port, username, password):
    """Connect to SSH server and execute a test command"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {hostname}:{port} with {username}/{password}...")
        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        print("Connection successful!")
        
        # Try to execute a command
        print("\nExecuting 'show version' command...")
        stdin, stdout, stderr = client.exec_command('show version')
        
        # Wait a moment for command to complete
        time.sleep(2)
        
        # Get output
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if error:
            print(f"Command error: {error}")
        else:
            print("Command output:")
            print(output)
            
        # Close the connection
        client.close()
        print("Connection closed.")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    hostname = "127.0.0.1"
    port = 2222
    username = "test"
    password = "Ac0rN$"
    
    success = ssh_connect(hostname, port, username, password)
    sys.exit(0 if success else 1)