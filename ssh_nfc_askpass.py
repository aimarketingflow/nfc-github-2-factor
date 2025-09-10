#!/usr/bin/env python3
"""
SSH NFC AskPass - Zero-Knowledge Passphrase Provider for SSH
Called by SSH when passphrase is needed - automatically triggers NFC authentication
"""

import json
import hashlib
import sys
import os
import signal
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def invisible_nfc_scan(purpose="authentication"):
    """Invisible NFC scan - outputs to stderr to avoid interfering with SSH"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}", file=sys.stderr)
    print("🔒 Place NFC tag on reader...", file=sys.stderr)
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked", file=sys.stderr)
    print("   🎯 Scan NFC tag now (press Enter when done):", file=sys.stderr)
    
    try:
        import termios
        import tty
        
        # Store original terminal settings
        original_settings = termios.tcgetattr(sys.stdin)
        
        def timeout_handler(signum, frame):
            raise TimeoutError("NFC scan timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            tty.setcbreak(sys.stdin.fileno())
            
            tag_data = ""
            while True:
                try:
                    char = sys.stdin.read(1)
                    if char == '\n' or char == '\r':
                        break
                    elif char == '\x03':
                        raise KeyboardInterrupt()
                    elif char == '\x7f':
                        if tag_data:
                            tag_data = tag_data[:-1]
                            print(".", end='', flush=True, file=sys.stderr)
                    else:
                        tag_data += char
                        print("*", end='', flush=True, file=sys.stderr)
                except Exception as e:
                    print(f"\n❌ Input error: {e}", file=sys.stderr)
                    return None
            
            signal.alarm(0)
            
        finally:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
            except:
                pass
        
        if not tag_data:
            print("\n❌ No tag data received", file=sys.stderr)
            return None
        
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
        tag_data = "0" * len(tag_data)
        del tag_data
        
        print(f"\n✅ NFC scan completed (zero-knowledge mode)", file=sys.stderr)
        return tag_hash
        
    except TimeoutError:
        print("\n❌ NFC scan timeout", file=sys.stderr)
        return None
    except KeyboardInterrupt:
        print("\n⚠️ NFC scan cancelled", file=sys.stderr)
        return None
    except Exception as e:
        print(f"\n❌ NFC scan failed: {e}", file=sys.stderr)
        return None

def generate_ssh_passphrase():
    """Generate passphrase for SSH - all output to stderr except final passphrase"""
    
    print("🔐 SSH PASSPHRASE REQUEST DETECTED", file=sys.stderr)
    print("🚀 Activating Zero-Knowledge NFC Authentication...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    # Find USB and pack
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No real ambient authentication pack found", file=sys.stderr)
        return None
    
    print(f"✅ Found authentication pack on USB", file=sys.stderr)
    
    # Load pack
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    # First NFC scan - unlock ambient data
    print("\n🏷️ STEP 1: NFC UNLOCK SCAN", file=sys.stderr)
    nfc_unlock_hash = invisible_nfc_scan("unlock ambient data")
    if not nfc_unlock_hash:
        return None
    
    # Decrypt ambient data
    try:
        from cryptography.fernet import Fernet
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'ambient_encryption_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(nfc_unlock_hash.encode()))
        fernet = Fernet(key)
        
        with open(pack_data['encrypted_file'], 'rb') as f:
            encrypted_ambient = f.read()
        
        decrypted_ambient = fernet.decrypt(encrypted_ambient)
        print("✅ Real ambient data unlocked (never displayed)", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Failed to unlock ambient data: {e}", file=sys.stderr)
        return None
    
    # Second NFC scan - assemble passphrase
    print("\n🏷️ STEP 2: NFC PASSPHRASE ASSEMBLY", file=sys.stderr)
    nfc_auth_hash = invisible_nfc_scan("passphrase assembly")
    if not nfc_auth_hash:
        return None
    
    print("✅ Passphrase assembled invisibly", file=sys.stderr)
    
    # Generate passphrase invisibly
    ambient_hash = hashlib.sha256(decrypted_ambient).hexdigest()
    passphrase_data = f"{nfc_auth_hash}{ambient_hash}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    print("🔐 Providing passphrase to SSH (invisible)", file=sys.stderr)
    
    # Clear sensitive data
    del decrypted_ambient
    
    return passphrase

def main():
    """SSH AskPass main - called by SSH when passphrase needed"""
    
    # Generate passphrase using NFC authentication
    passphrase = generate_ssh_passphrase()
    
    if passphrase:
        # Output ONLY the passphrase to stdout (SSH reads this)
        print(passphrase)
        
        # Clear from memory
        passphrase = "0" * len(passphrase)
        del passphrase
        
        print("✅ SSH authentication complete", file=sys.stderr)
    else:
        print("❌ SSH authentication failed", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
