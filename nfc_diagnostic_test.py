#!/usr/bin/env python3
"""
NFC Diagnostic Test - Non-blocking NFC scanner test
Tests NFC functionality with timeout to prevent hanging
"""

import sys
import hashlib
import select
import termios
import tty
import time

class NFCDiagnostic:
    def __init__(self):
        self.original_settings = None
    
    def setup_terminal(self):
        """Setup terminal for invisible input"""
        try:
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
            # Disable echo
            new_settings = termios.tcgetattr(sys.stdin)
            new_settings[3] = new_settings[3] & ~termios.ECHO
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)
            return True
        except Exception as e:
            print(f"❌ Terminal setup failed: {e}")
            return False
    
    def restore_terminal(self):
        """Restore original terminal settings"""
        if self.original_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
            except:
                pass
    
    def test_nfc_with_timeout(self, timeout_seconds=10):
        """Test NFC scanning with timeout"""
        print(f"🔍 Testing NFC scan (timeout: {timeout_seconds}s)")
        print("   Place NFC tag on reader and press Enter...")
        print("   Or just press Enter to skip")
        
        if not self.setup_terminal():
            return None
        
        try:
            start_time = time.time()
            input_data = ""
            
            while time.time() - start_time < timeout_seconds:
                # Check if input is available
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char == '\n' or char == '\r':
                        break
                    input_data += char
                
                # Show countdown
                remaining = int(timeout_seconds - (time.time() - start_time))
                if remaining != getattr(self, '_last_countdown', -1):
                    print(f"\r   Timeout in {remaining}s... ", end='', flush=True)
                    self._last_countdown = remaining
            
            print("\n")
            
            if input_data.strip():
                # Hash the input data
                tag_hash = hashlib.sha256(input_data.encode()).hexdigest()
                print(f"✅ NFC data received and hashed")
                print(f"   Hash: {tag_hash[:16]}...")
                return tag_hash
            else:
                print("⏰ No NFC data received (timeout or manual skip)")
                return None
                
        except Exception as e:
            print(f"❌ NFC test error: {e}")
            return None
        finally:
            self.restore_terminal()
    
    def test_fallback_input(self):
        """Test with manual keyboard input"""
        print("\n🔤 Testing manual input fallback:")
        try:
            test_input = input("   Enter test string (or press Enter to skip): ").strip()
            if test_input:
                test_hash = hashlib.sha256(test_input.encode()).hexdigest()
                print(f"✅ Manual input hashed")
                print(f"   Hash: {test_hash[:16]}...")
                return test_hash
            return None
        except Exception as e:
            print(f"❌ Manual input error: {e}")
            return None

def main():
    print("🔐 NFC DIAGNOSTIC TEST")
    print("=" * 40)
    
    diagnostic = NFCDiagnostic()
    
    # Test 1: NFC with timeout
    nfc_result = diagnostic.test_nfc_with_timeout(timeout_seconds=5)
    
    # Test 2: Manual input fallback
    manual_result = diagnostic.test_fallback_input()
    
    # Summary
    print("\n📊 DIAGNOSTIC RESULTS:")
    print(f"   NFC Scanner: {'✅ Working' if nfc_result else '❌ Not responding'}")
    print(f"   Manual Input: {'✅ Working' if manual_result else '❌ Failed'}")
    
    if nfc_result or manual_result:
        print("\n✅ System can generate SSH keys")
    else:
        print("\n❌ No input method working - check hardware")

if __name__ == "__main__":
    main()
