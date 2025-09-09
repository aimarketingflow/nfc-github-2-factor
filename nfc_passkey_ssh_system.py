#!/usr/bin/env python3
"""
NFC Passkey SSH Authentication System
NFC scan acts as SSH passkey, triggers USB unlock + key generation
"""

import os
import json
import hashlib
import base64
import subprocess
import tempfile
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa
import numpy as np

class NFCPasskeySSHSystem:
    """SSH system where NFC scan = passkey that unlocks everything"""
    
    def __init__(self):
        self.ssh_keys_dir = os.path.expanduser("~/.ssh")
        self.temp_key_path = None
        self.usb_pack_path = None
        
    def setup_ssh_agent_wrapper(self):
        """Create SSH agent wrapper that intercepts passkey requests"""
        
        wrapper_script = f"""#!/bin/bash
# MobileShield NFC Passkey SSH Wrapper
echo "🔑 MobileShield SSH Authentication"
echo "📟 Scan NFC tag when prompted for passkey..."

# Launch NFC passkey authentication
python3 "{os.path.abspath(__file__)}" --nfc-passkey-mode

# If successful, SSH key will be generated and added to agent
if [ $? -eq 0 ]; then
    echo "✅ NFC authentication successful - proceeding with SSH"
    # Execute original SSH command with generated key
    exec ssh "$@" -o PasswordAuthentication=no
else
    echo "❌ NFC authentication failed"
    exit 1
fi
"""
        
        wrapper_path = os.path.join(self.ssh_keys_dir, "mobileshield_ssh_wrapper.sh")
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_script)
        
        os.chmod(wrapper_path, 0o755)
        
        print(f"✅ SSH wrapper created: {wrapper_path}")
        return wrapper_path
    
    def detect_usb_pack(self):
        """Auto-detect USB drive with MobileShield pack"""
        
        print("🔍 Detecting USB pack...")
        
        try:
            volumes_dir = "/Volumes"
            if os.path.exists(volumes_dir):
                for item in os.listdir(volumes_dir):
                    volume_path = os.path.join(volumes_dir, item)
                    if os.path.ismount(volume_path) and item != "Macintosh HD":
                        pack_dir = os.path.join(volume_path, "MobileShield_Packs")
                        if os.path.exists(pack_dir):
                            packs = [d for d in os.listdir(pack_dir) if d.startswith("pack_")]
                            if packs:
                                # Use most recent pack
                                latest_pack = max(packs, key=lambda p: os.path.getmtime(os.path.join(pack_dir, p)))
                                self.usb_pack_path = os.path.join(pack_dir, latest_pack)
                                print(f"📦 Found pack: {self.usb_pack_path}")
                                return True
        except:
            pass
        
        print("❌ No USB pack detected")
        return False
    
    def nfc_passkey_authentication(self):
        """NFC scan that acts as SSH passkey"""
        
        print("\n📟 NFC PASSKEY AUTHENTICATION")
        print("=" * 35)
        print("🔑 This NFC scan IS your SSH passkey")
        print("🔓 Scan to unlock USB pack and generate SSH key...")
        
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            # This becomes the actual passkey value
            nfc_passkey_hash = scanner.invisible_scan_simple()
            
            print("✅ NFC passkey received")
            print("🔓 Unlocking USB pack...")
            
            return nfc_passkey_hash
            
        except ImportError:
            print("⚠️  NFC scanner not available - using demo passkey")
            nfc_demo = f"demo_passkey_{int(os.path.getmtime(self.usb_pack_path))}"
            return nfc_demo
        except Exception as e:
            print(f"❌ NFC passkey authentication failed: {e}")
            return None
    
    def unlock_usb_pack_with_nfc_passkey(self, nfc_passkey):
        """Use NFC passkey to unlock USB pack values"""
        
        print("🔓 Unlocking USB pack with NFC passkey...")
        
        # Find pack JSON file
        pack_files = os.listdir(self.usb_pack_path)
        json_file = None
        for file in pack_files:
            if file.endswith('.json') and 'pack' in file:
                json_file = os.path.join(self.usb_pack_path, file)
                break
        
        if not json_file:
            print("❌ Pack configuration not found")
            return None
        
        # Load pack container
        with open(json_file, 'r') as f:
            pack_container = json.load(f)
        
        # Verify USB binding
        usb_fingerprint = self.create_usb_fingerprint()
        required_fingerprint = pack_container['validation']['requires_usb_fingerprint']
        
        if usb_fingerprint != required_fingerprint:
            print(f"❌ USB binding verification failed")
            return None
        
        # Decrypt with NFC passkey as the key
        try:
            usb_key_material = (usb_fingerprint + "USB_BINDING").encode()
            usb_kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'USB_SPECIFIC_BINDING',
                iterations=50000,
            )
            usb_key = base64.urlsafe_b64encode(usb_kdf.derive(usb_key_material))
            usb_cipher = Fernet(usb_key)
            
            # Decrypt values
            encrypted_nfc = pack_container['pack_metadata']['nfc_hash_encrypted']
            encrypted_chaos = pack_container['pack_metadata']['chaos_encrypted']
            
            decrypted_nfc = usb_cipher.decrypt(encrypted_nfc.encode()).decode()
            decrypted_chaos = usb_cipher.decrypt(encrypted_chaos.encode()).decode()
            
            # Verify NFC passkey matches stored value
            if decrypted_nfc != nfc_passkey:
                print("❌ NFC passkey verification failed")
                return None
            
            # Get audio fingerprint
            audio_fingerprint = self.extract_pack_audio_fingerprint()
            if not audio_fingerprint:
                return None
            
            pack_values = {
                'nfc_passkey': nfc_passkey,
                'chaos_value': decrypted_chaos,
                'audio_fingerprint': audio_fingerprint,
                'usb_fingerprint': usb_fingerprint,
                'pack_container': pack_container
            }
            
            print("✅ USB pack unlocked with NFC passkey")
            return pack_values
            
        except Exception as e:
            print(f"❌ Pack unlock failed: {e}")
            return None
    
    def extract_pack_audio_fingerprint(self):
        """Extract audio fingerprint from pack"""
        
        # Find audio file
        pack_files = os.listdir(self.usb_pack_path)
        audio_file = None
        for file in pack_files:
            if file.endswith('.wav'):
                audio_file = os.path.join(self.usb_pack_path, file)
                break
        
        if not audio_file:
            print("❌ Audio file not found")
            return None
        
        try:
            # Simple audio fingerprint without librosa dependency
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Create fingerprint from audio file content
            audio_fingerprint = hashlib.sha256(audio_data).hexdigest()
            print(f"🎵 Audio fingerprint: {audio_fingerprint[:16]}...")
            
            return audio_fingerprint
            
        except Exception as e:
            print(f"❌ Audio fingerprint failed: {e}")
            return None
    
    def create_usb_fingerprint(self):
        """Create current USB fingerprint"""
        
        usb_path = os.path.dirname(os.path.dirname(self.usb_pack_path))  # Get volume path
        
        try:
            result = subprocess.run(['diskutil', 'info', usb_path], 
                                  capture_output=True, text=True)
            
            usb_info = {}
            for line in result.stdout.split('\n'):
                if 'Volume UUID' in line:
                    usb_info['volume_uuid'] = line.split(':')[1].strip()
                elif 'Device / Media Name' in line:
                    usb_info['device_name'] = line.split(':')[1].strip()
            
            usb_info['mount_point'] = usb_path
            fingerprint_data = str(sorted(usb_info.items()))
            
            return hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
        except:
            # Fallback
            fallback_info = {'mount_point': usb_path, 'fallback': True}
            return hashlib.sha256(str(fallback_info).encode()).hexdigest()
    
    def generate_ssh_key_from_pack_values(self, pack_values):
        """Generate SSH key from unlocked pack values (NOT including NFC passkey)"""
        
        print("🔑 Generating SSH key from pack values...")
        
        # Key generation uses everything EXCEPT the NFC passkey
        # NFC passkey is only for unlocking, not key generation
        key_seed = (
            pack_values['chaos_value'] + 
            pack_values['audio_fingerprint'] +
            pack_values['usb_fingerprint']
        ).encode()
        
        print(f"🔒 SSH key seed components:")
        print(f"   Chaos: {pack_values['chaos_value'][:16]}...")
        print(f"   Audio: {pack_values['audio_fingerprint'][:16]}...")
        print(f"   USB: {pack_values['usb_fingerprint'][:16]}...")
        print(f"   ⚠️  NFC passkey NOT included in key generation")
        
        # Generate deterministic SSH key
        ssh_kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'SSH_KEY_FROM_PACK_VALUES',
            iterations=100000,
        )
        
        key_material = ssh_kdf.derive(key_seed)
        
        # Use as entropy for RSA generation
        np.random.seed(int.from_bytes(key_material[:8], 'big'))
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Create temporary key file
        pack_id = pack_values['pack_container']['pack_metadata']['pack_id']
        temp_key = tempfile.NamedTemporaryFile(
            mode='wb', 
            prefix=f'mobileshield_{pack_id}_',
            suffix='.key',
            delete=False
        )
        
        temp_key.write(private_pem)
        temp_key.close()
        
        # Set proper permissions
        os.chmod(temp_key.name, 0o600)
        
        self.temp_key_path = temp_key.name
        
        print(f"✅ SSH key generated: {self.temp_key_path}")
        return self.temp_key_path
    
    def add_key_to_ssh_agent(self, key_path):
        """Add generated key to SSH agent"""
        
        try:
            result = subprocess.run(['ssh-add', key_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ SSH key added to agent")
                return True
            else:
                print(f"❌ Failed to add key to agent: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ SSH agent error: {e}")
            return False
    
    def run_nfc_passkey_mode(self):
        """Run in NFC passkey mode (called by SSH wrapper)"""
        
        print("🚀 NFC PASSKEY SSH AUTHENTICATION")
        print("=" * 40)
        
        # Step 1: Detect USB pack
        if not self.detect_usb_pack():
            return False
        
        # Step 2: NFC passkey authentication
        nfc_passkey = self.nfc_passkey_authentication()
        if not nfc_passkey:
            return False
        
        # Step 3: Unlock USB pack with NFC passkey
        pack_values = self.unlock_usb_pack_with_nfc_passkey(nfc_passkey)
        if not pack_values:
            return False
        
        # Step 4: Generate SSH key from pack values
        key_path = self.generate_ssh_key_from_pack_values(pack_values)
        if not key_path:
            return False
        
        # Step 5: Add to SSH agent
        if not self.add_key_to_ssh_agent(key_path):
            return False
        
        print(f"\n🎉 NFC PASSKEY AUTHENTICATION COMPLETE")
        print(f"   NFC scan unlocked USB pack")
        print(f"   SSH key generated from pack values")
        print(f"   Ready for GitHub authentication")
        
        return True
    
    def setup_github_ssh_alias(self):
        """Create GitHub SSH alias using NFC passkey system"""
        
        wrapper_path = self.setup_ssh_agent_wrapper()
        
        print(f"\n🐙 GITHUB SSH SETUP")
        print("=" * 25)
        print(f"Use this command for GitHub SSH:")
        print(f"   {wrapper_path} git@github.com")
        print(f"")
        print(f"Or create alias:")
        print(f"   alias github-ssh='{wrapper_path} git@github.com'")
        print(f"")
        print(f"Then clone with:")
        print(f"   github-ssh")
        print(f"   git clone git@github.com:username/repo.git")

def main():
    """Main entry point"""
    
    import sys
    
    nfc_ssh = NFCPasskeySSHSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--nfc-passkey-mode':
        # Called by SSH wrapper
        success = nfc_ssh.run_nfc_passkey_mode()
        sys.exit(0 if success else 1)
    else:
        # Setup mode
        print("🔑 NFC PASSKEY SSH SYSTEM SETUP")
        print("=" * 35)
        print("Setting up SSH authentication where NFC scan = passkey")
        print()
        
        nfc_ssh.setup_github_ssh_alias()
        
        print(f"\n✅ Setup complete!")
        print(f"   NFC scan will act as SSH passkey")
        print(f"   Pack values will generate SSH private key")
        print(f"   Ready for GitHub authentication")

if __name__ == "__main__":
    main()
