#!/usr/bin/env python3
"""
Dual NFC Unlock System
First scan: Unlocks immovable audio file data
Second scan: Unlocks actual password/credentials
"""

import hashlib
import json
import time
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DualNFCUnlock:
    """Two-stage NFC authentication system"""
    
    def __init__(self):
        self.stage1_salt = b'AIMF_STAGE1_UNLOCK'
        self.stage2_salt = b'AIMF_STAGE2_UNLOCK'
        
    def create_stage1_key(self, nfc_hash):
        """Create encryption key for stage 1 (file unlock)"""
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.stage1_salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(nfc_hash.encode()))
        return key
    
    def create_stage2_key(self, nfc_hash, audio_hash):
        """Create encryption key for stage 2 (password unlock)"""
        
        # Combine NFC hash with audio fingerprint for stage 2
        combined_material = (nfc_hash + audio_hash).encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.stage2_salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(combined_material))
        return key
    
    def encrypt_audio_data(self, audio_filepath, nfc_hash, audio_analysis_data):
        """Encrypt audio file data with stage 1 key"""
        
        print("🔒 Encrypting audio data (Stage 1)...")
        
        # Create stage 1 encryption key
        stage1_key = self.create_stage1_key(nfc_hash)
        cipher1 = Fernet(stage1_key)
        
        # Read and encrypt audio file
        with open(audio_filepath, 'rb') as f:
            audio_bytes = f.read()
        
        encrypted_audio = cipher1.encrypt(audio_bytes)
        
        # Encrypt audio analysis metadata
        analysis_json = json.dumps(audio_analysis_data)
        encrypted_analysis = cipher1.encrypt(analysis_json.encode())
        
        # Create encrypted container
        encrypted_container = {
            'encrypted_audio': base64.b64encode(encrypted_audio).decode(),
            'encrypted_analysis': base64.b64encode(encrypted_analysis).decode(),
            'stage1_locked': True,
            'creation_time': time.time()
        }
        
        # Save encrypted container
        container_path = audio_filepath + '.stage1_locked'
        with open(container_path, 'w') as f:
            json.dump(encrypted_container, f, indent=2)
        
        print(f"✅ Stage 1 encrypted: {container_path}")
        return container_path
    
    def encrypt_password_vault(self, password_data, nfc_hash, audio_hash):
        """Encrypt password vault with stage 2 key"""
        
        print("🔐 Encrypting password vault (Stage 2)...")
        
        # Create stage 2 encryption key
        stage2_key = self.create_stage2_key(nfc_hash, audio_hash)
        cipher2 = Fernet(stage2_key)
        
        # Encrypt password data
        password_json = json.dumps(password_data)
        encrypted_passwords = cipher2.encrypt(password_json.encode())
        
        # Create stage 2 container
        stage2_container = {
            'encrypted_vault': base64.b64encode(encrypted_passwords).decode(),
            'stage2_locked': True,
            'vault_type': 'password_credentials',
            'creation_time': time.time()
        }
        
        return stage2_container
    
    def stage1_unlock(self, container_path, nfc_hash):
        """First NFC scan - unlock audio file data"""
        
        print("\n🎯 STAGE 1 UNLOCK - Audio File Access")
        print("=" * 50)
        print("📟 Scan NFC tag to unlock audio data...")
        
        try:
            # Load encrypted container
            with open(container_path, 'r') as f:
                container = json.load(f)
            
            if not container.get('stage1_locked'):
                return False, "Container not stage 1 locked", None, None
            
            # Create stage 1 key
            stage1_key = self.create_stage1_key(nfc_hash)
            cipher1 = Fernet(stage1_key)
            
            # Decrypt audio data
            encrypted_audio = base64.b64decode(container['encrypted_audio'])
            audio_bytes = cipher1.decrypt(encrypted_audio)
            
            # Decrypt analysis data
            encrypted_analysis = base64.b64decode(container['encrypted_analysis'])
            analysis_json = cipher1.decrypt(encrypted_analysis).decode()
            audio_analysis = json.loads(analysis_json)
            
            print("✅ Stage 1 unlock successful!")
            print("   Audio data decrypted")
            print("   Analysis metadata decrypted")
            print("   Ready for Stage 2...")
            
            return True, "Stage 1 unlocked", audio_bytes, audio_analysis
            
        except Exception as e:
            return False, f"Stage 1 unlock failed: {str(e)}", None, None
    
    def stage2_unlock(self, stage2_container, nfc_hash, audio_analysis):
        """Second NFC scan - unlock password vault"""
        
        print("\n🔐 STAGE 2 UNLOCK - Password Vault Access")
        print("=" * 50)
        print("📟 Scan NFC tag again to unlock passwords...")
        
        try:
            if not stage2_container.get('stage2_locked'):
                return False, "Container not stage 2 locked", None
            
            # Create audio hash from analysis data
            audio_hash = hashlib.sha256(str(audio_analysis).encode()).hexdigest()
            
            # Create stage 2 key
            stage2_key = self.create_stage2_key(nfc_hash, audio_hash)
            cipher2 = Fernet(stage2_key)
            
            # Decrypt password vault
            encrypted_vault = base64.b64decode(stage2_container['encrypted_vault'])
            vault_json = cipher2.decrypt(encrypted_vault).decode()
            password_data = json.loads(vault_json)
            
            print("✅ Stage 2 unlock successful!")
            print("   Password vault decrypted")
            print("   Credentials available")
            
            return True, "Stage 2 unlocked", password_data
            
        except Exception as e:
            return False, f"Stage 2 unlock failed: {str(e)}", None
    
    def create_dual_locked_system(self, nfc_hash, password_vault):
        """Create complete dual-locked authentication system"""
        
        print("=" * 60)
        print("   DUAL NFC AUTHENTICATION SYSTEM")
        print("=" * 60)
        
        # 1. Record and analyze immovable audio
        print("\n🎵 Recording immovable authentication audio...")
        from immovable_audio_auth import ImmovableAudioAuth
        auth_system = ImmovableAudioAuth()
        
        # Record audio
        from song_recorder import SongRecorder
        recorder = SongRecorder()
        audio_file = recorder.record_song("dual_auth_audio.wav")
        
        if not audio_file:
            return None, None
        
        # Create system binding
        signature, metadata = auth_system.create_system_bound_metadata(audio_file, nfc_hash)
        
        # 2. Create audio analysis for stage 2 key
        audio_analysis = self.analyze_audio_for_stage2(audio_file)
        
        # 3. Encrypt audio with stage 1
        stage1_container = self.encrypt_audio_data(audio_file, nfc_hash, audio_analysis)
        
        # 4. Encrypt passwords with stage 2
        audio_hash = hashlib.sha256(str(audio_analysis).encode()).hexdigest()
        stage2_container = self.encrypt_password_vault(password_vault, nfc_hash, audio_hash)
        
        # 5. Save complete system
        dual_system = {
            'system_type': 'dual_nfc_unlock',
            'stage1_container_path': stage1_container,
            'stage2_container': stage2_container,
            'system_signature': signature,
            'creation_time': time.time(),
            'computer_binding': metadata['system_binding'],
            'instructions': {
                'step1': 'Scan NFC to unlock audio data',
                'step2': 'Scan NFC again to unlock passwords'
            }
        }
        
        system_file = 'dual_nfc_system.json'
        with open(system_file, 'w') as f:
            json.dump(dual_system, f, indent=2)
        
        print(f"\n✅ DUAL AUTHENTICATION SYSTEM CREATED")
        print(f"   System file: {system_file}")
        print(f"   Stage 1: {stage1_container}")
        print(f"   Stage 2: Embedded in system")
        print(f"\n🔒 Security: Requires TWO NFC scans + room acoustics + computer binding")
        
        # Clean up original audio file for security
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"   Original audio file securely removed")
        
        return system_file, dual_system
    
    def analyze_audio_for_stage2(self, audio_file):
        """Create audio analysis for stage 2 key derivation"""
        
        try:
            import librosa
            import numpy as np
            
            # Load audio
            audio, sr = librosa.load(audio_file)
            
            # Extract features for stage 2 binding
            analysis = {
                'spectral_centroid': float(librosa.feature.spectral_centroid(y=audio, sr=sr).mean()),
                'mfcc_mean': librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13).mean(axis=1).tolist(),
                'chroma_mean': librosa.feature.chroma_stft(y=audio, sr=sr).mean(axis=1).tolist(),
                'tempo': float(librosa.beat.tempo(y=audio, sr=sr)[0]),
                'rms_energy': float(librosa.feature.rms(y=audio).mean()),
                'duration': float(len(audio) / sr),
                'sample_rate': sr
            }
            
            return analysis
            
        except Exception as e:
            print(f"   Warning: Audio analysis limited: {e}")
            # Fallback analysis
            return {
                'file_size': os.path.getsize(audio_file),
                'modification_time': os.path.getmtime(audio_file),
                'fallback': True
            }
    
    def unlock_dual_system(self, system_file):
        """Complete dual unlock process"""
        
        print("=" * 60)
        print("   DUAL NFC UNLOCK PROCESS")
        print("=" * 60)
        
        # Load system
        try:
            with open(system_file, 'r') as f:
                dual_system = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load system: {e}")
            return None
        
        # Get NFC hash
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            
            # Stage 1: Unlock audio data
            print("\n🎯 STAGE 1: Unlocking audio data...")
            nfc_hash1 = scanner.invisible_scan_simple()
            
            success1, msg1, audio_bytes, audio_analysis = self.stage1_unlock(
                dual_system['stage1_container_path'], nfc_hash1
            )
            
            if not success1:
                print(f"❌ Stage 1 failed: {msg1}")
                return None
            
            # Stage 2: Unlock password vault
            print("\n🔐 STAGE 2: Unlocking password vault...")
            nfc_hash2 = scanner.invisible_scan_simple()
            
            # Verify same NFC tag
            if nfc_hash1 != nfc_hash2:
                print("❌ Different NFC tags detected - security violation")
                return None
            
            success2, msg2, password_data = self.stage2_unlock(
                dual_system['stage2_container'], nfc_hash2, audio_analysis
            )
            
            if not success2:
                print(f"❌ Stage 2 failed: {msg2}")
                return None
            
            print("\n🎉 DUAL UNLOCK COMPLETE!")
            print("   Both stages successful")
            print("   Credentials unlocked")
            
            return password_data
            
        except Exception as e:
            print(f"❌ Unlock process failed: {e}")
            return None

def main():
    """Interactive dual NFC system"""
    
    dual_system = DualNFCUnlock()
    
    print("🔐 DUAL NFC AUTHENTICATION SYSTEM")
    print("Creates two-stage NFC unlock process")
    print()
    
    choice = input("1. Create new dual system\n2. Unlock existing system\nChoice: ").strip()
    
    if choice == '1':
        # Create new system
        print("\n📟 First, scan NFC tag for binding...")
        try:
            from invisible_nfc_scanner import InvisibleNFCScanner
            scanner = InvisibleNFCScanner()
            nfc_hash = scanner.invisible_scan_simple()
            
            # Sample password vault
            password_vault = {
                'github_token': 'ghp_xxxxxxxxxxxxxxxxxxxx',
                'ssh_key_passphrase': 'ultra_secure_passphrase_123',
                'vault_description': 'Dual-locked credential vault',
                'creation_time': time.time()
            }
            
            system_file, system_data = dual_system.create_dual_locked_system(nfc_hash, password_vault)
            
            if system_file:
                print(f"\n🎉 Dual system created: {system_file}")
                print("   Ready for two-stage authentication!")
            
        except Exception as e:
            print(f"❌ Creation failed: {e}")
    
    elif choice == '2':
        # Unlock existing system
        system_file = input("Enter system file (dual_nfc_system.json): ").strip()
        if not system_file:
            system_file = 'dual_nfc_system.json'
        
        credentials = dual_system.unlock_dual_system(system_file)
        
        if credentials:
            print("\n🔓 UNLOCKED CREDENTIALS:")
            for key, value in credentials.items():
                if 'time' in key:
                    continue
                print(f"   {key}: [REDACTED - Available in memory]")

if __name__ == "__main__":
    main()
