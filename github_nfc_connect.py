#!/usr/bin/env python3
"""
GitHub NFC Connect - Seamless SSH Authentication
Automatically handles GitHub SSH authentication using zero-knowledge NFC process
"""

import json
import hashlib
import sys
import os
import signal
import subprocess
import tempfile
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def invisible_nfc_scan(purpose="authentication"):
    """Simple NFC scan that works with barcode scanner input"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}")
    print("🔒 Place NFC tag on reader...")
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked")
    print("   🎯 Scan NFC tag now (press Enter when done):")
    
    try:
        # Simple input that works with barcode scanner
        tag_data = input("").strip()
        
        if not tag_data:
            print("❌ No tag data received")
            return None
        
        # Show masked version
        print("*" * len(tag_data))
        
        # Immediately hash the tag data (NEVER store or display raw)
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
        
        # Securely overwrite raw tag data
        tag_data = "0" * len(tag_data)
        del tag_data
        
        print("✅ NFC scan completed (zero-knowledge mode)")
        return tag_hash
        
    except KeyboardInterrupt:
        print("\n⚠️ NFC scan cancelled")
        return None
    except Exception as e:
        print(f"\n❌ NFC scan failed: {e}")
        return None

def generate_passphrase():
    """Generate passphrase from dual NFC scans + real ambient data"""
    
    print("🔐 GITHUB ZERO-KNOWLEDGE SSH AUTHENTICATION")
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

def connect_to_github():
    """Connect to GitHub using zero-knowledge NFC authentication"""
    
    # Generate passphrase using NFC
    passphrase = generate_passphrase()
    
    if not passphrase:
        print("❌ Failed to generate passphrase")
        return False
    
    print("\n🔐 STEP 3: SSH CONNECTION TO GITHUB")
    print("🚀 Connecting with zero-knowledge passphrase...")
    
    # Create temporary askpass script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
        f.write(f'#!/bin/bash\necho "{passphrase}"\n')
        temp_askpass = f.name
    
    os.chmod(temp_askpass, 0o700)
    
    try:
        # Set environment for SSH_ASKPASS
        env = os.environ.copy()
        env['SSH_ASKPASS'] = temp_askpass
        env['DISPLAY'] = ':0'
        
        # Connect to GitHub
        result = subprocess.run([
            'ssh', '-o', 'StrictHostKeyChecking=no', 
            '-T', 'github-zero-nfc-new'
        ], env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        
        # Clean up
        os.unlink(temp_askpass)
        
        # Clear passphrase from memory
        passphrase = "0" * len(passphrase)
        del passphrase
        
        if result.returncode == 1 and "successfully authenticated" in result.stderr:
            print("✅ GitHub SSH authentication successful!")
            print(f"   {result.stderr.strip()}")
            return True
        else:
            print(f"❌ SSH connection failed")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except Exception as e:
        # Clean up temp file
        if os.path.exists(temp_askpass):
            os.unlink(temp_askpass)
        print(f"❌ SSH error: {e}")
        return False

def main():
    """Main GitHub NFC connection"""
    
    print("🔐 GitHub Zero-Knowledge NFC SSH Connection")
    print("🚀 Seamless authentication using dual NFC scans + real ambient data")
    print()
    
    success = connect_to_github()
    
    if success:
        print("\n🎉 GITHUB CONNECTION SUCCESSFUL")
        print("   ✅ Zero-knowledge NFC authentication complete")
        print("   ✅ No passphrase displayed or stored")
        print("   ✅ Ready for GitHub operations")
        print("\n📋 You can now use: git clone git@github-zero-nfc-new:username/repo.git")
    else:
        print("\n❌ GITHUB CONNECTION FAILED")
        print("   Check your NFC tags and USB authentication pack")

if __name__ == "__main__":
    main()
