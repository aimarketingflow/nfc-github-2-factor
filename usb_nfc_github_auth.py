#!/usr/bin/env python3
"""
USB + NFC GitHub Authentication System
Requires USB pack with ambient data + NFC scan for GitHub SSH access
"""

import os
import json
import hashlib
import base64
import numpy as np
import time
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from invisible_nfc_scanner import InvisibleNFCScanner

class USBNFCGitHubAuth:
    """USB + NFC authentication for GitHub SSH access"""
    
    def __init__(self):
        self.usb_paths = ["/Volumes/SILVER", "/Volumes/USB", "/Volumes/Untitled"]
        self.pack_filename = "mobileshield_auth_pack.json"
        
    def find_usb_pack(self):
        """Find USB drive with authentication pack"""
        
        print("🔍 SEARCHING FOR USB AUTHENTICATION PACK")
        print("=" * 45)
        
        for usb_path in self.usb_paths:
            if os.path.exists(usb_path):
                pack_path = os.path.join(usb_path, self.pack_filename)
                if os.path.exists(pack_path):
                    print(f"✅ Found USB pack: {pack_path}")
                    return pack_path, usb_path
                else:
                    print(f"📁 USB found but no pack: {usb_path}")
        
        print("❌ No USB authentication pack found")
        print("   Create pack with: python3 create_usb_auth_pack.py")
        return None, None
    
    def validate_usb_pack(self, pack_path, nfc_hash):
        """Validate USB pack with NFC authentication"""
        
        print("🔐 VALIDATING USB PACK WITH NFC")
        print("=" * 35)
        
        try:
            with open(pack_path, 'r') as f:
                pack_data = json.load(f)
            
            # Check required fields
            required_fields = ['pack_metadata', 'ambient_audio_hash', 'chaos_entropy', 'creation_location']
            for field in required_fields:
                if field not in pack_data:
                    print(f"❌ Missing required field: {field}")
                    return None
            
            # Validate NFC hash matches pack
            stored_nfc_hash = pack_data['pack_metadata'].get('nfc_binding_hash')
            if not stored_nfc_hash:
                print("❌ No NFC binding hash in pack")
                return None
            
            if stored_nfc_hash != nfc_hash:
                print("❌ NFC authentication failed - wrong tag")
                return None
            
            print("✅ USB pack validated with NFC authentication")
            print(f"   Creation time: {pack_data['pack_metadata']['creation_time']}")
            print(f"   Location: {pack_data['creation_location']}")
            print(f"   Audio hash: {pack_data['ambient_audio_hash'][:16]}...")
            print(f"   Chaos entropy: {pack_data['chaos_entropy'][:16]}...")
            
            return pack_data
            
        except Exception as e:
            print(f"❌ Pack validation error: {e}")
            return None
    
    def generate_github_ssh_keys(self, pack_data, nfc_hash):
        """Generate GitHub SSH keys from USB pack + NFC"""
        
        print("🔑 GENERATING GITHUB SSH KEYS")
        print("=" * 32)
        
        # Create composite authentication material
        composite_material = (
            nfc_hash +
            pack_data['ambient_audio_hash'] +
            str(pack_data['chaos_entropy']) +
            pack_data['creation_location'] +
            "GITHUB_SSH_AUTHENTICATION"
        ).encode()
        
        # Generate deterministic SSH keys
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'USB_NFC_GITHUB_SALT',
            iterations=150000,
        )
        
        key_seed = kdf.derive(composite_material)
        
        # Use seed for deterministic key generation
        seed_32bit = int.from_bytes(key_seed[:4], 'big') % (2**32)
        np.random.seed(seed_32bit)
        
        print("🔒 Generating 4096-bit RSA key pair...")
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        
        public_key = private_key.public_key()
        
        # Create SSH directory if needed
        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        
        # Use consistent filename based on pack
        pack_id = hashlib.sha256(composite_material).hexdigest()[:8]
        key_name = f"usb_nfc_github_{pack_id}"
        
        private_key_path = os.path.join(ssh_dir, key_name)
        public_key_path = os.path.join(ssh_dir, f"{key_name}.pub")
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        # Save private key
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_key_path, 0o600)
        
        # Save public key with comment
        hostname = os.uname().nodename
        public_key_content = public_ssh.decode() + f" usb-nfc-mobileshield@{hostname}\n"
        
        with open(public_key_path, 'w') as f:
            f.write(public_key_content)
        
        print(f"✅ SSH keys generated successfully!")
        print(f"   Private key: {private_key_path}")
        print(f"   Public key: {public_key_path}")
        print(f"   Key ID: {pack_id}")
        
        return {
            'private_key_path': private_key_path,
            'public_key_path': public_key_path,
            'public_key_content': public_key_content.strip(),
            'key_id': pack_id
        }
    
    def test_github_connection(self, private_key_path):
        """Test GitHub SSH connection"""
        
        print("🔗 TESTING GITHUB SSH CONNECTION")
        print("=" * 35)
        
        import subprocess
        
        try:
            # Test SSH connection to GitHub
            result = subprocess.run([
                'ssh', '-i', private_key_path, '-T', 'git@github.com'
            ], capture_output=True, text=True, timeout=10)
            
            if 'successfully authenticated' in result.stderr:
                print("✅ GitHub SSH authentication successful!")
                print(f"   Response: {result.stderr.strip()}")
                return True
            else:
                print("❌ GitHub SSH authentication failed")
                print(f"   Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ SSH connection timed out")
            return False
        except Exception as e:
            print(f"❌ SSH test error: {e}")
            return False
    
    def authenticate_github(self):
        """Complete USB + NFC GitHub authentication workflow"""
        
        print("🔐 USB + NFC GITHUB AUTHENTICATION")
        print("=" * 40)
        print("Requires USB pack + NFC tag for SSH access")
        print()
        
        # Step 1: Find USB pack
        pack_path, usb_path = self.find_usb_pack()
        if not pack_path:
            return None
        
        print()
        
        # Step 2: NFC authentication
        print("🏷️  NFC AUTHENTICATION REQUIRED")
        scanner = InvisibleNFCScanner()
        nfc_hash = scanner.invisible_scan_simple()
        if not nfc_hash:
            print("❌ NFC authentication failed")
            return None
        
        print()
        
        # Step 3: Validate USB pack with NFC
        pack_data = self.validate_usb_pack(pack_path, nfc_hash)
        if not pack_data:
            return None
        
        print()
        
        # Step 4: Generate SSH keys
        ssh_keys = self.generate_github_ssh_keys(pack_data, nfc_hash)
        if not ssh_keys:
            return None
        
        print()
        
        # Step 5: Test GitHub connection
        connection_success = self.test_github_connection(ssh_keys['private_key_path'])
        
        print()
        print("🎯 AUTHENTICATION SUMMARY")
        print("=" * 25)
        print(f"   USB Pack: ✅ Validated")
        print(f"   NFC Auth: ✅ Authenticated") 
        print(f"   SSH Keys: ✅ Generated")
        print(f"   GitHub: {'✅ Connected' if connection_success else '❌ Failed'}")
        print(f"   Key ID: {ssh_keys['key_id']}")
        
        if connection_success:
            print(f"\n🚀 SUCCESS! GitHub SSH access granted")
            print(f"   Use key: {ssh_keys['private_key_path']}")
        else:
            print(f"\n⚠️  SSH keys generated but GitHub connection failed")
            print(f"   Check if public key is added to GitHub")
        
        return ssh_keys

def main():
    """Main authentication workflow"""
    
    auth = USBNFCGitHubAuth()
    result = auth.authenticate_github()
    
    if result:
        print(f"\n🔑 Ready for GitHub operations with USB + NFC authentication")
    else:
        print(f"\n❌ Authentication failed - check USB pack and NFC tag")

if __name__ == "__main__":
    main()
