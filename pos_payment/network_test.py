# network_test.py
import socket
import subprocess


def test_network(ip, port):
    print(f"🔍 Testing connection to {ip}:{port}")

    # Test 1: Ping the device
    print("\n1. Pinging device...")
    try:
        result = subprocess.run(['ping', '-c', '4', ip],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Ping successful - Device is on network")
        else:
            print("   ❌ Ping failed - Device not reachable")
            print(f"   Debug: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Ping error: {e}")

    # Test 2: Check port
    print(f"\n2. Checking port {port}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result_code = sock.connect_ex((ip, port))
    sock.close()

    if result_code == 0:
        print(f"   ✅ Port {port} is OPEN")
    else:
        print(f"   ❌ Port {port} is CLOSED - Error code: {result_code}")


# Run test
test_network('192.168.1.157', 1362)