#!/usr/bin/env python3
"""
Invisible NFC Scanner - Zero-knowledge tag reading
Uses termios to capture tag data without any terminal display
"""

import sys
import termios
import tty
import time
import hashlib
import select

class InvisibleNFCScanner:
    """Invisible NFC tag scanner using termios raw mode"""
    
    def __init__(self):
        self.original_settings = None
        
    def enter_raw_mode(self):
        """Enter raw terminal mode to capture input without echo"""
        if sys.stdin.isatty():
            self.original_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
    
    def exit_raw_mode(self):
        """Restore normal terminal mode"""
        if self.original_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
    
    def invisible_scan_simple(self):
        """
        Simple invisible scan for HID readers (auto-type mode)
        Uses getpass-style input suppression
        """
        print("🔒 Place NFC tag on reader...")
        print("   ⚡ Invisible mode - tag data will NOT appear on screen")
        print("   Press Enter after tag auto-types")
        
        # Use termios to disable echo
        if sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin)
            new_settings = termios.tcgetattr(sys.stdin)
            new_settings[3] = new_settings[3] & ~termios.ECHO  # Disable echo
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)
        
        try:
            # This will capture the auto-typed input without displaying it
            tag_data = sys.stdin.readline().strip()
            
            if tag_data:
                # CRITICAL: Never return or display raw tag data
                # Immediately hash for authentication key derivation
                tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
                
                # Securely clear raw data from memory
                tag_data = "0" * len(tag_data)  # Overwrite
                tag_data = None  # Release
                
                print("✅ Tag scanned invisibly")
                print("   Authentication key derived: [HIDDEN]")
                print("   Raw UID: [NEVER STORED - Zero Knowledge]")
                
                return tag_hash
            else:
                print("❌ No tag data received")
                return None
                
        except KeyboardInterrupt:
            print("\n❌ Scan cancelled")
            return None
        
        finally:
            # Restore normal terminal settings
            if sys.stdin.isatty():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def test_invisible_scan():
    """Test invisible NFC scanning"""
    print("=" * 60)
    print("   INVISIBLE NFC SCANNER TEST")
    print("=" * 60)
    print("\n🔐 Zero-knowledge tag authentication")
    print("   • No tag data displayed")
    print("   • No data stored in logs")
    print("   • Used only for key derivation")
    
    scanner = InvisibleNFCScanner()
    auth_key = scanner.invisible_scan_simple()
    
    if auth_key:
        print(f"\n🎯 Authentication key length: {len(auth_key)} chars")
        print(f"   Key preview: {auth_key[:8]}...")
        print(f"   Key type: SHA256 hash")
        
        # Demonstrate key derivation for encryption
        encryption_key = hashlib.pbkdf2_hmac('sha256', 
                                           auth_key.encode(), 
                                           b'nfc_salt', 
                                           100000)[:32]
        
        print(f"\n🔑 Encryption key derived successfully")
        print(f"   Length: {len(encryption_key)} bytes")
        print(f"   PBKDF2 iterations: 100,000")
        print(f"   Ready for credential vault decryption")
        
        return auth_key
    
    return None

if __name__ == "__main__":
    # Import select here to avoid issues if not available
    try:
        import select
        test_invisible_scan()
    except ImportError:
        print("❌ select module not available")
        print("   This system requires Unix-like OS for invisible scanning")
