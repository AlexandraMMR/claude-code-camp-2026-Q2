#!/usr/bin/env python3
"""
MUD Client for CircleMUD Interaction

Connects to a local CircleMUD server via Telnet and provides various
subcommands for gameplay automation.
"""

import argparse
import json
import os
import sys
import time
import telnetlib
from pathlib import Path
from typing import List, Optional, Dict, Any


class MUDClient:
    """Client for interacting with CircleMUD server via Telnet."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize client with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
        self.tn = None
    
    def is_connected(self) -> bool:
        """Check if client is connected to MUD."""
        return self.tn is not None
        
    def _load_config(self) -> Dict[str, Any]:
        """Load connection configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Config file not found at {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERROR: Invalid JSON in {self.config_path}")
            sys.exit(1)
    
    def connect(self, max_retries: int = 3, debug: bool = False) -> str:
        """
        Connect to MUD server and auto-login.
        
        Args:
            max_retries: Maximum connection retry attempts
            debug: Enable debug output
            
        Returns:
            Initial server response after login
        """
        host = self.config.get('host', 'localhost')
        port = self.config.get('port', 4000)
        character = self.config.get('character', 'dummy')
        password = self.config.get('password', 'helloworld')
        
        for attempt in range(max_retries):
            try:
                print(f"Connecting to {host}:{port} (attempt {attempt + 1}/{max_retries})...")
                self.tn = telnetlib.Telnet(host, port, timeout=10)
                
                # Read until the name prompt
                if debug:
                    print("Waiting for name prompt...")
                
                # Try to read the initial banner and name prompt
                # CircleMUD typically asks "By what name do you wish to be known?"
                response = ""
                try:
                    # Read until the name prompt
                    banner = self.tn.read_until(b"By what name do you wish to be known?", timeout=5)
                    response += banner.decode('utf-8', errors='ignore')
                    if debug:
                        print(f"Got name prompt: {repr(banner[-50:])}")
                except EOFError:
                    if debug:
                        print("Connection closed by server")
                    return response + "[CONNECTION CLOSED]"
                except Exception as e:
                    if debug:
                        print(f"Error reading name prompt: {e}")
                    # Try alternative prompt detection
                    pass
                
                # Send character name
                if debug:
                    print(f"Sending character name: '{character}'")
                self.tn.write(f"{character}\r\n".encode())
                
                # Now check if we get a password prompt
                time.sleep(0.5)
                try:
                    # Look for password prompt
                    pass_prompt = self.tn.read_until(b"Password:", timeout=3)
                    response += pass_prompt.decode('utf-8', errors='ignore')
                    
                    if debug:
                        print("Password prompt detected")
                    
                    # Send password
                    if debug:
                        print(f"Sending password: '{password}'")
                    self.tn.write(f"{password}\r\n".encode())
                    
                except Exception:
                    # No password prompt found - might be using name as password
                    if debug:
                        print("No password prompt, trying name-only auth")
                    # Some MUDs use the name as password automatically
                    # or don't require password for existing characters
                    pass
                
                # Read the login response and initial game state
                time.sleep(1)
                try:
                    login_response = self.tn.read_very_eager()
                    if login_response:
                        response += login_response.decode('utf-8', errors='ignore')
                        if debug:
                            print(f"Login response: {repr(login_response[:100])}")
                except Exception as e:
                    if debug:
                        print(f"Error reading login response: {e}")
                
                # Check for "PRESS RETURN" prompt
                if "PRESS RETURN" in response.upper():
                    if debug:
                        print("Found PRESS RETURN prompt, sending Enter key")
                    self.tn.write(b"\r\n")
                    time.sleep(0.5)
                    # Read response after pressing return
                    return_response = self.tn.read_very_eager()
                    if return_response:
                        response += return_response.decode('utf-8', errors='ignore')
                        if debug:
                            print(f"After RETURN: {repr(return_response[:100])}")
                
                # Check for character menu ("Make your choice:")
                if "Make your choice:" in response:
                    if debug:
                        print("Found character menu, selecting option 1 to enter game")
                    # Select option 1 to enter the game
                    self.tn.write(b"1\r\n")
                    time.sleep(1)
                    menu_response = self.tn.read_very_eager()
                    if menu_response:
                        response += menu_response.decode('utf-8', errors='ignore')
                        if debug:
                            print(f"After selecting option 1: {repr(menu_response[:100])}")
                
                # Try to get to a prompt
                final_response = self._read_until_prompt(timeout=5)
                response += final_response
                
                if debug:
                    print(f"Final connection state: {repr(response[-200:])}")
                
                # Check if we're actually connected
                if "huh?" in response.lower() or ">" in response or "hp:" in response.lower():
                    print("Connected successfully!")
                else:
                    print("Connection may not be fully established")
                    print(f"Last 200 chars: {repr(response[-200:])}")
                
                return response
                
            except ConnectionRefusedError:
                if attempt < max_retries - 1:
                    print(f"Connection refused, retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print(f"ERROR: Could not connect to {host}:{port} after {max_retries} attempts")
                    sys.exit(1)
            except Exception as e:
                print(f"ERROR: Connection failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    sys.exit(1)
        
        return ""
    
    def _read_raw(self, timeout: float = 2.0) -> str:
        """
        Read raw data from connection with timeout.
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            Server response
        """
        if not self.tn:
            return "[ERROR: Not connected]"
        
        try:
            # Use read_until with a common pattern or timeout
            # First try to read anything available immediately
            data = self.tn.read_very_eager()
            if data:
                return data.decode('utf-8', errors='ignore')
            
            # If nothing immediate, try to read with a short timeout
            # Use read_until with newline or common MUD patterns
            try:
                data = self.tn.read_until(b"\n", timeout=timeout)
                return data.decode('utf-8', errors='ignore')
            except EOFError:
                return "[CONNECTION CLOSED]"
            except Exception:
                # If timeout or other error, return empty
                return ""
            
        except EOFError:
            return "[CONNECTION CLOSED]"
        except Exception as e:
            return f"[READ ERROR: {e}]"
    
    def _read_until_prompt(self, timeout: float = 10.0) -> str:
        """
        Read from connection until MUD prompt appears or timeout.
        
        Args:
            timeout: Maximum time to wait for prompt
            
        Returns:
            Server response
        """
        if not self.tn:
            return "[ERROR: Not connected]"
        
        start_time = time.time()
        response = ""
        
        while time.time() - start_time < timeout:
            try:
                # Check if data is available
                data = self.tn.read_very_eager()
                if data:
                    response += data.decode('utf-8', errors='ignore')
                    
                    # Check for common MUD prompts
                    if "HP:" in response or ">" in response or "Huh?" in response:
                        break
                
                time.sleep(0.1)
            except EOFError:
                response += "[CONNECTION CLOSED]"
                break
            except Exception as e:
                response += f"[READ ERROR: {e}]"
                break
        
        # Add timeout marker if we didn't get a clear prompt
        if "HP:" not in response and ">" not in response and "Huh?" not in response:
            response += f"\n[TIMEOUT after {timeout}s]"
        
        return response
    
    def send_command(self, command: str, timeout: float = 2.0) -> str:
        """
        Send a single command to the MUD.
        
        Args:
            command: Raw MUD command
            timeout: Timeout for response
            
        Returns:
            Server response
        """
        if not self.tn:
            return "[ERROR: Not connected]"
        
        print(f"Sending command: {command}")
        self.tn.write(f"{command}\r\n".encode())
        time.sleep(0.1)  # Brief delay
        
        return self._read_until_prompt(timeout)
    
    def send_commands(self, commands: List[str], delay: float = 0.2) -> List[str]:
        """
        Send multiple commands sequentially.
        
        Args:
            commands: List of raw MUD commands
            delay: Delay between commands in seconds
            
        Returns:
            List of server responses
        """
        responses = []
        
        for cmd in commands:
            response = self.send_command(cmd)
            responses.append(response)
            if delay > 0:
                time.sleep(delay)
        
        return responses
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get character status by sending 'score' and 'inventory'.
        
        Returns:
            Parsed character status as dictionary
        """
        if not self.tn:
            return {"error": "Not connected"}
        
        # Send score command
        score_response = self.send_command("score")
        
        # Send inventory command
        inventory_response = self.send_command("inventory")
        
        # Parse the responses (basic parsing - could be enhanced)
        status = {
            "score_raw": score_response,
            "inventory_raw": inventory_response,
            "timestamp": time.time()
        }
        
        return status
    
    def disconnect(self):
        """Disconnect from MUD server."""
        if self.tn:
            try:
                self.tn.close()
                print("Disconnected")
            except:
                pass
            finally:
                self.tn = None


def save_output(output: str, output_file: Optional[str] = None):
    """Save output to file or print to console."""
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Output saved to {output_file}")
        except Exception as e:
            print(f"ERROR: Could not save to {output_file}: {e}")
    else:
        print("\n" + "="*50)
        print(output)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="CircleMUD Client")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    
    # Connect command
    connect_parser = subparsers.add_parser('connect', help='Connect to MUD and auto-login')
    connect_parser.add_argument('--output', help='Output file for response')
    connect_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Command command
    cmd_parser = subparsers.add_parser('cmd', help='Send a single raw command')
    cmd_parser.add_argument('mud_command', help='MUD command to send')
    cmd_parser.add_argument('--output', help='Output file for response')
    cmd_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Send multiple commands')
    run_parser.add_argument('--commands', nargs='+', required=True, help='MUD commands to send')
    run_parser.add_argument('--output', help='Output file for response')
    run_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get character status')
    status_parser.add_argument('--output', help='Output file for JSON response')
    status_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Session command
    session_parser = subparsers.add_parser('session', help='Interactive REPL session')
    session_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Map command
    map_parser = subparsers.add_parser('map', help='Build room map')
    map_parser.add_argument('--output', help='Output file for JSON map')
    map_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Disconnect command
    disconnect_parser = subparsers.add_parser('disconnect', help='Disconnect from MUD')
    disconnect_parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Create client with config from project root
    config_path = str(project_root / "config.json")
    client = MUDClient(config_path)
    
    try:
        if args.command == 'connect':
            response = client.connect(debug=args.debug)
            save_output(response, args.output)
            # Don't disconnect after connect - keep connection open
            print("\nNote: Connection remains open. Use 'disconnect' command to close.")
            return
            
        elif args.command == 'cmd':
            if not client.is_connected():
                client.connect(debug=args.debug)
            response = client.send_command(args.mud_command)
            save_output(response, args.output)
            print("\nNote: Connection remains open for further commands.")
            print("Use 'disconnect' command when done.")
            
        elif args.command == 'run':
            if not client.is_connected():
                client.connect(debug=args.debug)
            responses = client.send_commands(args.commands)
            combined = "\n---\n".join(responses)
            save_output(combined, args.output)
            print("\nNote: Connection remains open for further commands.")
            print("Use 'disconnect' command when done.")
            
        elif args.command == 'status':
            if not client.is_connected():
                client.connect(debug=args.debug)
            status = client.get_status()
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(status, f, indent=2)
                print(f"Status saved to {args.output}")
            else:
                print(json.dumps(status, indent=2))
            print("\nNote: Connection remains open for further commands.")
            print("Use 'disconnect' command when done.")
                
        elif args.command == 'session':
            client.connect(debug=args.debug)
            print("Interactive session started. Type 'quit' to exit.")
            print("-" * 50)
            
            while True:
                try:
                    cmd = input("MUD> ").strip()
                    if cmd.lower() == 'quit':
                        break
                    if cmd:
                        response = client.send_command(cmd)
                        print(response)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except EOFError:
                    break
            # Session ends, disconnect
            client.disconnect()
            return
                    
        elif args.command == 'map':
            if not client.is_connected():
                client.connect(debug=args.debug)
            # Basic mapping - explore immediate area
            commands = ["look", "n", "s", "e", "w", "u", "d"]
            responses = {}
            
            for cmd in commands:
                response = client.send_command(cmd)
                responses[cmd] = response
            
            map_data = {
                "explored_commands": commands,
                "responses": responses,
                "timestamp": time.time()
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(map_data, f, indent=2)
                print(f"Map data saved to {args.output}")
            else:
                print(json.dumps(map_data, indent=2))
            print("\nNote: Connection remains open for further commands.")
            print("Use 'disconnect' command when done.")
        
        elif args.command == 'disconnect':
            client.disconnect()
            print("Disconnected from MUD")
            return
    
    except Exception as e:
        print(f"ERROR: {e}")
        client.disconnect()


if __name__ == "__main__":
    main()