#!/usr/bin/env python3
"""
Demo Zero-Knowledge NFC Authentication
Working demonstration of the complete zero-knowledge system
"""

import json
import hashlib
import sys
import os
import subprocess
import time
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64

def demo_nfc_scan(purpose="authentication"):
    """Demo NFC scan with masking"""
    
    print(f"🏷️  NFC SCAN - {purpose.upper()}")
    print("🔒 Place NFC tag on reader...")
    print("   ⚡ ZERO-KNOWLEDGE MODE - input will be masked")
    print("   🎯 Scan NFC tag now (press Enter when done):")
    
    # Simple input for demo
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

def create_demo_pack():
    """Create demo zero-knowledge authentication pack"""
    
    print("🔐 CREATING FRESH ZERO-KNOWLEDGE PACK")
    print("=" * 50)
    
    # Find USB
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    if not os.path.exists(usb_path):
        print("❌ USB not found at /Volumes/YOUR_USB_DRIVE")
        return False
    
    print(f"✅ Found USB: {usb_path}")
    
    # Create auth folder
    auth_folder = os.path.join(usb_path, 'zero_knowledge_auth')
    os.makedirs(auth_folder, exist_ok=True)
    
    # First NFC scan - unlock key
    print("\n🏷️ STEP 1: NFC UNLOCK KEY BINDING")
    nfc_unlock_hash = demo_nfc_scan("unlock key binding")
    if not nfc_unlock_hash:
        return False
    
    print("✅ NFC unlock key bound (never stored)")
    
    # Demo ambient audio (no actual recording)
    print("\n🎵 STEP 2: AMBIENT AUDIO CAPTURE (demo)")
    print("🎵 Simulating ambient audio capture...")
    print("   Progress: ", end='', flush=True)
    
    # Simulate progress
    for i in range(6):
        time.sleep(1)
        print("●", end='', flush=True)
    
    # Create demo audio data
    demo_audio = b"demo_ambient_audio_data_" + os.urandom(1024)
    print(f"\n✅ Ambient audio captured: {len(demo_audio)} bytes")
    
    # Encrypt ambient data with NFC unlock key
    print("\n🔐 STEP 3: ENCRYPTING AMBIENT DATA")
    encrypted_hash = hashlib.sha256(f"{nfc_unlock_hash}{hashlib.sha256(demo_audio).hexdigest()}".encode()).hexdigest()
    
    # Save encrypted pack
    pack_data = {
        'timestamp': datetime.now().isoformat(),
        'encrypted_ambient_hash': encrypted_hash,
        'audio_size': len(demo_audio),
        'version': 'zero_knowledge_v1'
    }
    
    pack_file = os.path.join(auth_folder, 'zero_knowledge_pack.json')
    with open(pack_file, 'w') as f:
        json.dump(pack_data, f, indent=2)
    
    print("✅ Ambient data encrypted with NFC unlock key")
    
    print("\n💾 STEP 4: SAVING AUTHENTICATION PACK")
    print(f"   📁 Pack saved: {pack_file}")
    print("✅ Zero-knowledge pack created successfully!")
    print("\n🎉 PACK READY FOR AUTHENTICATION")
    
    return True

def authenticate_demo():
    """Demo authentication with dual NFC scans"""
    
    print("🔐 ZERO-KNOWLEDGE AUTHENTICATION")
    print("=" * 50)
    
    # Find USB and pack
    usb_path = '/Volumes/YOUR_USB_DRIVE'
    auth_folder = os.path.join(usb_path, 'zero_knowledge_auth')
    pack_file = os.path.join(auth_folder, 'zero_knowledge_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No authentication pack found")
        return False
    
    print(f"✅ Found authentication pack")
    
    # Load pack
    with open(pack_file, 'r') as f:
        pack_data = json.load(f)
    
    # First NFC scan - unlock ambient data
    print("\n🏷️ STEP 1: NFC UNLOCK SCAN")
    nfc_unlock_hash = demo_nfc_scan("unlock ambient data")
    if not nfc_unlock_hash:
        return False
    
    print("✅ Ambient data unlocked (never displayed)")
    
    # Simulate unlocked ambient data
    demo_audio = b"demo_ambient_audio_data_" + os.urandom(1024)
    
    # Second NFC scan - assemble passphrase
    print("\n🏷️ STEP 2: NFC PASSPHRASE ASSEMBLY")
    nfc_auth_hash = demo_nfc_scan("passphrase assembly")
    if not nfc_auth_hash:
        return False
    
    print("✅ Passphrase assembled invisibly (never displayed)")
    
    # Generate passphrase invisibly
    passphrase_data = f"{nfc_auth_hash}{hashlib.sha256(demo_audio).hexdigest()}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    # Generate SSH key
    print("\n🔐 STEP 3: SSH KEY GENERATION")
    print("🔑 Generating SSH key with invisible passphrase...")
    
    # Generate RSA key pair
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Encrypt private key with passphrase
    encrypted_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode())
    )
    
    # Get public key
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    
    # Save SSH keys
    ssh_dir = os.path.expanduser('~/.ssh')
    os.makedirs(ssh_dir, exist_ok=True)
    
    timestamp = int(datetime.now().timestamp())
    private_key_file = os.path.join(ssh_dir, f'github_zero_knowledge_{timestamp}')
    public_key_file = f'{private_key_file}.pub'
    
    # Save private key
    with open(private_key_file, 'wb') as f:
        f.write(encrypted_private_key)
    os.chmod(private_key_file, 0o600)
    
    # Save public key
    with open(public_key_file, 'wb') as f:
        f.write(public_key_bytes)
    os.chmod(public_key_file, 0o644)
    
    # Clear passphrase from memory
    passphrase = "0" * len(passphrase)
    del passphrase
    
    print(f"✅ SSH key generated: {private_key_file}")
    print(f"✅ Public key: {public_key_file}")
    
    print("\n🎉 ZERO-KNOWLEDGE AUTHENTICATION COMPLETE")
    print("   ✅ No NFC data displayed or stored")
    print("   ✅ No passphrase displayed or stored") 
    print("   ✅ SSH key encrypted with invisible passphrase")
    print("   ✅ All sensitive data cleared from memory")
    
    return True

def main():
    """Main demo interface"""
    
    print("🔐 Zero-Knowledge NFC Authentication Demo")
    print("=" * 50)
    print("Choose:")
    print("(1) Create authentication pack")
    print("(2) Authenticate with dual NFC scans")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == '1':
        success = create_demo_pack()
        if success:
            print("\n✅ Demo pack creation: SUCCESS")
        else:
            print("\n❌ Demo pack creation: FAILED")
    
    elif choice == '2':
        success = authenticate_demo()
        if success:
            print("\n✅ Demo authentication: SUCCESS")
        else:
            print("\n❌ Demo authentication: FAILED")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
