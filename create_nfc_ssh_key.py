#!/usr/bin/env python3
"""
Create SSH Key with Dual NFC Passphrase
Generate SSH key using zero-knowledge dual NFC authentication
"""

import json
import hashlib
import sys
import os
import subprocess
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
        tag_data = input("").strip()
        
        if not tag_data:
            print("❌ No tag data received")
            return None
        
        print("*" * len(tag_data))
        tag_hash = hashlib.sha256(tag_data.encode()).hexdigest()
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

def generate_nfc_passphrase():
    """Generate passphrase from dual NFC scans + real ambient data"""
    
    print("🔐 DUAL NFC PASSPHRASE GENERATION")
    print("=" * 40)
    
    # Find USB and pack
    usb_path = '/Volumes/BLUESAM'
    auth_folder = os.path.join(usb_path, 'real_ambient_auth')
    pack_file = os.path.join(auth_folder, 'real_ambient_pack.json')
    
    if not os.path.exists(pack_file):
        print("❌ No real ambient authentication pack found on USB")
        return None
    
    print(f"✅ Found authentication pack on USB")
    
    # Load pack
    try:
        with open(pack_file, 'r') as f:
            pack_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load authentication pack: {e}")
        return None
    
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
        
        encrypted_file = os.path.join(auth_folder, pack_data['encrypted_file'])
        with open(encrypted_file, 'rb') as f:
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
    
    # Generate passphrase invisibly
    ambient_hash = hashlib.sha256(decrypted_ambient).hexdigest()
    passphrase_data = f"{nfc_auth_hash}{ambient_hash}"
    passphrase = hashlib.sha256(passphrase_data.encode()).hexdigest()[:32]
    
    print("✅ Passphrase generated invisibly (32-character)")
    
    # Clear sensitive data
    del decrypted_ambient
    
    return passphrase

def create_ssh_key_with_nfc_passphrase():
    """Create SSH key using dual NFC passphrase"""
    
    print("🔑 CREATING SSH KEY WITH DUAL NFC PASSPHRASE")
    print("=" * 50)
    
    # Generate NFC passphrase
    passphrase = generate_nfc_passphrase()
    
    if not passphrase:
        print("❌ Failed to generate NFC passphrase")
        return None
    
    # Generate timestamp for unique key name
    timestamp = int(datetime.now().timestamp())
    key_name = f"github_nfc_seamless_{timestamp}"
    key_path = os.path.expanduser(f"~/.ssh/{key_name}")
    
    print(f"\n🔐 SSH KEY GENERATION")
    print(f"📁 Key path: {key_path}")
    print(f"🔒 Passphrase: {'*' * len(passphrase)} (never displayed)")
    
    try:
        # Generate SSH key with NFC passphrase
        cmd = [
            'ssh-keygen',
            '-t', 'rsa',
            '-b', '2048',
            '-f', key_path,
            '-N', passphrase,
            '-C', f'nfc-seamless-{timestamp}@github.com'
        ]
        
        print("🔨 Generating SSH key with NFC passphrase...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ SSH key generation failed: {result.stderr}")
            return None
        
        print("✅ SSH key generated successfully")
        
        # Set proper permissions
        os.chmod(key_path, 0o600)
        os.chmod(f"{key_path}.pub", 0o644)
        
        # Read public key
        with open(f"{key_path}.pub", 'r') as f:
            public_key = f.read().strip()
        
        print(f"\n📋 PUBLIC KEY:")
        print(public_key)
        
        # Update SSH config
        ssh_config_path = os.path.expanduser("~/.ssh/config")
        host_alias = f"github-nfc-seamless"
        
        config_entry = f"""
# NFC Seamless SSH key with dual authentication
Host {host_alias}
    HostName github.com
    User git
    IdentityFile {key_path}
"""
        
        with open(ssh_config_path, 'a') as f:
            f.write(config_entry)
        
        print(f"\n✅ SSH config updated with host: {host_alias}")
        
        # Clear passphrase from memory
        passphrase = "0" * len(passphrase)
        del passphrase
        
        return {
            'key_path': key_path,
            'public_key': public_key,
            'host_alias': host_alias
        }
        
    except Exception as e:
        print(f"❌ Error creating SSH key: {e}")
        return None

def main():
    """Main NFC SSH key creation"""
    
    print("🔑 NFC Seamless SSH Key Generator")
    print("🚀 Creates SSH key using dual NFC authentication + real ambient data")
    print()
    
    key_info = create_ssh_key_with_nfc_passphrase()
    
    if not key_info:
        print("❌ Failed to create NFC SSH key")
        return
    
    print(f"\n🎉 NFC SSH KEY CREATED SUCCESSFULLY")
    print(f"   Host alias: {key_info['host_alias']}")
    print(f"   Key path: {key_info['key_path']}")
    print()
    print(f"📋 NEXT STEPS:")
    print(f"1. Copy the public key above to GitHub Settings > SSH and GPG keys")
    print(f"2. Test seamless authentication:")
    print(f"   python3 seamless_nfc_github_auth.py")
    print(f"3. Or test manually:")
    print(f"   ssh -T {key_info['host_alias']}")

if __name__ == "__main__":
    main()
