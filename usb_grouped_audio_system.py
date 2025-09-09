#!/usr/bin/env python3
"""
USB Grouped Audio Authentication System
Multiple encryption packs with grouped ambient audio files
"""

import hashlib
import json
import time
import os
import shutil
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class USBGroupedAudioSystem:
    """Manage grouped ambient audio encryption packs on USB"""
    
    def __init__(self, usb_path="/Volumes/USB_AUTH"):
        self.usb_path = usb_path
        self.local_backup_dir = "local_audio_backup"
        self.encryption_packs_dir = "encryption_packs"
        self.group_manifest_file = "audio_group_manifest.json"
        
        # Create directories
        for directory in [self.local_backup_dir, self.encryption_packs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def create_audio_group_pack(self, pack_id, nfc_hash, chaos_value):
        """Create a new encryption pack with grouped audio"""
        
        print(f"\n🎵 CREATING ENCRYPTION PACK: {pack_id}")
        print("=" * 50)
        
        # 1. Record new ambient audio for this pack
        print("🎤 Recording ambient audio for this encryption pack...")
        from song_recorder import SongRecorder
        recorder = SongRecorder()
        
        audio_filename = f"ambient_pack_{pack_id}_{int(time.time())}.wav"
        audio_file = recorder.record_song(audio_filename)
        
        if not audio_file:
            print("❌ Audio recording failed")
            return None
        
        # 2. Create audio fingerprint for grouping
        audio_fingerprint = self.create_audio_fingerprint(audio_file)
        
        # 3. Create pack metadata with hidden mappings
        pack_metadata = {
            'pack_id': pack_id,
            'creation_time': time.time(),
            'audio_file': audio_filename,
            'audio_fingerprint': audio_fingerprint,
            'group_signature': self.create_group_signature(pack_id, audio_fingerprint),
            # Hidden until unlock
            'nfc_hash_encrypted': self.encrypt_nfc_mapping(nfc_hash, audio_fingerprint),
            'chaos_value_encrypted': self.encrypt_chaos_mapping(chaos_value, audio_fingerprint),
            'unlock_required': True
        }
        
        # 4. Create encrypted pack container
        pack_container = self.create_pack_container(pack_metadata, audio_file, nfc_hash, chaos_value)
        
        # 5. Save to local backup
        local_pack_dir = os.path.join(self.local_backup_dir, f"pack_{pack_id}")
        if not os.path.exists(local_pack_dir):
            os.makedirs(local_pack_dir)
        
        local_pack_file = os.path.join(local_pack_dir, f"encryption_pack_{pack_id}.json")
        with open(local_pack_file, 'w') as f:
            json.dump(pack_container, f, indent=2)
        
        # 6. Copy audio to local backup
        local_audio_file = os.path.join(local_pack_dir, audio_filename)
        shutil.copy2(audio_file, local_audio_file)
        
        print(f"✅ Encryption pack created: {pack_id}")
        print(f"   Local backup: {local_pack_file}")
        print(f"   Audio backup: {local_audio_file}")
        
        return pack_container, local_pack_file
    
    def copy_pack_to_usb(self, pack_container, pack_id):
        """Copy encryption pack to USB drive"""
        
        print(f"\n💾 COPYING PACK TO USB: {pack_id}")
        print("-" * 30)
        
        # Check if USB is available
        if not os.path.exists(self.usb_path):
            print(f"❌ USB drive not found at {self.usb_path}")
            return False
        
        # Create USB directory structure
        usb_packs_dir = os.path.join(self.usb_path, "encryption_packs")
        if not os.path.exists(usb_packs_dir):
            os.makedirs(usb_packs_dir)
        
        usb_pack_dir = os.path.join(usb_packs_dir, f"pack_{pack_id}")
        if not os.path.exists(usb_pack_dir):
            os.makedirs(usb_pack_dir)
        
        # Copy pack container
        usb_pack_file = os.path.join(usb_pack_dir, f"encryption_pack_{pack_id}.json")
        with open(usb_pack_file, 'w') as f:
            json.dump(pack_container, f, indent=2)
        
        # Copy audio file
        local_audio_file = os.path.join(self.local_backup_dir, f"pack_{pack_id}", pack_container['pack_metadata']['audio_file'])
        usb_audio_file = os.path.join(usb_pack_dir, pack_container['pack_metadata']['audio_file'])
        
        if os.path.exists(local_audio_file):
            shutil.copy2(local_audio_file, usb_audio_file)
            print(f"✅ Audio copied to USB: {pack_container['pack_metadata']['audio_file']}")
        
        # Update USB group manifest
        self.update_usb_group_manifest(pack_id, pack_container['pack_metadata'])
        
        print(f"✅ Pack {pack_id} copied to USB successfully")
        return True
    
    def create_audio_fingerprint(self, audio_file):
        """Create unique fingerprint for audio file"""
        
        try:
            # Read audio file and create content hash
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # Create multiple fingerprint layers
            fingerprint = {
                'content_hash': hashlib.sha256(audio_data).hexdigest(),
                'file_size': len(audio_data),
                'creation_time': os.path.getctime(audio_file),
                'file_name_hash': hashlib.sha256(os.path.basename(audio_file).encode()).hexdigest()[:16]
            }
            
            return hashlib.sha256(str(fingerprint).encode()).hexdigest()
            
        except Exception as e:
            print(f"   Audio fingerprint error: {e}")
            return hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    def create_group_signature(self, pack_id, audio_fingerprint):
        """Create signature for pack grouping verification"""
        
        group_data = {
            'pack_id': pack_id,
            'audio_fingerprint': audio_fingerprint,
            'creation_timestamp': time.time()
        }
        
        return hashlib.sha256(str(group_data).encode()).hexdigest()
    
    def encrypt_nfc_mapping(self, nfc_hash, audio_fingerprint):
        """Encrypt NFC hash using audio fingerprint"""
        
        key_material = (audio_fingerprint + "NFC_MAPPING").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'NFC_AUDIO_MAPPING',
            iterations=50000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        cipher = Fernet(key)
        
        return cipher.encrypt(nfc_hash.encode()).decode()
    
    def encrypt_chaos_mapping(self, chaos_value, audio_fingerprint):
        """Encrypt chaos value using audio fingerprint"""
        
        key_material = (audio_fingerprint + "CHAOS_MAPPING").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'CHAOS_AUDIO_MAPPING',
            iterations=50000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        cipher = Fernet(key)
        
        return cipher.encrypt(str(chaos_value).encode()).decode()
    
    def create_pack_container(self, pack_metadata, audio_file, nfc_hash, chaos_value):
        """Create complete encryption pack container"""
        
        # Create master encryption key from all factors
        master_key_material = (nfc_hash + str(chaos_value) + pack_metadata['audio_fingerprint']).encode()
        master_kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'MASTER_PACK_ENCRYPTION',
            iterations=100000,
        )
        master_key = base64.urlsafe_b64encode(master_kdf.derive(master_key_material))
        master_cipher = Fernet(master_key)
        
        # Sample credentials to encrypt
        credentials = {
            'pack_credentials': f'encrypted_data_for_pack_{pack_metadata["pack_id"]}',
            'access_tokens': f'token_set_{pack_metadata["pack_id"]}_secure',
            'encryption_keys': f'key_vault_{pack_metadata["pack_id"]}_protected'
        }
        
        encrypted_credentials = master_cipher.encrypt(json.dumps(credentials).encode())
        
        pack_container = {
            'container_version': '1.0',
            'pack_metadata': pack_metadata,
            'encrypted_credentials': base64.b64encode(encrypted_credentials).decode(),
            'grouping_required': True,
            'unlock_instructions': {
                'step_1': 'Verify audio group integrity',
                'step_2': 'Scan NFC to unlock mappings', 
                'step_3': 'Provide chaos value for decryption'
            }
        }
        
        return pack_container
    
    def update_usb_group_manifest(self, pack_id, pack_metadata):
        """Update USB group manifest for pack recognition"""
        
        manifest_file = os.path.join(self.usb_path, self.group_manifest_file)
        
        # Load existing manifest
        if os.path.exists(manifest_file):
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {
                'manifest_version': '1.0',
                'creation_time': time.time(),
                'audio_groups': {},
                'group_count': 0
            }
        
        # Add pack to manifest
        manifest['audio_groups'][pack_id] = {
            'pack_id': pack_id,
            'audio_fingerprint': pack_metadata['audio_fingerprint'],
            'group_signature': pack_metadata['group_signature'],
            'creation_time': pack_metadata['creation_time'],
            'requires_grouping': True
        }
        
        manifest['group_count'] = len(manifest['audio_groups'])
        manifest['last_updated'] = time.time()
        
        # Save manifest
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ USB group manifest updated with pack {pack_id}")
    
    def verify_audio_group_integrity(self, usb_path=None):
        """Verify that audio files form valid groups on USB"""
        
        if usb_path is None:
            usb_path = self.usb_path
        
        print(f"\n🔍 VERIFYING AUDIO GROUP INTEGRITY")
        print("-" * 40)
        
        manifest_file = os.path.join(usb_path, self.group_manifest_file)
        
        if not os.path.exists(manifest_file):
            print("❌ No group manifest found on USB")
            return False, []
        
        # Load manifest
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        verified_groups = []
        
        for pack_id, group_info in manifest['audio_groups'].items():
            pack_dir = os.path.join(usb_path, "encryption_packs", f"pack_{pack_id}")
            
            if not os.path.exists(pack_dir):
                print(f"❌ Pack directory missing: {pack_id}")
                continue
            
            # Verify audio file exists and matches fingerprint
            pack_file = os.path.join(pack_dir, f"encryption_pack_{pack_id}.json")
            
            if os.path.exists(pack_file):
                with open(pack_file, 'r') as f:
                    pack_data = json.load(f)
                
                audio_file = os.path.join(pack_dir, pack_data['pack_metadata']['audio_file'])
                
                if os.path.exists(audio_file):
                    current_fingerprint = self.create_audio_fingerprint(audio_file)
                    
                    if current_fingerprint == group_info['audio_fingerprint']:
                        print(f"✅ Pack {pack_id}: Audio group verified")
                        verified_groups.append(pack_id)
                    else:
                        print(f"❌ Pack {pack_id}: Audio fingerprint mismatch")
                else:
                    print(f"❌ Pack {pack_id}: Audio file missing")
            else:
                print(f"❌ Pack {pack_id}: Pack file missing")
        
        print(f"\n📊 Group Verification Results:")
        print(f"   Total packs: {len(manifest['audio_groups'])}")
        print(f"   Verified: {len(verified_groups)}")
        
        return len(verified_groups) > 0, verified_groups
    
    def unlock_pack_with_nfc(self, pack_id, usb_path=None):
        """Unlock specific pack using NFC authentication"""
        
        if usb_path is None:
            usb_path = self.usb_path
        
        print(f"\n🔐 UNLOCKING PACK: {pack_id}")
        print("-" * 30)
        
        # Verify group integrity first
        integrity_ok, verified_groups = self.verify_audio_group_integrity(usb_path)
        
        if not integrity_ok or pack_id not in verified_groups:
            print(f"❌ Pack {pack_id} failed group integrity check")
            return None
        
        # Load pack data
        pack_dir = os.path.join(usb_path, "encryption_packs", f"pack_{pack_id}")
        pack_file = os.path.join(pack_dir, f"encryption_pack_{pack_id}.json")
        
        with open(pack_file, 'r') as f:
            pack_data = json.load(f)
        
        # NFC authentication
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            print(f"📟 Scan NFC to unlock pack {pack_id}...")
            nfc_hash = scanner.invisible_scan_simple()
            
            # Decrypt NFC mapping
            audio_fingerprint = pack_data['pack_metadata']['audio_fingerprint']
            decrypted_nfc = self.decrypt_nfc_mapping(
                pack_data['pack_metadata']['nfc_hash_encrypted'], 
                audio_fingerprint
            )
            
            if decrypted_nfc == nfc_hash:
                print("✅ NFC authentication successful")
                print(f"🔓 Pack {pack_id} unlocked and ready for use")
                return pack_data
            else:
                print("❌ NFC authentication failed")
                return None
                
        except ImportError:
            print("⚠️  NFC scanner not available - using demo mode")
            return pack_data  # Demo mode
        except Exception as e:
            print(f"❌ Unlock error: {e}")
            return None
    
    def decrypt_nfc_mapping(self, encrypted_nfc, audio_fingerprint):
        """Decrypt NFC mapping using audio fingerprint"""
        
        key_material = (audio_fingerprint + "NFC_MAPPING").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'NFC_AUDIO_MAPPING',
            iterations=50000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))
        cipher = Fernet(key)
        
        return cipher.decrypt(encrypted_nfc.encode()).decode()

def main():
    """Test USB grouped audio system"""
    
    print("💾 USB GROUPED AUDIO AUTHENTICATION SYSTEM")
    print("Testing hardware setup with multiple encryption packs")
    print()
    
    system = USBGroupedAudioSystem()
    
    while True:
        print("\n" + "=" * 50)
        print("   USB GROUPED AUDIO MENU")
        print("=" * 50)
        print("1. Create new encryption pack")
        print("2. Copy pack to USB")
        print("3. Verify USB audio groups")
        print("4. Unlock pack with NFC")
        print("5. List local packs")
        print("6. Exit")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            pack_id = input("Enter pack ID: ").strip()
            if not pack_id:
                pack_id = f"pack_{int(time.time())}"
            
            print("\n📟 Scan NFC for pack binding...")
            try:
                from invisible_nfc_scanner import InvisibleNFCScanner
                scanner = InvisibleNFCScanner()
                nfc_hash = scanner.invisible_scan_simple()
            except:
                nfc_hash = f"demo_nfc_{pack_id}"
                print("⚠️  Using demo NFC hash")
            
            # Demo chaos value
            chaos_value = f"chaos_{int(time.time())}"
            
            pack_container, pack_file = system.create_audio_group_pack(pack_id, nfc_hash, chaos_value)
            
            if pack_container:
                print(f"\n🎉 Pack {pack_id} created successfully!")
        
        elif choice == '2':
            pack_id = input("Enter pack ID to copy to USB: ").strip()
            
            # Load pack from local backup
            local_pack_file = os.path.join(system.local_backup_dir, f"pack_{pack_id}", f"encryption_pack_{pack_id}.json")
            
            if os.path.exists(local_pack_file):
                with open(local_pack_file, 'r') as f:
                    pack_container = json.load(f)
                
                system.copy_pack_to_usb(pack_container, pack_id)
            else:
                print(f"❌ Local pack {pack_id} not found")
        
        elif choice == '3':
            integrity_ok, verified_groups = system.verify_audio_group_integrity()
            
            if integrity_ok:
                print(f"✅ USB audio groups verified: {verified_groups}")
            else:
                print("❌ USB audio group verification failed")
        
        elif choice == '4':
            pack_id = input("Enter pack ID to unlock: ").strip()
            unlocked_pack = system.unlock_pack_with_nfc(pack_id)
            
            if unlocked_pack:
                print(f"🎉 Pack {pack_id} unlocked successfully!")
                print("   Credentials available for use")
        
        elif choice == '5':
            print("\n📁 Local Encryption Packs:")
            if os.path.exists(system.local_backup_dir):
                for item in os.listdir(system.local_backup_dir):
                    if item.startswith('pack_'):
                        pack_id = item.replace('pack_', '')
                        print(f"   📦 {pack_id}")
            else:
                print("   No local packs found")
        
        elif choice == '6':
            print("\n👋 USB grouped audio system offline")
            break
        
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
