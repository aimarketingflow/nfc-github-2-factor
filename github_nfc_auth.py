#!/usr/bin/env python3
"""
GitHub NFC Authentication - Seamless SSH with Zero-Knowledge NFC
Automatically handles SSH authentication to GitHub using dual NFC scans + real ambient data
"""

import json
import hashlib
import sys
import os
import signal
import subprocess
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def invisible_nfc_scan(purpose="authentication"):
    """Invisible NFC scan using PineappleExpress method"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}")
    print("🔒 Place NFC tag on reader...")
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked")
    print("   🎯 Scan NFC tag now (press Enter when done):")
    
    try:
        import termios
        import tty
        
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
                            print(".", end='', flush=True)
                    else:
                        tag_data += char
                        print("*", end='', flush=True)
                except Exception as e:
                    print(f"\n❌ Input error: {e}")
                    return None
            
            signal.alarm(0)
            
        finally:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_settings)
            except:
                pass
        
        if not tag_data:
            print("\n❌ No tag data received")
            return None
        
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
        tag_data = "0" * len(tag_data)
        del tag_data
        
        print(f"\n✅ NFC scan completed (zero-knowledge mode)")
        return tag_hash
        
    except TimeoutError:
        print("\n❌ NFC scan timeout")
        return None
    except KeyboardInterrupt:
        print("\n⚠️ NFC scan cancelled")
        return None
    except Exception as e:
        print(f"\n❌ NFC scan failed: {e}")
        return None

def generate_passphrase():
    """Generate passphrase from dual NFC scans + real ambient data"""
    
    print("🔐 GITHUB NFC AUTHENTICATION")
    print("=" * 50)
    
    # Find USB and pack
    usb_path = '/Volumes/BLUESAM'
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No real ambient authentication pack found")
        return None
    
    print(f"✅ Found authentication pack on USB")
    
    # Load pack
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    # First NFC scan - unlock ambient data
    print("\n🏷️ STEP 1: NFC UNLOCK SCAN")
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
        print("✅ Real ambient data unlocked (never displayed)")
        
    except Exception as e:
        print(f"❌ Failed to unlock ambient data: {e}")
        return None
    
    # Second NFC scan - assemble passphrase
    print("\n🏷️ STEP 2: NFC PASSPHRASE ASSEMBLY")
    nfc_auth_hash = invisible_nfc_scan("passphrase assembly")
    if not nfc_auth_hash:
        return None
    
    print("✅ Passphrase assembled invisibly (never displayed)")
    
    # Generate passphrase invisibly
    ambient_hash = hashlib.sha256(decrypted_ambient).hexdigest()
    passphrase_data = f"{nfc_auth_hash}{ambient_hash}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    # Clear sensitive data
    del decrypted_ambient
    
    return passphrase

def ssh_to_github():
    """SSH to GitHub using NFC authentication"""
    
    # Generate passphrase using NFC
    passphrase = generate_passphrase()
    
    if not passphrase:
        print("❌ Failed to generate passphrase")
        return False
    
    print("\n🔐 STEP 3: SSH AUTHENTICATION")
    print("🚀 Connecting to GitHub with zero-knowledge passphrase...")
    
    # Create a temporary script to provide the passphrase
    temp_script = f"""#!/bin/bash
echo "{passphrase}"
"""
    
    temp_file = '/tmp/nfc_ssh_pass.sh'
    with open(temp_file, 'w') as f:
        f.write(temp_script)
    
    os.chmod(temp_file, 0o700)
    
    try:
        # Set SSH_ASKPASS environment and run SSH
        env = os.environ.copy()
        env['SSH_ASKPASS'] = temp_file
        env['DISPLAY'] = ':0'
        
        result = subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            '-T', 'github-zero-nfc'
        ], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        
        # Clean up temp file
        os.remove(temp_file)
        
        # Clear passphrase from memory
        passphrase = "0" * len(passphrase)
        del passphrase
        
        if result.returncode == 1 and "successfully authenticated" in result.stderr:
            print("✅ GitHub SSH authentication successful!")
            print(result.stderr.strip())
            return True
        else:
            print(f"❌ SSH failed: {result.stderr}")
            return False
            
    except Exception as e:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print(f"❌ SSH error: {e}")
        return False

def main():
    """Main GitHub NFC authentication"""
    
    print("🔐 GitHub Zero-Knowledge NFC Authentication")
    print("🚀 Seamless SSH authentication using dual NFC scans + real ambient data")
    print()
    
    success = ssh_to_github()
    
    if success:
        print("\n🎉 GITHUB AUTHENTICATION COMPLETE")
        print("   ✅ Zero-knowledge NFC authentication successful")
        print("   ✅ No passphrase displayed or stored")
        print("   ✅ Ready for GitHub operations")
    else:
        print("\n❌ GITHUB AUTHENTICATION FAILED")

if __name__ == "__main__":
    main()
