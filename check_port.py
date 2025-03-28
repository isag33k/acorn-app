import socket

def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        print(f"Port {port} is open on {host}")
        s.close()
        return True
    except socket.error:
        print(f"Cannot connect to port {port} on {host}")
        return False

# Check localhost/127.0.0.1
print("Checking localhost (127.0.0.1):")
check_port("127.0.0.1", 2222)

# Check 0.0.0.0
print("\nChecking 0.0.0.0:")
check_port("0.0.0.0", 2222)

# Check the public IP (if available)
print("\nChecking server's hostname:")
try:
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print(f"Server hostname: {hostname}, IP: {ip}")
    check_port(ip, 2222)
except Exception as e:
    print(f"Error getting hostname: {e}")