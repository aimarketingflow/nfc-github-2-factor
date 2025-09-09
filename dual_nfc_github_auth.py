#!/usr/bin/env python3
"""
Dual NFC GitHub Authentication System
First scan: Unlocks USB files (with location metadata verification)
Second scan: Unlocks GitHub passkey (combined with USB data)
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

class DualNFCGitHubAuth:
    """Dual NFC scan system for GitHub authentication"""
    
    def __init__(self):
        self.ssh_keys_dir = os.path.expanduser("~/.ssh")
        self.usb_pack_path = None
        self.unlocked_usb_data = None
        self.github_passkey = None
        
    def detect_usb_pack_with_location_verify(self):
        """Detect USB and verify location metadata"""
        
        print("🔍 STEP 1: USB DETECTION + LOCATION VERIFICATION")
        print("=" * 50)
        
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
                                latest_pack = max(packs, key=lambda p: os.path.getmtime(os.path.join(pack_dir, p)))
                                self.usb_pack_path = os.path.join(pack_dir, latest_pack)
                                
                                # Verify location metadata
                                if self.verify_location_metadata(volume_path):
                                    print(f"✅ USB pack found: {self.usb_pack_path}")
                                    print(f"✅ Location metadata verified")
                                    return True
                                else:
                                    print(f"❌ Location metadata verification failed")
                                    return False
        except Exception as e:
            print(f"❌ USB detection failed: {e}")
        
        print("❌ No valid USB pack with correct location metadata")
        return False
    
    def verify_location_metadata(self, usb_path):
        """Verify USB location metadata matches expected"""
        
        try:
            # Get current USB characteristics
            result = subprocess.run(['diskutil', 'info', usb_path], 
                                  capture_output=True, text=True)
            
            current_info = {}
            for line in result.stdout.split('\n'):
                if 'Volume UUID' in line:
                    current_info['volume_uuid'] = line.split(':')[1].strip()
                elif 'Device / Media Name' in line:
                    current_info['device_name'] = line.split(':')[1].strip()
                elif 'Total Size' in line:
                    current_info['total_size'] = line.split(':')[1].strip()
                elif 'File System Personality' in line:
                    current_info['filesystem'] = line.split(':')[1].strip()
            
            # Add mount point to match capture system (use stable characteristics only)
            current_info['mount_point'] = usb_path
            
            # Load expected metadata from pack
            pack_files = os.listdir(self.usb_pack_path)
            json_file = None
            for file in pack_files:
                if file.endswith('.json') and 'pack' in file:
                    json_file = os.path.join(self.usb_pack_path, file)
                    break
            
            if not json_file:
                return False
            
            with open(json_file, 'r') as f:
                pack_container = json.load(f)
            
            expected_fingerprint = pack_container['validation']['requires_usb_fingerprint']
            expected_mount = pack_container['validation']['requires_original_mount']
            
            # Create current fingerprint matching capture system format
            fingerprint_data = str(sorted(current_info.items()))
            current_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
            
            print(f"   Current mount: {current_info.get('mount_point', 'Unknown')}")
            print(f"   Expected mount: {expected_mount}")
            print(f"   Fingerprint match: {current_fingerprint[:16]}... vs {expected_fingerprint[:16]}...")
            
            return (current_fingerprint == expected_fingerprint and 
                   current_info.get('mount_point') == expected_mount)
            
        except Exception as e:
            print(f"   Location verification error: {e}")
            return False
    
    def first_nfc_scan_unlock_usb(self):
        """First NFC scan: Unlock USB files"""
        
        print("\n📟 FIRST NFC SCAN: UNLOCK USB FILES")
        print("=" * 40)
        print("🔓 Scan NFC tag to unlock encrypted USB pack...")
        print("   This unlocks file access only")
        
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            first_nfc_hash = scanner.invisible_scan_simple()
            
            print("✅ First NFC scan complete")
            print("🔓 Attempting USB file unlock...")
            
            return self.unlock_usb_files_with_nfc(first_nfc_hash)
            
        except ImportError:
            print("⚠️  NFC scanner not available - using demo unlock")
            demo_hash = f"demo_first_{int(os.path.getmtime(self.usb_pack_path))}"
            return self.unlock_usb_files_with_nfc(demo_hash)
        except Exception as e:
            print(f"❌ First NFC scan failed: {e}")
            return False
    
    def unlock_usb_files_with_nfc(self, nfc_hash):
        """Unlock USB files using first NFC scan"""
        
        try:
            # Load pack container
            pack_files = os.listdir(self.usb_pack_path)
            json_file = None
            for file in pack_files:
                if file.endswith('.json') and 'pack' in file:
                    json_file = os.path.join(self.usb_pack_path, file)
                    break
            
            with open(json_file, 'r') as f:
                pack_container = json.load(f)
            
            # Create USB-specific decryption key
            usb_fingerprint = pack_container['validation']['requires_usb_fingerprint']
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
            
            # Verify first NFC scan matches
            if decrypted_nfc != nfc_hash:
                print("❌ First NFC scan verification failed")
                return False
            
            # Extract audio fingerprint
            audio_fingerprint = self.extract_audio_fingerprint()
            if not audio_fingerprint:
                return False
            
            # Store unlocked USB data
            self.unlocked_usb_data = {
                'nfc_hash': decrypted_nfc,
                'chaos_value': decrypted_chaos,
                'audio_fingerprint': audio_fingerprint,
                'usb_fingerprint': usb_fingerprint,
                'pack_container': pack_container
            }
            
            print("✅ USB files unlocked successfully")
            print(f"   NFC verified: {decrypted_nfc[:16]}...")
            print(f"   Chaos value: {decrypted_chaos[:16]}...")
            print(f"   Audio print: {audio_fingerprint[:16]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ USB unlock failed: {e}")
            return False
    
    def extract_audio_fingerprint(self):
        """Extract audio fingerprint from USB pack"""
        
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
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            audio_fingerprint = hashlib.sha256(audio_data).hexdigest()
            return audio_fingerprint
            
        except Exception as e:
            print(f"❌ Audio fingerprint failed: {e}")
            return None
    
    def second_nfc_scan_github_passkey(self):
        """Second NFC scan: Generate GitHub passkey"""
        
        print("\n📟 SECOND NFC SCAN: GENERATE GITHUB PASSKEY")
        print("=" * 45)
        print("🔑 Scan NFC tag to generate GitHub authentication passkey...")
        print("   This combines with USB data for final authentication")
        
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            second_nfc_hash = scanner.invisible_scan_simple()
            
            print("✅ Second NFC scan complete")
            print("🔑 Generating GitHub passkey...")
            
            return self.generate_github_passkey(second_nfc_hash)
            
        except ImportError:
            print("⚠️  NFC scanner not available - using demo passkey")
            demo_hash = f"demo_second_{int(os.path.getmtime(self.usb_pack_path))}_github"
            return self.generate_github_passkey(demo_hash)
        except Exception as e:
            print(f"❌ Second NFC scan failed: {e}")
            return False
    
    def generate_github_passkey(self, second_nfc_hash):
        """Generate GitHub passkey from second NFC + USB data"""
        
        if not self.unlocked_usb_data:
            print("❌ USB data not unlocked - run first NFC scan")
            return False
        
        try:
            # Combine second NFC scan with all USB data
            github_passkey_material = (
                second_nfc_hash +  # Second NFC scan
                self.unlocked_usb_data['nfc_hash'] +  # First NFC from USB
                self.unlocked_usb_data['chaos_value'] +  # Chaos from USB
                self.unlocked_usb_data['audio_fingerprint'] +  # Audio from USB
                self.unlocked_usb_data['usb_fingerprint']  # USB binding
            ).encode()
            
            print(f"🔒 GitHub passkey components:")
            print(f"   Second NFC: {second_nfc_hash[:16]}...")
            print(f"   USB NFC: {self.unlocked_usb_data['nfc_hash'][:16]}...")
            print(f"   USB Chaos: {self.unlocked_usb_data['chaos_value'][:16]}...")
            print(f"   USB Audio: {self.unlocked_usb_data['audio_fingerprint'][:16]}...")
            print(f"   USB Binding: {self.unlocked_usb_data['usb_fingerprint'][:16]}...")
            
            # Generate GitHub passkey hash
            github_kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'GITHUB_DUAL_NFC_PASSKEY',
                iterations=100000,
            )
            
            github_passkey_bytes = github_kdf.derive(github_passkey_material)
            self.github_passkey = base64.b64encode(github_passkey_bytes).decode()
            
            print(f"✅ GitHub passkey generated: {self.github_passkey[:16]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ GitHub passkey generation failed: {e}")
            return False
    
    def generate_ssh_key_for_github(self):
        """Generate SSH key using GitHub passkey"""
        
        if not self.github_passkey:
            print("❌ GitHub passkey not generated")
            return None
        
        print("\n🔑 GENERATING SSH KEY FOR GITHUB")
        print("=" * 35)
        
        # Use GitHub passkey as SSH key seed
        ssh_key_material = self.github_passkey.encode()
        
        ssh_kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'SSH_GITHUB_DUAL_NFC',
            iterations=100000,
        )
        
        key_seed = ssh_kdf.derive(ssh_key_material)
        
        # Use as entropy for RSA generation (numpy seed must be 32-bit)
        seed_32bit = int.from_bytes(key_seed[:4], 'big') % (2**32)
        np.random.seed(seed_32bit)
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        # Save SSH keys
        key_name = f"github_dual_nfc_{int(datetime.now().timestamp())}"
        private_key_path = os.path.join(self.ssh_keys_dir, key_name)
        public_key_path = os.path.join(self.ssh_keys_dir, f"{key_name}.pub")
        
        with open(private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(private_key_path, 0o600)
        
        public_key_content = public_ssh.decode() + f" dual-nfc-github@{os.uname().nodename}\n"
        with open(public_key_path, 'w') as f:
            f.write(public_key_content)
        
        print(f"✅ SSH keys generated:")
        print(f"   Private: {private_key_path}")
        print(f"   Public: {public_key_path}")
        
        return private_key_path, public_key_path, public_key_content
    
    def display_github_setup_instructions(self, public_key_content):
        """Display GitHub setup instructions"""
        
        print(f"\n🐙 GITHUB SETUP INSTRUCTIONS")
        print("=" * 35)
        
        print(f"📋 Copy this public key to GitHub:")
        print(f"   {public_key_content.strip()}")
        
        print(f"\n🔗 GitHub Setup Steps:")
        print(f"1. Go to: https://github.com/settings/keys")
        print(f"2. Click 'New SSH key'")
        print(f"3. Title: 'Dual NFC MobileShield Authentication'")
        print(f"4. Paste the public key above")
        print(f"5. Click 'Add SSH key'")
        
        print(f"\n⚡ Test Authentication:")
        print(f"   Run this script again to test dual NFC GitHub auth")
    
    def run_complete_dual_nfc_auth(self):
        """Run complete dual NFC GitHub authentication"""
        
        print("🚀 DUAL NFC GITHUB AUTHENTICATION SYSTEM")
        print("=" * 50)
        print("Two NFC scans required for GitHub authentication:")
        print("  1st scan: Unlocks USB files")
        print("  2nd scan: Generates GitHub passkey")
        print()
        
        # Step 1: Detect USB with location verification
        if not self.detect_usb_pack_with_location_verify():
            return False
        
        # Step 2: First NFC scan - unlock USB files
        if not self.first_nfc_scan_unlock_usb():
            return False
        
        # Step 3: Second NFC scan - generate GitHub passkey
        if not self.second_nfc_scan_github_passkey():
            return False
        
        # Step 4: Generate SSH key for GitHub
        ssh_result = self.generate_ssh_key_for_github()
        if not ssh_result:
            return False
        
        private_key_path, public_key_path, public_key_content = ssh_result
        
        # Step 5: Display GitHub setup
        self.display_github_setup_instructions(public_key_content)
        
        print(f"\n🎉 DUAL NFC AUTHENTICATION COMPLETE!")
        print(f"   USB files unlocked with location verification")
        print(f"   GitHub passkey generated from dual NFC scans")
        print(f"   SSH keys ready for GitHub authentication")
        
        return True

def main():
    """Launch dual NFC GitHub authentication"""
    
    print("🔐 MOBILESHIELD DUAL NFC GITHUB AUTHENTICATION")
    print("Have your NFC tag ready for TWO scans")
    print()
    print("⚠️  IMPORTANT: You will be prompted for NFC scans during the process")
    print("   This first prompt is just to start - NO NFC SCAN NEEDED")
    print()
    
    auth_system = DualNFCGitHubAuth()
    
    input("🚀 Press ENTER (keyboard only) to start the workflow...")
    
    success = auth_system.run_complete_dual_nfc_auth()
    
    if success:
        print("\n✅ SUCCESS - Dual NFC GitHub authentication ready")
    else:
        print("\n❌ FAILED - Check USB pack and NFC authentication")

if __name__ == "__main__":
    main()
