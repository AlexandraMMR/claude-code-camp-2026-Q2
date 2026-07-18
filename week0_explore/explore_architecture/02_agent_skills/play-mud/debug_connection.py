#!/usr/bin/env python3
"""
Debug script to troubleshoot MUD connection issues.
"""

import telnetlib
import time
import sys

def debug_connection(host='localhost', port=4000, username='dummy', password='helloworld'):
    """Debug the telnet connection step by step."""
    
    print(f"Attempting to connect to {host}:{port}")
    print("=" * 60)
    
    try:
        # Connect with verbose output
        print("1. Creating Telnet connection...")
        tn = telnetlib.Telnet(host, port, timeout=10)
        print("   ✓ Connection established")
        
        # Wait a bit for initial banner
        print("\n2. Waiting for initial response (2 seconds)...")
        time.sleep(2)
        
        # Try to read whatever is available
        try:
            initial_data = tn.read_very_eager()
            if initial_data:
                print(f"   Initial data received: {repr(initial_data[:200])}")
                print(f"   As text: {initial_data.decode('utf-8', errors='ignore')[:200]}")
            else:
                print("   No initial data received")
        except Exception as e:
            print(f"   Error reading initial data: {e}")
        
        # Try sending username
        print(f"\n3. Sending username: '{username}'")
        tn.write(f"{username}\r\n".encode())
        time.sleep(1)
        
        # Read response
        try:
            username_response = tn.read_very_eager()
            if username_response:
                print(f"   Response after username: {repr(username_response[:200])}")
                print(f"   As text: {username_response.decode('utf-8', errors='ignore')[:200]}")
            else:
                print("   No response after username")
        except Exception as e:
            print(f"   Error reading username response: {e}")
        
        # Check if password prompt appears
        if username_response and (b'password' in username_response.lower() or b'word' in username_response.lower()):
            print(f"\n4. Password prompt detected, sending password: '{password}'")
            tn.write(f"{password}\r\n".encode())
        else:
            print("\n4. No password prompt detected, trying name-only authentication")
            print("   (This might be what's expected based on the hint)")
        
        time.sleep(1)
        
        # Read final response
        print("\n5. Reading final response...")
        try:
            final_response = tn.read_very_eager()
            if final_response:
                print(f"   Final response: {repr(final_response[:300])}")
                print(f"   As text:\n{final_response.decode('utf-8', errors='ignore')}")
            else:
                print("   No final response")
                
                # Try waiting longer
                print("   Waiting 3 more seconds...")
                time.sleep(3)
                final_response = tn.read_very_eager()
                if final_response:
                    print(f"   After waiting: {repr(final_response[:300])}")
                    print(f"   As text:\n{final_response.decode('utf-8', errors='ignore')}")
                else:
                    print("   Still no response after waiting")
        except Exception as e:
            print(f"   Error reading final response: {e}")
        
        # Try sending a simple command
        print("\n6. Testing with 'look' command...")
        tn.write(b"look\r\n")
        time.sleep(1)
        
        try:
            look_response = tn.read_very_eager()
            if look_response:
                print(f"   Look response: {repr(look_response[:300])}")
                print(f"   As text:\n{look_response.decode('utf-8', errors='ignore')}")
            else:
                print("   No response to 'look' command")
        except Exception as e:
            print(f"   Error reading look response: {e}")
        
        tn.close()
        print("\n" + "=" * 60)
        print("Debug complete")
        
    except ConnectionRefusedError:
        print("✗ Connection refused. Is the MUD server running?")
        print(f"  Run: cd week0_explore/infrastructure && docker compose up --build")
    except Exception as e:
        print(f"✗ Connection error: {e}")
        import traceback
        traceback.print_exc()

def manual_telnet_test():
    """Even simpler test - just show what raw telnet sees."""
    print("Manual Telnet Test")
    print("=" * 60)
    print("\nYou can manually test with:")
    print("1. Open PowerShell or Command Prompt")
    print("2. Run: telnet localhost 4000")
    print("3. Type 'dummy' and press Enter")
    print("4. If prompted for password, type 'helloworld'")
    print("5. Type 'look' to see if you're connected")
    print("\nIf this works but our script doesn't, we need to see")
    print("exactly what the server sends after each step.")

if __name__ == "__main__":
    print("MUD Connection Debug Tool")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'manual':
        manual_telnet_test()
    else:
        debug_connection()
    
    print("\n" + "=" * 60)
    print("Based on the hint 'the name is entered as the password',")
    print("it's possible that CircleMUD uses the character name as")
    print("the password for simplicity in this setup.")
    print("\nIf the debug shows no password prompt, try modifying")
    print("the config to use username as password.")